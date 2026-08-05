from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Role
from utils import role_required, log_action, assign_pending_approvals

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("", methods=["GET"])
@role_required("admin")
def list_users():
    users = User.query.order_by(User.user_id.asc()).all()
    return jsonify([u.to_dict() for u in users])


@users_bp.route("", methods=["POST"])
@role_required("admin")
def create_user():
    admin_id = int(get_jwt_identity())
    data = request.get_json(force=True) or {}
    required = ["full_name", "email", "password", "role_id"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": f"Missing required fields: {required}"}), 400

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "A user with this email already exists"}), 409

    user = User(full_name=data["full_name"], email=data["email"].lower(),
                role_id=data["role_id"], department=data.get("department", ""))
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()
    assign_pending_approvals(user)
    db.session.commit()
    log_action(admin_id, "CREATE_USER", details=user.email)
    return jsonify(user.to_dict()), 201


@users_bp.route("/<int:user_id>", methods=["PUT"])
@role_required("admin")
def update_user(user_id):
    admin_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json(force=True) or {}

    role_changed = False
    if "role_id" in data:
        role_changed = user.role_id != data["role_id"]
        user.role_id = data["role_id"]
    if "department" in data:
        user.department = data["department"]
    if "full_name" in data:
        user.full_name = data["full_name"]
    if data.get("password"):
        user.set_password(data["password"])

    db.session.commit()
    if role_changed:
        assign_pending_approvals(user)
        db.session.commit()
    log_action(admin_id, "UPDATE_USER", details=user.email)
    return jsonify(user.to_dict())


@users_bp.route("/roles", methods=["GET"])
@jwt_required()
def list_roles():
    roles = Role.query.all()
    return jsonify([r.to_dict() for r in roles])
