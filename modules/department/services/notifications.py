from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.department.models import Department, DepartmentNotification
from modules.directory import contracts as directory

log = logging.getLogger("fusion.department")


def enqueue(
    *,
    department: Department,
    topic: str,
    dedupe_key: str,
    recipient_user_id: int | None,
    subject: str,
    body: str,
    payload: dict | None = None,
) -> DepartmentNotification | None:
    if recipient_user_id is None:
        return None
    try:
        with transaction.atomic():
            obj, _ = DepartmentNotification.objects.get_or_create(
                dedupe_key=dedupe_key,
                defaults={
                    "department": department,
                    "topic": topic,
                    "recipient_user_id": recipient_user_id,
                    "subject": subject[:200],
                    "body": body,
                    "payload": payload or {},
                },
            )
            return obj
    except IntegrityError:
        return DepartmentNotification.objects.filter(dedupe_key=dedupe_key).first()


def deliver_pending(*, limit: int | None = None) -> int:
    # AFR-DEPT-041..046: idempotent drain safe under concurrent workers and redelivery.
    batch_limit = limit or getattr(settings, "NOTIFY_MAX_PER_RUN", 500)
    max_attempts = getattr(settings, "NOTIFY_MAX_ATTEMPTS", 5)
    delivered = 0

    with transaction.atomic():
        pending = list(
            DepartmentNotification.objects.select_for_update(skip_locked=True)
            .filter(status="pending")
            .order_by("id")[:batch_limit]
        )
        if not pending:
            return 0
        user_map = directory.get_users([n.recipient_user_id for n in pending])
        for note in pending:
            user = user_map.get(note.recipient_user_id)
            email = getattr(user, "email", "") if user else ""
            note.attempts += 1
            try:
                if email:
                    send_mail(
                        note.subject,
                        note.body,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                note.status = "sent"
                note.sent_at = timezone.now()
                note.last_error = ""
                note.save(update_fields=["status", "attempts", "sent_at", "last_error",
                                         "updated_at"])
                delivered += 1
            except OSError as exc:
                note.last_error = str(exc)[:300]
                if note.attempts >= max_attempts:
                    note.status = "failed"
                note.save(update_fields=["status", "attempts", "last_error", "updated_at"])
                log.warning("department.notify.failed id=%s err=%s", note.pk, exc)
    return delivered
