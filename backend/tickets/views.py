from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ticket
from .serializers import TicketSerializer


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
