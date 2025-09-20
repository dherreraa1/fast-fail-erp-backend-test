import uuid
from django.db import models
from django.conf import settings

class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name

class Document(models.Model):
    STATUS_CHOICES = [
        ("P", "Pending"),
        ("A", "Approved"),
        ("R", "Rejected"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="documents")
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()
    bucket_key = models.CharField(max_length=500)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    validation_status = models.CharField(max_length=1, choices=STATUS_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

class ValidationStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, related_name="validation_steps", on_delete=models.CASCADE)
    order = models.PositiveIntegerField(help_text="Order/priority: higher = higher hierarchy")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    acted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    acted_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("document", "order")
        ordering = ["order"]

    def is_pending(self) -> bool:
        return (not self.approved) and (not self.rejected)

class ValidationAction(models.Model):
    ACTION_CHOICES = [("A", "Approve"), ("R", "Reject")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step = models.ForeignKey(ValidationStep, related_name="actions", on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
