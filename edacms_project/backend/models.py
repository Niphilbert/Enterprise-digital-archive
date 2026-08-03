from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class Role(db.Model):
    __tablename__ = "roles"
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.Text)

    users = db.relationship("User", backref="role", lazy=True)

    def to_dict(self):
        return {"role_id": self.role_id, "role_name": self.role_name, "permissions": self.permissions}


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"), nullable=False)
    department = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role.role_name if self.role else None,
            "role_id": self.role_id,
            "department": self.department,
        }


class Document(db.Model):
    __tablename__ = "documents"
    document_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="Active")

    versions = db.relationship("DocumentVersion", backref="document", lazy=True,
                                order_by="DocumentVersion.version_number")
    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    def to_dict(self):
        return {
            "document_id": self.document_id,
            "title": self.title,
            "category": self.category,
            "uploaded_by": self.uploader.full_name if self.uploader else None,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "status": self.status,
            "version_count": len(self.versions),
        }


class DocumentVersion(db.Model):
    __tablename__ = "document_versions"
    version_id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.document_id"), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    modified_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(255))

    modifier = db.relationship("User", foreign_keys=[modified_by])

    def to_dict(self):
        return {
            "version_id": self.version_id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "modified_by": self.modifier.full_name if self.modifier else None,
            "modified_date": self.modified_date.isoformat() if self.modified_date else None,
            "note": self.note,
        }


class Contract(db.Model):
    __tablename__ = "contracts"
    contract_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    party_name = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), default="Draft")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    owner = db.relationship("User", foreign_keys=[owner_id])
    workflows = db.relationship("Workflow", backref="contract", lazy=True)

    def to_dict(self):
        return {
            "contract_id": self.contract_id,
            "title": self.title,
            "party_name": self.party_name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "owner": self.owner.full_name if self.owner else None,
        }


class Workflow(db.Model):
    __tablename__ = "workflows"
    workflow_id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.contract_id"), nullable=False)
    current_step = db.Column(db.String(100))
    status = db.Column(db.String(30), default="Pending")

    steps = db.relationship("ApprovalStep", backref="workflow", lazy=True)

    def to_dict(self):
        return {
            "workflow_id": self.workflow_id,
            "contract_id": self.contract_id,
            "current_step": self.current_step,
            "status": self.status,
        }


class ApprovalStep(db.Model):
    __tablename__ = "approval_steps"
    step_id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflows.workflow_id"), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    decision = db.Column(db.String(20))
    comment = db.Column(db.Text)
    decision_date = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    approver = db.relationship("User", foreign_keys=[approver_id])

    def to_dict(self):
        contract = self.workflow.contract if self.workflow else None
        return {
            "step_id": self.step_id,
            "workflow_id": self.workflow_id,
            "contract_id": contract.contract_id if contract else None,
            "contract_title": contract.title if contract else None,
            "requested_by": contract.owner.full_name if contract and contract.owner else None,
            "approver": self.approver.full_name if self.approver else None,
            "decision": self.decision,
            "comment": self.comment,
            "created_date": self.created_date.isoformat() if self.created_date else None,
        }


class AccessLog(db.Model):
    __tablename__ = "access_logs"
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.document_id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user": self.user.full_name if self.user else None,
            "document_id": self.document_id,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class ComplianceReport(db.Model):
    __tablename__ = "compliance_reports"
    report_id = db.Column(db.Integer, primary_key=True)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    date_range = db.Column(db.String(50))
    report_type = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    summary_json = db.Column(db.Text)

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "date_range": self.date_range,
            "report_type": self.report_type,
            "created_date": self.created_date.isoformat() if self.created_date else None,
        }
