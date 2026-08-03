"""
Seed script for the Enterprise Digital Archive & Contract Management System.
Run with: python3 seed.py
Creates roles, demo user accounts, and a small set of sample documents/contracts.
Safe to re-run — it skips creation if data already exists.
"""
from datetime import date, timedelta
from app import create_app
from extensions import db
from models import Role, User, Document, DocumentVersion, Contract

app = create_app()

ROLES = [
    ("admin", "manage_users,manage_access,view_all,generate_reports"),
    ("legal_manager", "draft_contract,approve_contract,manage_documents"),
    ("manager", "approve_contract,view_reports"),
    ("auditor", "view_all,generate_reports"),
    ("staff", "upload_document,view_documents"),
]

USERS = [
    ("Alice Admin", "admin@olympeconsulting.rw", "Admin@123", "admin", "IT & Administration"),
    ("Jeanne Uwimana", "legal@olympeconsulting.rw", "Legal@123", "legal_manager", "Legal"),
    ("Paul Mugisha", "manager@olympeconsulting.rw", "Manager@123", "manager", "Operations"),
    ("Grace Niyonzima", "auditor@olympeconsulting.rw", "Auditor@123", "auditor", "Compliance"),
    ("Eric Habimana", "staff@olympeconsulting.rw", "Staff@123", "staff", "Client Services"),
]


def run():
    with app.app_context():
        db.create_all()

        role_map = {}
        if Role.query.count() == 0:
            for name, perms in ROLES:
                r = Role(role_name=name, permissions=perms)
                db.session.add(r)
            db.session.commit()
            print(f"Created {len(ROLES)} roles.")
        for r in Role.query.all():
            role_map[r.role_name] = r.role_id

        user_map = {}
        if User.query.count() == 0:
            for full_name, email, password, role_name, dept in USERS:
                u = User(full_name=full_name, email=email, role_id=role_map[role_name], department=dept)
                u.set_password(password)
                db.session.add(u)
            db.session.commit()
            print(f"Created {len(USERS)} demo users.")
        for u in User.query.all():
            user_map[u.email] = u.user_id

        staff_id = user_map.get("staff@olympeconsulting.rw")
        legal_id = user_map.get("legal@olympeconsulting.rw")

        if Document.query.count() == 0 and staff_id:
            sample_docs = [
                ("Master Service Agreement.pdf", "Contracts", staff_id),
                ("HR Policy Manual.docx", "Policy", legal_id),
                ("Vendor NDA - Olympe.pdf", "Legal", legal_id),
                ("Audit Report Q2.pdf", "Compliance", staff_id),
            ]
            for title, category, uploader in sample_docs:
                doc = Document(title=title, category=category, file_path="placeholder.txt",
                                uploaded_by=uploader, status="Active")
                db.session.add(doc)
                db.session.flush()
                v = DocumentVersion(document_id=doc.document_id, version_number=1,
                                     file_path="placeholder.txt", modified_by=uploader,
                                     note="Initial upload")
                db.session.add(v)
            db.session.commit()
            print(f"Created {len(sample_docs)} sample documents.")

        if Contract.query.count() == 0 and legal_id:
            today = date.today()
            sample_contracts = [
                ("Master Service Agreement — Olympe Consulting", "AUCA", today - timedelta(days=200),
                 today + timedelta(days=165), "Active"),
                ("Vendor NDA", "TechSupply Rwanda Ltd", today - timedelta(days=30),
                 today + timedelta(days=335), "Active"),
                ("Consulting Retainer Agreement", "GreenFields Cooperative", today, today + timedelta(days=365), "Draft"),
            ]
            for title, party, start, end, status in sample_contracts:
                c = Contract(title=title, party_name=party, start_date=start, end_date=end,
                              status=status, owner_id=legal_id)
                db.session.add(c)
            db.session.commit()
            print(f"Created {len(sample_contracts)} sample contracts.")

        print("\nSeed complete. Demo accounts (email / password):")
        for full_name, email, password, role_name, dept in USERS:
            print(f"  {role_name:<15} {email:<35} {password}")


if __name__ == "__main__":
    run()
