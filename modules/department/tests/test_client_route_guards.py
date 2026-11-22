import re
from pathlib import Path

from django.conf import settings

from modules.department import registry


def test_every_department_route_is_guarded_with_its_nav_permission():
    routes_file = (
        Path(settings.BASE_DIR) / "client" / "src" / "modules" / "department" / "routes.tsx"
    )
    src = routes_file.read_text()
    guards = dict(
        re.findall(r'path:\s*"([^"]+)",\s*element:\s*guarded\("([^"]+)"', src)
    )
    base = registry.MODULE["base_path"].rstrip("/")
    expected = {
        item["to"][len(base) :].lstrip("/"): item["required_permission"]
        for item in registry.NAV_ITEMS
    }
    assert guards == expected
