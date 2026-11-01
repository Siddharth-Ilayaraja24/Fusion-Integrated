"""Scheduled work.

Ids only in arguments, never ORM objects. Everything is idempotent, because
`acks_late` means a task can run twice if a worker dies mid-flight.
"""
from __future__ import annotations

import logging

from celery import shared_task

log = logging.getLogger("fusion.department.tasks")


@shared_task(
    name="department.deliver_notifications",
    acks_late=True, reject_on_worker_lost=True,
    soft_time_limit=270, time_limit=300,
)
def deliver_notifications(limit: int | None = None) -> str:
    """Drain the notification outbox.

    No autoretry — the rows carry their own attempts and backoff, so a failed
    pass is picked up by the next beat rather than re-sending the batch.
    """
    from modules.department.services import notifications

    report = notifications.deliver_pending(limit=limit)
    log.info("department.notify.run %s", report)
    return str(report)
