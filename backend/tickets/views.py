import json
import os

import requests
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ticket
from .serializers import TicketSerializer

LLM_PROMPT = (
    'Return ONLY a JSON object with the keys "suggested_category" and "suggested_priority"
'
    'based on these specific options:
'
    'categories: billing, technical, account, general
'
    'priorities: low, medium, high, critical'
)

ALLOWED_CATEGORIES = {"billing", "technical", "account", "general"}
ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}


def _extract_output_text(payload):
    output = payload.get("output", [])
    texts = []
    for item in output:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                texts.append(content.get("text", ""))
    return "".join(texts).strip()


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    filterset_fields = ["category", "priority", "status"]
    search_fields = ["title", "description"]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        total_tickets = Ticket.objects.count()
        open_tickets = Ticket.objects.filter(status=Ticket.Status.OPEN).count()

        avg_per_day = (
            Ticket.objects.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .aggregate(avg=Avg("count"))
            .get("avg")
            or 0
        )

        priority_counts = Ticket.objects.aggregate(
            low=Count("id", filter=Q(priority=Ticket.Priority.LOW)),
            medium=Count("id", filter=Q(priority=Ticket.Priority.MEDIUM)),
            high=Count("id", filter=Q(priority=Ticket.Priority.HIGH)),
            critical=Count("id", filter=Q(priority=Ticket.Priority.CRITICAL)),
        )

        category_counts = Ticket.objects.aggregate(
            billing=Count("id", filter=Q(category=Ticket.Category.BILLING)),
            technical=Count("id", filter=Q(category=Ticket.Category.TECHNICAL)),
            account=Count("id", filter=Q(category=Ticket.Category.ACCOUNT)),
            general=Count("id", filter=Q(category=Ticket.Category.GENERAL)),
        )

        data = {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "avg_tickets_per_day": float(avg_per_day) if avg_per_day else 0,
            "priority_breakdown": {
                "low": priority_counts.get("low", 0),
                "medium": priority_counts.get("medium", 0),
                "high": priority_counts.get("high", 0),
                "critical": priority_counts.get("critical", 0),
            },
            "category_breakdown": {
                "billing": category_counts.get("billing", 0),
                "technical": category_counts.get("technical", 0),
                "account": category_counts.get("account", 0),
                "general": category_counts.get("general", 0),
            },
        }

        return Response(data)

    @action(detail=False, methods=["post"])
    def classify(self, request):
        description = (request.data.get("description") or "").strip()
        empty = {"suggested_category": "", "suggested_priority": ""}

        if not description:
            return Response(empty)

        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            return Response(empty)

        payload = {
            "model": "gpt-4o-mini",
            "input": f"{LLM_PROMPT}

Description:
{description}",
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "ticket_classification",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "suggested_category": {
                                "type": "string",
                                "enum": [
                                    "billing",
                                    "technical",
                                    "account",
                                    "general",
                                ],
                            },
                            "suggested_priority": {
                                "type": "string",
                                "enum": [
                                    "low",
                                    "medium",
                                    "high",
                                    "critical",
                                ],
                            },
                        },
                        "required": ["suggested_category", "suggested_priority"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
            "temperature": 0,
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            output_text = _extract_output_text(data)
            parsed = json.loads(output_text) if output_text else {}
        except Exception:
            return Response(empty)

        category = parsed.get("suggested_category", "")
        priority = parsed.get("suggested_priority", "")

        if category not in ALLOWED_CATEGORIES:
            category = ""
        if priority not in ALLOWED_PRIORITIES:
            priority = ""

        return Response({
            "suggested_category": category,
            "suggested_priority": priority,
        })
