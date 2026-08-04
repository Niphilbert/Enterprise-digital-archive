import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const DEMO_ACCOUNTS = [
  { role: "Admin", email: "admin@olympeconsulting.rw", password: "Admin@123" },
  { role: "Legal/Contract Manager", email: "legal@olympeconsulting.rw", password: "Legal@123" },
  { role: "Manager", email: "manager@olympeconsulting.rw", password: "Manager@123" },
  { role: "Auditor", email: "auditor@olympeconsulting.rw", password: "Auditor@123" },
  { role: "Staff", email: "staff@olympeconsulting.rw", password: "Staff@123" },
];

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.error || "Unable to log in. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-illustration" aria-hidden="true">
          <div className="company-mark">
            <div className="company-mark__shield">OC</div>
            <div className="company-mark__text">
              <div className="company-mark__name">Olympe Consulting</div>
              <div className="company-mark__tag">Digital Strategy • Contracts • Governance</div>
            </div>
          </div>
          <div className="company-panel">
            <div className="company-panel__header">Enterprise Platform</div>
            <div className="company-panel__body">
              <div className="company-panel__line" />
              <div className="company-panel__line short" />
              <div className="company-panel__line tiny" />
            </div>
          </div>
        </div>

        <div className="login-box">
          <div className="login-logo">ED</div>
          <h1 className="login-title">Enterprise Digital Archive &amp; Contract Management System</h1>
          <p className="login-subtitle">Secure document governance for Olympe Consulting</p>

          {error && <div className="login-error">{error}</div>}

          <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email address</label>
            <input
              type="email"
              placeholder="you@olympeconsulting.rw"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? "Logging in…" : "Log In"}
          </button>
        </form>

          <div className="demo-accounts">
            <div className="demo-title">Demo accounts (click to autofill, after running <code>seed.py</code>):</div>
            {DEMO_ACCOUNTS.map((acc) => (
              <div
                key={acc.email}
                className="demo-row"
                onClick={() => { setEmail(acc.email); setPassword(acc.password); }}
              >
                <span><code>{acc.email}</code> / {acc.password}</span>
                <span>— {acc.role}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
