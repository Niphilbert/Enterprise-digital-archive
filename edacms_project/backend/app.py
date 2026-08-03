import os
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    jwt.init_app(app)

    from routes.auth import auth_bp
    from routes.documents import documents_bp
    from routes.contracts import contracts_bp
    from routes.workflow import workflow_bp
    from routes.users import users_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(reports_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "EDACMS API"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
