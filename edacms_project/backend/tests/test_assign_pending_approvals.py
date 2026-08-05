import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils import assign_pending_approvals


class FakeRole:
    def __init__(self, role_name):
        self.role_name = role_name


class FakeUser:
    def __init__(self, user_id, role_name):
        self.user_id = user_id
        self.role = FakeRole(role_name)


def test_assign_pending_approvals_returns_empty_for_non_approver_role():
    user = FakeUser(1, "staff")
    assert assign_pending_approvals(user) == []
