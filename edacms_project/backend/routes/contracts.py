from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Contract, Workflow, ApprovalStep, User, Role
from utils import log_action

contracts_bp = Blueprint("contracts", __name__, url_prefix="/api/contracts")


@contracts_bp.route("", methods=["GET"])
@jwt_required()
def list_contracts():
    status = request.args.get("status", "").strip()
    query = Contract.query
    if status:
        query = query.filter(Contract.status == status)
    contracts = query.order_by(Contract.contract_id.desc()).all()

    today = date.today()
    result = []
    for c in contracts:
        d = c.to_dict()
        days_left = (c.end_date - today).days
        d["days_to_expiry"] = days_left
        if c.status == "Active" and 0 <= days_left <= 30:
            d["status"] = "Renewal Due"
        result.append(d)
    return jsonify(result)


@contracts_bp.route("", methods=["POST"])
@jwt_required()
def create_contract():
    user_id = int(get_jwt_identity())
    data = request.get_json(force=True) or {}
    required = ["title", "party_name", "start_date", "end_date"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": f"Missing required fields: {required}"}), 400

    contract = Contract(
        title=data["title"],
        party_name=data["party_name"],
        start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date(),
        end_date=datetime.strptime(data["end_date"], "%Y-%m-%d").date(),
        status="Draft",
        owner_id=user_id,
    )
    db.session.add(contract)
    db.session.commit()
    log_action(user_id, "DRAFT_CONTRACT", details=contract.title)
    return jsonify(contract.to_dict()), 201


@contracts_bp.route("/<int:contract_id>", methods=["GET"])
@jwt_required()
def get_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    d = contract.to_dict()
    d["workflows"] = [w.to_dict() for w in contract.workflows]
    steps = []
    for w in contract.workflows:
        steps.extend([s.to_dict() for s in w.steps])
    d["approval_steps"] = steps
    return jsonify(d)


@contracts_bp.route("/<int:contract_id>/submit", methods=["POST"])
@jwt_required()
def submit_for_approval(contract_id):
    user_id = int(get_jwt_identity())
    contract = Contract.query.get_or_404(contract_id)
    data = request.get_json(silent=True) or {}
    approver_id = data.get("approver_id")

    approver = None
    if approver_id:
        approver = User.query.get(approver_id)
    else:
        # Prefer a Manager as approver; fall back to Admin. Never assign the submitter as their own approver.
        for preferred_role in ("manager", "admin"):
            role = Role.query.filter_by(role_name=preferred_role).first()
            if role:
                candidate = User.query.filter(
                    User.role_id == role.role_id, User.user_id != user_id
                ).first()
                if candidate:
                    approver = candidate
                    break

    if not approver:
        return jsonify({"error": "No suitable approver could be found"}), 400

    workflow = Workflow(contract_id=contract.contract_id, current_step="Manager Review", status="Pending")
    db.session.add(workflow)
    db.session.flush()

    step = ApprovalStep(workflow_id=workflow.workflow_id, approver_id=approver.user_id)
    db.session.add(step)

    contract.status = "Under Review"
    db.session.commit()

    log_action(user_id, "SUBMIT_CONTRACT", details=f"{contract.title} -> {approver.full_name}")
    return jsonify(contract.to_dict()), 200


@contracts_bp.route("/<int:contract_id>/renew", methods=["POST"])
@jwt_required()
def renew_contract(contract_id):
    user_id = int(get_jwt_identity())
    contract = Contract.query.get_or_404(contract_id)
    data = request.get_json(force=True) or {}
    new_end_date = data.get("new_end_date")
    if not new_end_date:
        return jsonify({"error": "new_end_date is required"}), 400

    contract.end_date = datetime.strptime(new_end_date, "%Y-%m-%d").date()
    contract.status = "Active"
    db.session.commit()
    log_action(user_id, "RENEW_CONTRACT", details=f"{contract.title} -> {new_end_date}")
    return jsonify(contract.to_dict())


@contracts_bp.route("/<int:contract_id>/archive", methods=["POST"])
@jwt_required()
def archive_contract(contract_id):
    user_id = int(get_jwt_identity())
    contract = Contract.query.get_or_404(contract_id)
    contract.status = "Archived"
    db.session.commit()
    log_action(user_id, "ARCHIVE_CONTRACT", details=contract.title)
    return jsonify(contract.to_dict())
