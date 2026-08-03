from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Document, Contract, AccessLog, ApprovalStep, ComplianceReport, User
from utils import log_action

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    total_documents = Document.query.count()
    active_contracts = Contract.query.filter(Contract.status.in_(["Active", "Approved"])).count()
    pending_approvals = ApprovalStep.query.filter_by(decision=None).count()

    status_counts = {}
    for status in ["Draft", "Under Review", "Approved", "Active", "Archived"]:
        status_counts[status] = Contract.query.filter_by(status=status).count()

    recent_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(8).all()

    return jsonify({
        "total_documents": total_documents,
        "active_contracts": active_contracts,
        "pending_approvals": pending_approvals,
        "contract_status_counts": status_counts,
        "recent_activity": [
            f"{log.user.full_name if log.user else 'Someone'} — {log.action.replace('_', ' ').title()}"
            + (f" ({log.details})" if log.details else "")
            for log in recent_logs
        ],
    })


@reports_bp.route("/compliance", methods=["GET"])
@jwt_required()
def compliance_report():
    user_id = int(get_jwt_identity())
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    report_type = request.args.get("report_type", "Activity Summary")

    query = AccessLog.query
    if date_from:
        query = query.filter(AccessLog.timestamp >= date_from)
    if date_to:
        query = query.filter(AccessLog.timestamp <= date_to + " 23:59:59")
    logs = query.order_by(AccessLog.timestamp.desc()).all()

    action_counts = {}
    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1

    report = ComplianceReport(
        generated_by=user_id,
        date_range=f"{date_from or 'all'} to {date_to or 'now'}",
        report_type=report_type,
    )
    db.session.add(report)
    db.session.commit()
    log_action(user_id, "GENERATE_REPORT", details=report_type)

    return jsonify({
        "report_id": report.report_id,
        "report_type": report_type,
        "date_range": report.date_range,
        "total_events": len(logs),
        "action_breakdown": action_counts,
        "events": [log.to_dict() for log in logs[:100]],
    })


@reports_bp.route("/access-logs", methods=["GET"])
@jwt_required()
def access_logs():
    logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(200).all()
    return jsonify([log.to_dict() for log in logs])
