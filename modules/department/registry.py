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
]

SYSTEM_PERMISSIONS = []

ROLE_GRANTS = {
    "student": ["department.department.view"],
    "faculty": ["department.department.view"],
    "acadadmin": ["department.department.view", "department.role_assignment.view", "department.role_assignment.assign"],
    "HOD (CSE)": ["department.department.view"],
    "HOD (Design)": ["department.department.view"],
    "HOD (ECE)": ["department.department.view"],
    "HOD (Liberal Arts)": ["department.department.view"],
    "HOD (ME)": ["department.department.view"],
    "HOD (NS)": ["department.department.view"],
    "dept_admin": ["department.department.view"],
    "deptadmin_cse": ["department.department.view"],
    "deptadmin_design": ["department.department.view"],
    "deptadmin_ece": ["department.department.view"],
    "deptadmin_liberalarts": ["department.department.view"],
    "deptadmin_me": ["department.department.view"],
    "deptadmin_ns": ["department.department.view"],
    "deptadmin_sm": ["department.department.view"],
}
