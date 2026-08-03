# Enterprise Digital Archive & Contract Management System (EDACMS)

A full-stack implementation for Olympe Consulting, built with:
- **Backend:** Python (Flask) + MySQL
- **Frontend:** JavaScript (React + Vite)

Implements all modules designed earlier: Digital Document Repository, Contract
Lifecycle Management, Search & Retrieval, Workflow & Approval Management,
Versioning & Change Management, Security & Access Governance (RBAC), and
Reporting & Compliance.

---

## 1. Prerequisites

Install these on your computer before starting:

| Tool | Minimum Version | Check with |
|---|---|---|
| Python | 3.10+ | `python3 --version` |
| Node.js | 18+ | `node -v` |
| MySQL Server (or MariaDB) | 8.0 / 10.x | `mysql --version` |
| npm | comes with Node | `npm -v` |

If you don't have MySQL installed:
- **Windows:** install [MySQL Installer](https://dev.mysql.com/downloads/installer/) or XAMPP.
- **macOS:** `brew install mysql && brew services start mysql`
- **Linux (Ubuntu/Debian):** `sudo apt install mysql-server && sudo systemctl start mysql`

---

## 2. Set up the database

Open a MySQL shell (`mysql -u root -p`) and run:

```sql
CREATE DATABASE edacms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'edacms_user'@'localhost' IDENTIFIED BY 'edacms_pass';
GRANT ALL PRIVILEGES ON edacms.* TO 'edacms_user'@'localhost';
FLUSH PRIVILEGES;
```

(You can use different credentials — just update `backend/config.py` or set
the environment variables `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`,
`DB_NAME` accordingly.)

---

## 3. Run the backend (Flask API)

```bash
cd backend
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate          # macOS/Linux
venv\Scripts\activate             # Windows (Command Prompt / PowerShell)

pip install -r requirements.txt

# Create the database tables and demo data
python3 seed.py

# Start the API server
python3 app.py
```

The API will start at **http://127.0.0.1:5000**. You should see:
```
* Running on http://0.0.0.0:5000
```

Leave this terminal window running. Open a **new terminal** for the frontend.

---

## 4. Run the frontend (React app)

```bash
cd frontend
npm install
npm run dev
```

The app will start at **http://127.0.0.1:5173** (Vite will print the exact
URL). Open that URL in your browser.

---

## 5. Log in

Use any of the demo accounts created by `seed.py` (also shown on the login
screen — click a row to autofill):

| Role | Email | Password |
|---|---|---|
| Admin | admin@olympeconsulting.rw | Admin@123 |
| Legal / Contract Manager | legal@olympeconsulting.rw | Legal@123 |
| Manager | manager@olympeconsulting.rw | Manager@123 |
| Auditor | auditor@olympeconsulting.rw | Auditor@123 |
| Staff | staff@olympeconsulting.rw | Staff@123 |

---

## 6. What to try

- **Login as Staff** → Document Repository → Upload a document.
- **Login as Legal/Contract Manager** → Contracts → Draft New Contract → open it → Submit for Approval.
- **Login as Manager** → Workflow & Approvals → Review the pending item → Approve or Reject.
- **Login as Legal/Contract Manager again** → Contracts → the contract is now "Active"; try Renew or Archive.
- **Login as any user** → Search & Retrieval → search by keyword, category, or date.
- **Open a document** → Versioning → upload a new version, then Rollback to an earlier one.
- **Login as Admin** → Security & Access → view/add users and see the role-permission matrix.
- **Login as Auditor** → Reports & Compliance → generate a report and export it (Print to PDF).
- **Dashboard** (any role) → live counts and recent activity feed update automatically as you use the system.

---

## 7. Project structure

```
edacms/
├── backend/
│   ├── app.py            # Flask app factory + entry point
│   ├── config.py         # DB connection settings (reads env vars)
│   ├── extensions.py     # SQLAlchemy + JWT setup
│   ├── models.py         # Database models (matches the ERD/data dictionary)
│   ├── utils.py          # role_required decorator, audit logging
│   ├── seed.py           # creates roles, demo users, sample data
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth.py           # login, /me
│   │   ├── documents.py      # upload, search, versions, rollback, download
│   │   ├── contracts.py      # draft, submit, renew, archive
│   │   ├── workflow.py       # pending approvals, decide
│   │   ├── users.py          # admin: manage users & roles
│   │   └── reports.py        # dashboard metrics, compliance reports
│   └── uploads/           # uploaded files are stored here
└── frontend/
    └── src/
        ├── api.js                 # axios client with JWT handling
        ├── context/AuthContext.jsx
        ├── components/            # Layout, Modal, StatusBadge
        └── pages/                 # Login, Dashboard, Documents, Contracts,
                                    # Search, Workflow, Versioning, Access, Reports
```

---

## 8. Troubleshooting

- **"Can't connect to MySQL server"** → make sure MySQL is running (`mysql.server start` on macOS, `sudo systemctl start mysql` on Linux, or start the MySQL service on Windows).
- **CORS or "Network Error" in the browser** → make sure the Flask backend is running on port 5000 before you open the frontend.
- **Port already in use** → stop whatever is using port 5000 or 5173, or change the port in `backend/app.py` (`app.run(port=...)`) and `frontend/src/api.js` (`API_BASE`).
- **Re-running `seed.py`** is safe — it only creates data if the tables are empty. To fully reset, drop and recreate the `edacms` database, then re-run `seed.py`.

---

## 9. Moving to production

This setup uses Flask's development server and Vite's dev server, which are
fine for demos and coursework but not for production. For a real deployment
you would additionally want to: run Flask behind Gunicorn/uWSGI + Nginx,
build the frontend with `npm run build` and serve the static files, set
strong values for `SECRET_KEY`/`JWT_SECRET_KEY` via environment variables,
and store uploaded files in a dedicated storage service.
