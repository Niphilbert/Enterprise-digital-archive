from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from extensions import db
from models import AccessLog


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
