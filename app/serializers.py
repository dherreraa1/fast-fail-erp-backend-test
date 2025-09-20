from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Company, Document, ValidationStep, ValidationAction

User = get_user_model()

class ValidationActionSerializer(serializers.ModelSerializer):
    actor = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = ValidationAction
        fields = ["id", "actor", "action", "reason", "created_at"]

class ValidationStepSerializer(serializers.ModelSerializer):
    approver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    actions = ValidationActionSerializer(many=True, read_only=True)
    class Meta:
        model = ValidationStep
        fields = ["id", "order", "approver", "approved", "rejected", "acted_by", "acted_at", "reason", "actions"]
        read_only_fields = ["approved", "rejected", "acted_by", "acted_at", "actions"]

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name"]

class DocumentSerializer(serializers.ModelSerializer):
    validation_steps = ValidationStepSerializer(many=True, read_only=True)
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    class Meta:
        model = Document
        fields = ["id", "company", "entity_type", "entity_id", "name", "mime_type", "size_bytes", "bucket_key", "created_by", "validation_status", "created_at", "validation_steps"]
        read_only_fields = ["id", "created_by", "validation_status", "created_at", "validation_steps"]
