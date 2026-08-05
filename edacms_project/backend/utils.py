from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from extensions import db
from models import AccessLog, ApprovalStep, Workflow, Contract, Role


def select_approver(submitter_id, candidates):
    preferred_roles = ("manager", "legal_manager", "admin")

    for role_name in preferred_roles:
        for candidate in candidates:
            if candidate.get("role_name") == role_name and candidate.get("user_id") != submitter_id:
                return candidate

    for role_name in preferred_roles:
        for candidate in candidates:
            if candidate.get("role_name") == role_name:
                return candidate

    return None


def get_pending_step_for_user(steps, user_id):
    for step in steps:
        if getattr(step, "approver_id", None) == user_id and getattr(step, "decision", None) is None:
            return step
    return None


def assign_pending_approvals(user):
    if not user or not getattr(user, "user_id", None):
        return []

    role_name = None
    role = None
    if getattr(user, "role", None):
        role = user.role
    elif getattr(user, "role_id", None):
        role = Role.query.get(user.role_id)

    if role:
        role_name = role.role_name

    if role_name not in {"manager", "legal_manager", "admin"}:
        return []

    workflows = Workflow.query.join(Contract).filter(
        Workflow.status == "Pending",
        Contract.status == "Under Review"
    ).all()

    assigned_steps = []
    for workflow in workflows:
        existing_step = ApprovalStep.query.filter_by(
            workflow_id=workflow.workflow_id,
            approver_id=user.user_id
        ).first()
        if existing_step:
            continue

        step = ApprovalStep(workflow_id=workflow.workflow_id, approver_id=user.user_id)
        db.session.add(step)
        assigned_steps.append(step)

    return assigned_steps


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def log_action(user_id, action, document_id=None, details=None):
    entry = AccessLog(user_id=user_id, action=action, document_id=document_id, details=details)
    db.session.add(entry)
    db.session.commit()
