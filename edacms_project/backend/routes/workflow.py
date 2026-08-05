from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import ApprovalStep, Workflow, Contract, User, Role
from utils import log_action, get_pending_step_for_user

workflow_bp = Blueprint("workflow", __name__, url_prefix="/api/workflow")


@workflow_bp.route("/pending", methods=["GET"])
@jwt_required()
def pending_for_me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.role or user.role.role_name != "manager":
        return jsonify([])

    steps = ApprovalStep.query.filter_by(approver_id=user_id).order_by(
        ApprovalStep.created_date.asc()
    ).all()
    pending_steps = [s for s in steps if s.decision is None]
    return jsonify([s.to_dict() for s in pending_steps])


@workflow_bp.route("/steps/<int:step_id>/decide", methods=["POST"])
@jwt_required()
def decide(step_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.role or user.role.role_name != "manager":
        return jsonify({"error": "Only managers can approve or reject contracts"}), 403

    step = ApprovalStep.query.get_or_404(step_id)
    if step.approver_id != user_id:
        return jsonify({"error": "You are not the assigned approver for this item"}), 403

    data = request.get_json(force=True) or {}
    decision = data.get("decision")  # "Approved" or "Rejected"
    comment = data.get("comment", "")

    if decision not in ("Approved", "Rejected"):
        return jsonify({"error": "decision must be 'Approved' or 'Rejected'"}), 400

    step.decision = decision
    step.comment = comment
    step.decision_date = datetime.utcnow()

    workflow = step.workflow
    contract = workflow.contract
    if decision == "Approved":
        workflow.status = "Approved"
        contract.status = "Active"
    else:
        workflow.status = "Rejected"
        contract.status = "Draft"

    db.session.commit()
    log_action(user_id, "WORKFLOW_DECISION", details=f"{contract.title}: {decision}")
    return jsonify(step.to_dict())
