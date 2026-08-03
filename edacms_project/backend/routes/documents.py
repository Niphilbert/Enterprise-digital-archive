import os
import uuid
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import Document, DocumentVersion
from utils import log_action

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")


def _save_file(file_storage):
    filename = secure_filename(file_storage.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(path)
    return unique_name


@documents_bp.route("", methods=["GET"])
@jwt_required()
def list_documents():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    query = Document.query
    if q:
        query = query.filter(Document.title.ilike(f"%{q}%"))
    if category:
        query = query.filter(Document.category == category)
    if date_from:
        query = query.filter(Document.upload_date >= date_from)
    if date_to:
        query = query.filter(Document.upload_date <= date_to + " 23:59:59")

    docs = query.order_by(Document.upload_date.desc()).all()
    return jsonify([d.to_dict() for d in docs])


@documents_bp.route("", methods=["POST"])
@jwt_required()
def upload_document():
    user_id = int(get_jwt_identity())
    title = request.form.get("title")
    category = request.form.get("category", "General")
    file = request.files.get("file")

    if not title or not file:
        return jsonify({"error": "title and file are required"}), 400

    stored_name = _save_file(file)
    doc = Document(title=title, category=category, file_path=stored_name,
                    uploaded_by=user_id, status="Active")
    db.session.add(doc)
    db.session.flush()

    version = DocumentVersion(document_id=doc.document_id, version_number=1,
                               file_path=stored_name, modified_by=user_id,
                               note="Initial upload")
    db.session.add(version)
    db.session.commit()

    log_action(user_id, "UPLOAD_DOCUMENT", document_id=doc.document_id, details=title)
    return jsonify(doc.to_dict()), 201


@documents_bp.route("/<int:doc_id>", methods=["GET"])
@jwt_required()
def get_document(doc_id):
    user_id = int(get_jwt_identity())
    doc = Document.query.get_or_404(doc_id)
    log_action(user_id, "VIEW_DOCUMENT", document_id=doc.document_id, details=doc.title)
    return jsonify(doc.to_dict())


@documents_bp.route("/<int:doc_id>/versions", methods=["GET"])
@jwt_required()
def list_versions(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return jsonify([v.to_dict() for v in doc.versions])


@documents_bp.route("/<int:doc_id>/versions", methods=["POST"])
@jwt_required()
def upload_new_version(doc_id):
    user_id = int(get_jwt_identity())
    doc = Document.query.get_or_404(doc_id)
    file = request.files.get("file")
    note = request.form.get("note", "")
    if not file:
        return jsonify({"error": "file is required"}), 400

    stored_name = _save_file(file)
    next_number = max([v.version_number for v in doc.versions], default=0) + 1
    version = DocumentVersion(document_id=doc.document_id, version_number=next_number,
                               file_path=stored_name, modified_by=user_id, note=note or "Updated")
    doc.file_path = stored_name
    db.session.add(version)
    db.session.commit()

    log_action(user_id, "NEW_VERSION", document_id=doc.document_id, details=f"v{next_number}")
    return jsonify(version.to_dict()), 201


@documents_bp.route("/<int:doc_id>/versions/<int:version_id>/rollback", methods=["POST"])
@jwt_required()
def rollback_version(doc_id, version_id):
    user_id = int(get_jwt_identity())
    doc = Document.query.get_or_404(doc_id)
    target = DocumentVersion.query.get_or_404(version_id)
    if target.document_id != doc.document_id:
        return jsonify({"error": "version does not belong to this document"}), 400

    next_number = max([v.version_number for v in doc.versions], default=0) + 1
    new_version = DocumentVersion(
        document_id=doc.document_id, version_number=next_number,
        file_path=target.file_path, modified_by=user_id,
        note=f"Rollback to v{target.version_number}",
    )
    doc.file_path = target.file_path
    db.session.add(new_version)
    db.session.commit()

    log_action(user_id, "ROLLBACK_VERSION", document_id=doc.document_id,
               details=f"rolled back to v{target.version_number} as new v{next_number}")
    return jsonify(new_version.to_dict()), 201


@documents_bp.route("/<int:doc_id>/download", methods=["GET"])
@jwt_required()
def download_document(doc_id):
    user_id = int(get_jwt_identity())
    doc = Document.query.get_or_404(doc_id)
    log_action(user_id, "DOWNLOAD_DOCUMENT", document_id=doc.document_id, details=doc.title)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], doc.file_path, as_attachment=True)


@documents_bp.route("/categories", methods=["GET"])
@jwt_required()
def categories():
    cats = db.session.query(Document.category).distinct().all()
    return jsonify(sorted({c[0] for c in cats if c[0]}))
