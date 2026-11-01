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
    ("department.inventory.view", "View department inventory"),
    ("department.inventory.create", "Create department inventory"),
    ("department.stock_request.view", "View stock requests"),
    ("department.stock_request.create", "Create stock requests"),
    ("department.stock_request.approve", "Approve stock requests"),
    ("department.stock_request.update", "Update stock requests"),
    ("department.stock_movement.view", "View stock movements"),
    ("department.feedback.view", "View department feedback"),
    ("department.feedback.create", "Create department feedback"),
    ("department.feedback.review", "Review department feedback"),
    ("department.feedback.update", "Update department feedback"),
]

SYSTEM_PERMISSIONS = []

ROLE_GRANTS = {
    "student": ["department.department.view", "department.announcement.view", "department.feedback.view", "department.feedback.create"],
    "faculty": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.stock_request.create", "department.feedback.view", "department.feedback.create"],
    "acadadmin": ["department.department.view", "department.role_assignment.view", "department.role_assignment.assign"],
    "HOD (CSE)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete", "department.inventory.view", "department.stock_request.view", "department.stock_request.approve", "department.stock_movement.view", "department.feedback.view", "department.feedback.update"],
    "HOD (Design)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete", "department.inventory.view", "department.stock_request.view", "department.stock_request.approve", "department.stock_movement.view", "department.feedback.view", "department.feedback.update"],
    "HOD (ECE)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete", "department.inventory.view", "department.stock_request.view", "department.stock_request.approve", "department.stock_movement.view", "department.feedback.view", "department.feedback.update"],
    "HOD (Liberal Arts)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete", "department.inventory.view", "department.stock_request.view", "department.stock_request.approve", "department.stock_movement.view", "department.feedback.view", "department.feedback.update"],
    "HOD (ME)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete", "department.inventory.view", "department.stock_request.view", "department.stock_request.approve", "department.stock_movement.view", "department.feedback.view", "department.feedback.update"],
    "HOD (NS)": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.announcement.update", "department.announcement.delete", "department.inventory.view", "department.stock_request.view", "department.stock_request.approve", "department.stock_movement.view", "department.feedback.view", "department.feedback.update"],
    "dept_admin": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.inventory.view", "department.inventory.create", "department.stock_request.view", "department.stock_request.update", "department.stock_movement.view", "department.feedback.view", "department.feedback.review"],
    "deptadmin_cse": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.inventory.view", "department.inventory.create", "department.stock_request.view", "department.stock_request.update", "department.stock_movement.view", "department.feedback.view", "department.feedback.review"],
    "deptadmin_design": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.inventory.view", "department.inventory.create", "department.stock_request.view", "department.stock_request.update", "department.stock_movement.view", "department.feedback.view", "department.feedback.review"],
    "deptadmin_ece": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.inventory.view", "department.inventory.create", "department.stock_request.view", "department.stock_request.update", "department.stock_movement.view", "department.feedback.view", "department.feedback.review"],
    "deptadmin_liberalarts": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.inventory.view", "department.inventory.create", "department.stock_request.view", "department.stock_request.update", "department.stock_movement.view", "department.feedback.view", "department.feedback.review"],
    "deptadmin_me": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.inventory.view", "department.inventory.create", "department.stock_request.view", "department.stock_request.update", "department.stock_movement.view", "department.feedback.view", "department.feedback.review"],
    "deptadmin_ns": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.inventory.view", "department.inventory.create", "department.stock_request.view", "department.stock_request.update", "department.stock_movement.view", "department.feedback.view", "department.feedback.review"],
    "deptadmin_sm": ["department.department.view", "department.announcement.view", "department.announcement.create", "department.inventory.view", "department.inventory.create", "department.stock_request.view", "department.stock_request.update", "department.stock_movement.view", "department.feedback.view", "department.feedback.review"],
}
