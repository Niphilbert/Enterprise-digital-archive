import { useEffect, useState } from "react";
import api from "../api";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/reports/dashboard")
      .then((res) => setData(res.data))
      .catch(() => setError("Could not load dashboard data."));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return <div className="empty-state">Loading dashboard…</div>;

  const maxCount = Math.max(1, ...Object.values(data.contract_status_counts));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Overview of documents, contracts, and recent activity</p>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="label">Total Documents</div>
          <div className="value">{data.total_documents}</div>
        </div>
        <div className="stat-card">
          <div className="label">Active Contracts</div>
          <div className="value">{data.active_contracts}</div>
        </div>
        <div className="stat-card">
          <div className="label">Pending Approvals</div>
          <div className="value">{data.pending_approvals}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 className="card-title">Contract Status Overview</h3>
          {Object.entries(data.contract_status_counts).map(([status, count]) => (
            <div key={status} style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                <span>{status}</span>
                <span className="muted">{count}</span>
              </div>
              <div className="progress-bar">
                <div style={{ width: `${(count / maxCount) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>

        <div className="card">
          <h3 className="card-title">Recent Activity</h3>
          {data.recent_activity.length === 0 && <div className="empty-state">No recent activity yet.</div>}
          <ul className="timeline">
            {data.recent_activity.map((a, i) => (
              <li key={i}>
                <span className="dot" />
                <span>{a}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
