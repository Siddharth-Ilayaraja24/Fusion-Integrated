"""What the server tells the shell about this module (ADR-0010)."""
MODULE = {
    "code": "department", "label": "Department", "icon": "Buildings",
    "base_path": "/department", "nav_section": "Department", "sort_order": 40,
    "status": "active",
}

NAV_ITEMS = []

PERMISSIONS = [
    ("department.department.view", "View department listings"),
    ("department.role_assignment.view", "View department role assignments"),
    ("department.role_assignment.assign", "Assign department roles"),
    ("department.announcement.view", "View department announcements"),
    ("department.announcement.create", "Create department announcements"),
    ("department.announcement.update", "Update department announcements"),
    ("department.announcement.delete", "Delete department announcements"),
]

SYSTEM_PERMISSIONS = []

ROLE_GRANTS = {
    "student": ["department.department.view", "department.announcement.view"],
    "faculty": ["department.department.view", "department.announcement.view", "department.announcement.create"],
    "acadadmin": ["department.department.view", "department.role_assignment.view", "department.role_assignment.assign"],
    "HOD (CSE)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete"],
    "HOD (Design)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete"],
    "HOD (ECE)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete"],
    "HOD (Liberal Arts)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete"],
    "HOD (ME)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete"],
    "HOD (NS)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete"],
    "dept_admin": ["department.department.view", "department.announcement.view", "department.announcement.create"],
    "deptadmin_cse": ["department.department.view", "department.announcement.view", "department.announcement.create"],
    "deptadmin_design": ["department.department.view", "department.announcement.view", "department.announcement.create"],
    "deptadmin_ece": ["department.department.view", "department.announcement.view", "department.announcement.create"],
    "deptadmin_liberalarts": ["department.department.view", "department.announcement.view", "department.announcement.create"],
    "deptadmin_me": ["department.department.view", "department.announcement.view", "department.announcement.create"],
    "deptadmin_ns": ["department.department.view", "department.announcement.view", "department.announcement.create"],
    "deptadmin_sm": ["department.department.view", "department.announcement.view", "department.announcement.create"],
}
