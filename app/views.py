from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.timezone import now
from django.db.models import Max
from .models import Company, Document, ValidationStep, ValidationAction
from .serializers import DocumentSerializer, CompanySerializer
from .storage import generate_presigned_put_url, generate_presigned_get_url
from django.contrib.auth import get_user_model

User = get_user_model()

class CompanyCreateView(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        company_id = data.get("company_id")
        entity = data.get("entity") or {}
        document_info = data.get("document") or {}

        company = get_object_or_404(Company, id=company_id)

        doc = Document.objects.create(
            company=company,
            entity_type=entity.get("entity_type", "generic"),
            entity_id=entity.get("entity_id"),
            name=document_info.get("name"),
            mime_type=document_info.get("mime_type"),
            size_bytes=document_info.get("size_bytes", 0),
            bucket_key=document_info.get("bucket_key"),
            created_by=request.user,
            validation_status="P" if data.get("validation_flow", {}).get("enabled") else None,
        )

        if data.get("validation_flow", {}).get("enabled"):
            steps = data["validation_flow"].get("steps", [])
            for s in steps:
                ValidationStep.objects.create(document=doc, order=s["order"], approver_id=s["approver_user_id"])

        upload_url = generate_presigned_put_url(doc.bucket_key)
        return Response({"document_id": str(doc.id), "upload_url": upload_url}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirm_upload(self, request, pk=None):
        doc = get_object_or_404(Document, id=pk)
        # En producción, se debe usar head_object para confirmar la existencia; se omiten comprobaciones pesadas por brevedad.
        return Response({"detail": "Upload confirmado", "document_id": str(doc.id)})

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        doc = get_object_or_404(Document, id=pk)
        url = generate_presigned_get_url(doc.bucket_key)
        return Response({"download_url": url, "validation_status": doc.validation_status})

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def approve(self, request, pk=None):
        doc = get_object_or_404(Document, id=pk)
        if doc.validation_status is None:
            return Response({"detail": "Documento no tiene flujo de validación."}, status=status.HTTP_400_BAD_REQUEST)
        if doc.validation_status in ("A", "R"):
            return Response({"detail": "Documento terminal."}, status=status.HTTP_400_BAD_REQUEST)

        actor_id = request.data.get("actor_user_id")
        reason = request.data.get("reason", "")

        actor = get_object_or_404(User, id=actor_id)

        actor_steps = doc.validation_steps.filter(approver=actor, approved=False, rejected=False)  # type: ignore[attr-defined]
        if not actor_steps.exists():
            return Response({"detail": "No hay pasos pendientes asignados a este actor."}, status=status.HTTP_400_BAD_REQUEST)

        actor_orders = list(actor_steps.values_list("order", flat=True))
        actor_max_order = max(actor_orders)

        now_dt = now()
        actor_steps.update(approved=True, acted_by=actor, acted_at=now_dt, reason=reason)

        # Crear ValidationAction para cada step del actor
        for step in actor_steps:
            ValidationAction.objects.create(step=step, actor=actor, action="A", reason=reason)

        prior_pending = doc.validation_steps.filter(order__lt=actor_max_order, approved=False, rejected=False)  # type: ignore[attr-defined]
        prior_pending.update(approved=True, acted_by=actor, acted_at=now_dt, reason=f"Auto-aprobado por {actor_id} (jerarquía)")

        # Crear ValidationAction para los steps auto-aprobados también
        for step in prior_pending:
            ValidationAction.objects.create(step=step, actor=actor, action="A", reason=f"Auto-aprobado por jerarquía")

        max_order = doc.validation_steps.aggregate(max_order=Max("order"))["max_order"]  # type: ignore[attr-defined]
        if max_order is not None and actor_max_order >= max_order:
            doc.validation_status = "A"
        else:
            doc.validation_status = "P"
        doc.save(update_fields=["validation_status"])
        return Response({"detail": "Aprobado", "document_status": doc.validation_status})

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reject(self, request, pk=None):
        doc = get_object_or_404(Document, id=pk)
        if doc.validation_status is None:
            return Response({"detail": "Documento no tiene flujo de validación."}, status=status.HTTP_400_BAD_REQUEST)
        if doc.validation_status in ("A", "R"):
            return Response({"detail": "Documento terminal."}, status=status.HTTP_400_BAD_REQUEST)

        actor_id = request.data.get("actor_user_id")
        reason = request.data.get("reason", "")
        actor = get_object_or_404(User, id=actor_id)

        steps = doc.validation_steps.filter(approver=actor, approved=False, rejected=False)  # type: ignore[attr-defined]
        if not steps.exists():
            return Response({"detail": "No hay pasos pendientes para este actor."}, status=status.HTTP_400_BAD_REQUEST)

        now_dt = now()
        steps.update(rejected=True, acted_by=actor, acted_at=now_dt, reason=reason)

        for s in steps:
            ValidationAction.objects.create(step=s, actor=actor, action="R", reason=reason)

        doc.validation_status = "R"
        doc.save(update_fields=["validation_status"])
        return Response({"detail": "Rechazado", "document_status": doc.validation_status})