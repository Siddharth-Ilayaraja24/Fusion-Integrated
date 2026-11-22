from celery import shared_task

from modules.department.services import notifications, roles


@shared_task(
    name="department.apply_role_transitions",
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=45,
    time_limit=60,
)
def apply_role_transitions() -> int:
    return roles.apply_effective_transitions()


@shared_task(
    name="department.deliver_notifications",
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=45,
    time_limit=60,
)
def deliver_notifications() -> int:
    return notifications.deliver_pending()
