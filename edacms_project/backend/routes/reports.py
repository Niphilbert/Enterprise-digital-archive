from datetime import datetime, date, timedelta
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Document, Contract, AccessLog, ApprovalStep, ComplianceReport, User
from utils import log_action

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - fallback when reportlab is unavailable
    canvas = None
    letter = None
    colors = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    inch = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _build_report_payload(user_id, date_from, date_to, report_type):
    query = AccessLog.query
    parsed_from = _parse_date(date_from)
    parsed_to = _parse_date(date_to)

    if parsed_from:
        query = query.filter(AccessLog.timestamp >= parsed_from)
    if parsed_to:
        end_of_day = parsed_to + timedelta(days=1)
        query = query.filter(AccessLog.timestamp < end_of_day)

    logs = query.order_by(AccessLog.timestamp.desc()).all()

    action_counts = {}
    user_activity = {}
    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        display_name = log.user.full_name if log.user else "Unknown"
        user_activity[display_name] = user_activity.get(display_name, 0) + 1

    document_categories = {}
    for document in Document.query.all():
        category = document.category or "General"
        document_categories[category] = document_categories.get(category, 0) + 1

    contract_status_counts = {}
    for status in ["Draft", "Under Review", "Approved", "Active", "Archived"]:
        contract_status_counts[status] = Contract.query.filter_by(status=status).count()

    workflow_summary = {
        "pending": ApprovalStep.query.filter_by(decision=None).count(),
        "approved": ApprovalStep.query.filter_by(decision="Approved").count(),
        "rejected": ApprovalStep.query.filter_by(decision="Rejected").count(),
    }

    generated_by = User.query.get(user_id)
    report = ComplianceReport(
        generated_by=user_id,
        date_range=f"{date_from or 'all'} to {date_to or 'now'}",
        report_type=report_type,
    )
    db.session.add(report)
    db.session.commit()
    log_action(user_id, "GENERATE_REPORT", details=report_type)

    return {
        "report_id": report.report_id,
        "report_type": report_type,
        "generated_at": report.created_date.isoformat() if report.created_date else datetime.utcnow().isoformat(),
        "generated_by": generated_by.full_name if generated_by else "System",
        "date_range": report.date_range,
        "total_events": len(logs),
        "action_breakdown": action_counts,
        "user_activity": dict(sorted(user_activity.items(), key=lambda item: item[1], reverse=True)[:10]),
        "summary": {
            "total_documents": Document.query.count(),
            "active_documents": Document.query.filter_by(status="Active").count(),
            "active_contracts": Contract.query.filter(Contract.status.in_(["Active", "Approved"])).count(),
            "pending_approvals": workflow_summary["pending"],
            "document_categories": document_categories,
            "contract_status_counts": contract_status_counts,
            "workflow_summary": workflow_summary,
        },
        "events": [log.to_dict() for log in logs[:50]],
    }


def _build_pdf_bytes(report_data):
    if canvas is None or letter is None or colors is None or getSampleStyleSheet is None or ParagraphStyle is None or inch is None or Paragraph is None or SimpleDocTemplate is None or Spacer is None or Table is None or TableStyle is None:
        html = (
            "<html><body>"
            f"<h1>{report_data['report_type']}</h1>"
            f"<p>Date range: {report_data['date_range']}</p>"
            f"<p>Total events: {report_data['total_events']}</p>"
            "<ul>"
            + "".join(
                f"<li>{action.replace('_', ' ').title()}: {count}</li>"
                for action, count in report_data["action_breakdown"].items()
            )
            + "</ul></body></html>"
        )
        return html.encode("utf-8")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#0f4c81"))
    heading_style = ParagraphStyle("heading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=colors.HexColor("#0f4c81"), spaceAfter=6)
    body_style = styles["BodyText"]
    small_style = ParagraphStyle("small", parent=styles["BodyText"], fontSize=9, leading=11)

    story = []
    story.append(Paragraph(report_data["report_type"], title_style))
    story.append(Paragraph(f"Generated by {report_data['generated_by']} on {report_data['generated_at']}", body_style))
    story.append(Paragraph(f"Date range: {report_data['date_range']}", body_style))
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Executive summary", heading_style))
    summary_rows = [
        ["Metric", "Value"],
        ["Total logged events", str(report_data["total_events"])],
        ["Documents in repository", str(report_data["summary"]["total_documents"])],
        ["Active documents", str(report_data["summary"]["active_documents"])],
        ["Active contracts", str(report_data["summary"]["active_contracts"])],
        ["Pending approvals", str(report_data["summary"]["pending_approvals"])],
    ]
    summary_table = Table(summary_rows, colWidths=[2.8 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f4c81")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f7f9fc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Document and contract overview", heading_style))
    overview_rows = [["Category", "Count"]]
    for category, count in sorted(report_data["summary"]["document_categories"].items()):
        overview_rows.append([category, str(count)])
    overview_table = Table(overview_rows, colWidths=[3.2 * inch, 1.3 * inch])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6f8b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Contract status distribution", heading_style))
    contract_rows = [["Status", "Count"]]
    for status, count in report_data["summary"]["contract_status_counts"].items():
        contract_rows.append([status, str(count)])
    contract_table = Table(contract_rows, colWidths=[3.2 * inch, 1.3 * inch])
    contract_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3d5a80")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(contract_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Action breakdown", heading_style))
    action_rows = [["Action", "Count"]]
    for action, count in sorted(report_data["action_breakdown"].items(), key=lambda item: item[1], reverse=True):
        action_rows.append([action.replace("_", " ").title(), str(count)])
    action_table = Table(action_rows, colWidths=[3.2 * inch, 1.3 * inch])
    action_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f772d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(action_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Top users by activity", heading_style))
    if report_data["user_activity"]:
        user_rows = [["User", "Activity count"]]
        for user, count in report_data["user_activity"].items():
            user_rows.append([user, str(count)])
        user_table = Table(user_rows, colWidths=[3.2 * inch, 1.3 * inch])
        user_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6a4c93")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(user_table)
    else:
        story.append(Paragraph("No user activity data available for this period.", body_style))
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Detailed recent events", heading_style))
    if report_data["events"]:
        for event in report_data["events"]:
            timestamp = event.get("timestamp", "") or ""
            user = event.get("user") or "Unknown"
            action = (event.get("action") or "").replace("_", " ").title()
            details = event.get("details") or ""
            story.append(Paragraph(f"• {timestamp} — {user} — {action} — {details}", small_style))
            story.append(Spacer(1, 0.04 * inch))
    else:
        story.append(Paragraph("No activity events were found for this date range.", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


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

    report_payload = _build_report_payload(user_id, date_from, date_to, report_type)
    return jsonify(report_payload)


@reports_bp.route("/compliance/download", methods=["GET"])
@jwt_required()
def compliance_report_download():
    user_id = int(get_jwt_identity())
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    report_type = request.args.get("report_type", "Activity Summary")

    report_payload = _build_report_payload(user_id, date_from, date_to, report_type)
    pdf_bytes = _build_pdf_bytes(report_payload)
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf" if canvas is not None else "text/html",
        as_attachment=True,
        download_name=f"{report_type.lower().replace(' ', '_')}.pdf" if canvas is not None else "report.html",
    )


@reports_bp.route("/access-logs", methods=["GET"])
@jwt_required()
def access_logs():
    logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(200).all()
    return jsonify([log.to_dict() for log in logs])
