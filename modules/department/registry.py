MODULE = {
    "code": "department",
    "label": "Department",
    "icon": "Buildings",
    "base_path": "/department",
    "nav_section": "Department",
    "sort_order": 40,
    "status": "active",
}

NAV_ITEMS = [
    {
        "code": "department.announcements",
        "label": "Announcements",
        "icon": "Megaphone",
        "to": "/department/announcements",
        "required_permission": "department.announcement.view",
        "sort_order": 10,
    },
    {
        "code": "department.inventory",
        "label": "Inventory & Stock",
        "icon": "Package",
        "to": "/department/inventory",
        "required_permission": "department.stock_request.view",
        "sort_order": 20,
    },
    {
        "code": "department.feedback",
        "label": "Feedback",
        "icon": "ChatText",
        "to": "/department/feedback",
        "required_permission": "department.feedback.view",
        "sort_order": 30,
    },
    {
        "code": "department.timetable",
        "label": "Timetable & Programs",
        "icon": "CalendarBlank",
        "to": "/department/timetable",
        "required_permission": "department.timetable.view",
        "sort_order": 40,
    },
    {
        "code": "department.resources",
        "label": "Lab Resources",
        "icon": "Desktop",
        "to": "/department/resources",
        "required_permission": "department.lab.view",
        "sort_order": 50,
    },
    {
        "code": "department.profiles",
        "label": "Profiles",
        "icon": "Users",
        "to": "/department/profiles",
        "required_permission": "department.profile.view",
        "sort_order": 60,
    },
    {
        "code": "department.details",
        "label": "Department Details",
        "icon": "Buildings",
        "to": "/department/details",
        "required_permission": "department.department.view",
        "sort_order": 70,
    },
    {
        "code": "department.roles",
        "label": "Role Assignments",
        "icon": "UserGear",
        "to": "/department/roles",
        "required_permission": "department.role_assignment.view",
        "sort_order": 80,
    },
]

PERMISSIONS = [
    ("department.department.view", "View department overview and details"),
    ("department.department.update", "Update general details and propose official changes"),
    ("department.official_change.view", "View pending and decided official department changes"),
    ("department.official_change.approve", "Approve or reject official department changes"),
    ("department.announcement.view", "View relevant department announcements"),
    ("department.announcement.create", "Create and publish department announcements"),
    ("department.announcement.update", "Edit or hide active department announcements"),
    ("department.announcement.delete", "Delete active department announcements"),
    ("department.inventory.view", "View department inventory items"),
    ("department.inventory.create", "Insert stock records into department inventory"),
    ("department.stock_request.view", "View stock requests within scope"),
    ("department.stock_request.create", "Submit Faculty stock requests"),
    ("department.stock_request.approve", "Approve or reject pending stock requests"),
    ("department.stock_request.update", "Issue HOD-approved stock requests"),
    ("department.stock_movement.view", "View immutable stock movement audit log"),
    ("department.feedback.view", "View confidential feedback within scope"),
    ("department.feedback.create", "Submit confidential department feedback"),
    ("department.feedback.review", "Perform initial review and categorization of feedback"),
    ("department.feedback.update", "Resolve or close reviewed feedback"),
    ("department.timetable.view", "View class and lab timetables"),
    ("department.timetable.create", "Upload class and lab timetables"),
    ("department.timetable.update", "Modify existing class and lab timetables"),
    ("department.lab.view", "View department lab equipment and resource profiles"),
    ("department.lab.update", "Update department lab equipment and resource profiles"),
    ("department.program.view", "View department academic program information"),
    ("department.program.update", "Manage department academic program information"),
    ("department.profile.view", "View department user profiles under visibility rules"),
    ("department.profile.update", "Manage Faculty, Student, and Alumni profiles"),
    ("department.roster.update", "Manage Faculty-Student course enrollment roster"),
    ("department.role_assignment.view", "View department HOD and Dept_Admin role assignments"),
    ("department.role_assignment.assign", "Assign time-bound HOD and Dept_Admin roles"),
    ("department.role_assignment.revoke", "System effective-date role transition"),
]

SYSTEM_PERMISSIONS = [
    "department.role_assignment.revoke",
]

SCOPE_PERMISSIONS: list[str] = []

_STUDENT = [
    "department.department.view",
    "department.announcement.view",
    "department.feedback.view",
    "department.feedback.create",
    "department.timetable.view",
    "department.program.view",
    "department.profile.view",
]

_FACULTY = [
    "department.department.view",
    "department.announcement.view",
    "department.announcement.create",
    "department.inventory.view",
    "department.stock_request.view",
    "department.stock_request.create",
    "department.stock_movement.view",
    "department.feedback.view",
    "department.feedback.create",
    "department.timetable.view",
    "department.lab.view",
    "department.program.view",
    "department.profile.view",
]

_ACADADMIN = [
    "department.department.view",
    "department.role_assignment.view",
    "department.role_assignment.assign",
]

_HOD = [
    "department.department.view",
    "department.announcement.view",
    "department.announcement.create",
    "department.announcement.update",
    "department.announcement.delete",
    "department.inventory.view",
    "department.stock_request.view",
    "department.stock_request.approve",
    "department.stock_movement.view",
    "department.feedback.view",
    "department.feedback.update",
    "department.timetable.view",
    "department.lab.view",
    "department.program.view",
    "department.profile.view",
    "department.official_change.view",
    "department.official_change.approve",
]

_DEPT_ADMIN = [
    "department.department.view",
    "department.department.update",
    "department.announcement.view",
    "department.announcement.create",
    "department.inventory.view",
    "department.inventory.create",
    "department.stock_request.view",
    "department.stock_request.update",
    "department.stock_movement.view",
    "department.feedback.view",
    "department.feedback.review",
    "department.feedback.update",
    "department.timetable.view",
    "department.timetable.create",
    "department.timetable.update",
    "department.lab.view",
    "department.lab.update",
    "department.program.view",
    "department.program.update",
    "department.profile.view",
    "department.profile.update",
    "department.roster.update",
    "department.official_change.view",
]

ROLE_GRANTS = {
    "student": _STUDENT,
    "faculty": _FACULTY,
    "acadadmin": _ACADADMIN,
    "HOD (CSE)": _HOD,
    "HOD (Design)": _HOD,
    "HOD (ECE)": _HOD,
    "HOD (Liberal Arts)": _HOD,
    "HOD (ME)": _HOD,
    "HOD (NS)": _HOD,
    "dept_admin": _DEPT_ADMIN,
    "deptadmin_cse": _DEPT_ADMIN,
    "deptadmin_design": _DEPT_ADMIN,
    "deptadmin_ece": _DEPT_ADMIN,
    "deptadmin_liberalarts": _DEPT_ADMIN,
    "deptadmin_me": _DEPT_ADMIN,
    "deptadmin_ns": _DEPT_ADMIN,
    "deptadmin_sm": _DEPT_ADMIN,
}


def readiness() -> list[str]:
    from modules.department.models import Department

    unmet: list[str] = []
    if not Department.objects.exists():
        unmet.append(
            "No departments exist yet. Run `python manage.py seed_departments` to create them."
        )
    return unmet
