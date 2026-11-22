from celery.schedules import crontab

TASK_ROUTES = {
    "department.deliver_notifications": {"queue": "notifications"},
    "department.apply_role_transitions": {"queue": "default"},
}

BEAT_SCHEDULE = {
    # UC-DEPT-022 / BR-DEPT-024: activate scheduled HOD/Dept_Admin handovers on time.
    "department.apply-role-transitions": {
        "task": "department.apply_role_transitions",
        "schedule": crontab(minute="*"),
        "options": {"expires": 55},
    },
    # AFR-DEPT-041..046: drain pending stock, feedback, and announcement notifications.
    "department.deliver-notifications": {
        "task": "department.deliver_notifications",
        "schedule": 60.0,
        "options": {"expires": 55},
    },
}
