import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils import select_approver


def test_select_approver_prefers_manager_before_admin():
    candidates = [
        {"role_name": "admin", "user_id": 2, "user": object()},
        {"role_name": "manager", "user_id": 3, "user": object()},
    ]

    selected = select_approver(1, candidates)
    assert selected is not None
    assert selected["role_name"] == "manager"
    assert selected["user_id"] == 3


def test_select_approver_prefers_manager_over_legal_manager():
    candidates = [
        {"role_name": "legal_manager", "user_id": 2, "user": object()},
        {"role_name": "manager", "user_id": 3, "user": object()},
    ]

    selected = select_approver(1, candidates)
    assert selected is not None
    assert selected["role_name"] == "manager"
    assert selected["user_id"] == 3


def test_select_approver_skips_submitter():
    candidates = [
        {"role_name": "manager", "user_id": 1, "user": object()},
        {"role_name": "manager", "user_id": 2, "user": object()},
    ]

    selected = select_approver(1, candidates)
    assert selected is not None
    assert selected["user_id"] == 2
