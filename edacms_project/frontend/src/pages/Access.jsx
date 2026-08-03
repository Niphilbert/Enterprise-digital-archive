import { useEffect, useState } from "react";
import api from "../api";
import Modal from "../components/Modal";

export default function Access() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState("");

  function load() {
    api.get("/users").then((res) => setUsers(res.data)).catch(() => setError("Could not load users."));
    api.get("/users/roles").then((res) => setRoles(res.data));
  }
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Security &amp; Access Governance</h1>
          <p className="page-subtitle">Manage user accounts, roles, and permissions</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ Add User</button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-2">
        <div className="card" style={{ padding: 0, gridColumn: "1 / -1" }}>
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Department</th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id}>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td><span className="role-badge">{u.role.replace("_", " ")}</span></td>
                  <td>{u.department || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3 className="card-title">Role-Based Access Matrix</h3>
        <table>
          <thead><tr><th>Role</th><th>Documents</th><th>Contracts</th><th>Reports</th><th>Admin</th></tr></thead>
          <tbody>
            <tr><td>Staff</td><td>View / Upload</td><td>View</td><td>—</td><td>—</td></tr>
            <tr><td>Legal / Contract Manager</td><td>View / Edit</td><td>Full</td><td>View</td><td>—</td></tr>
            <tr><td>Manager</td><td>View</td><td>Approve</td><td>View</td><td>—</td></tr>
            <tr><td>Admin</td><td>Full</td><td>Full</td><td>Full</td><td>Full</td></tr>
            <tr><td>Auditor</td><td>View</td><td>View</td><td>Full</td><td>—</td></tr>
          </tbody>
        </table>
      </div>

      {showCreate && (
        <CreateUserModal
          roles={roles}
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); }}
          setError={setError}
        />
      )}
    </div>
  );
}

function CreateUserModal({ roles, onClose, onCreated, setError }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState(roles[0]?.role_id || "");
  const [department, setDepartment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true); setError("");
    try {
      await api.post("/users", { full_name: fullName, email, password, role_id: Number(roleId), department });
      onCreated();
    } catch (err) {
      setError(err.response?.data?.error || "Could not create user.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal title="Add User" subtitle="Create a new account and assign a role" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="field"><label>Full Name</label><input value={fullName} onChange={(e) => setFullName(e.target.value)} required /></div>
        <div className="field"><label>Email</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
        <div className="field"><label>Temporary Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
        <div className="field">
          <label>Role</label>
          <select value={roleId} onChange={(e) => setRoleId(e.target.value)}>
            {roles.map((r) => <option key={r.role_id} value={r.role_id}>{r.role_name.replace("_", " ")}</option>)}
          </select>
        </div>
        <div className="field"><label>Department</label><input value={department} onChange={(e) => setDepartment(e.target.value)} /></div>
        <div className="modal-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "Creating…" : "Create User"}</button>
        </div>
      </form>
    </Modal>
  );
}
