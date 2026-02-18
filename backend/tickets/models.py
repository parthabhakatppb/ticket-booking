from django.db import models


class Ticket(models.Model):
    class Category(models.TextChoices):
        BILLING = "billing", "Billing"
        TECHNICAL = "technical", "Technical"
        ACCOUNT = "account", "Account"
        GENERAL = "general", "General"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    priority = models.CharField(max_length=20, choices=Priority.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(category__in=[c.value for c in Category]),
                name="ticket_category_valid",
            ),
            models.CheckConstraint(
                check=models.Q(priority__in=[p.value for p in Priority]),
                name="ticket_priority_valid",
            ),
            models.CheckConstraint(
                check=models.Q(status__in=[s.value for s in Status]),
                name="ticket_status_valid",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"
