import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils import get_pending_step_for_user


class FakeStep:
    def __init__(self, step_id, approver_id, decision=None):
        self.step_id = step_id
        self.approver_id = approver_id
        self.decision = decision


def test_get_pending_step_for_user_returns_matching_pending_step():
    steps = [
        FakeStep(1, 2, "Approved"),
        FakeStep(2, 3, None),
    ]

    pending = get_pending_step_for_user(steps, 3)
    assert pending is not None
    assert pending.step_id == 2


def test_get_pending_step_for_user_returns_none_when_no_pending_step_exists():
    steps = [FakeStep(1, 2, "Approved")]

    pending = get_pending_step_for_user(steps, 3)
    assert pending is None
