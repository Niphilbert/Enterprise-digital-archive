import { useEffect, useState } from "react";
import api from "../api";
import Modal from "../components/Modal";
import { useAuth } from "../context/AuthContext";

function timeAgo(iso) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 60) return `${mins} min${mins === 1 ? "" : "s"}`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"}`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"}`;
}

export default function Workflow() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const { user } = useAuth();

  function load() {
    api.get("/workflow/pending")
      .then((res) => setItems(res.data))
      .catch((err) => {
        setError(err.response?.data?.error || "Could not load pending approvals.");
      });
  }
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Workflow &amp; Approval Management</h1>
          <p className="page-subtitle">Review and decide on items awaiting your approval</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="card" style={{ padding: 0 }}>
        {user?.role !== "manager" ? (
          <div className="empty-state">Only manager accounts can access approval actions.</div>
        ) : items.length === 0 ? (
          <div className="empty-state">You have no pending approvals right now. 🎉</div>
        ) : (
          <table>
            <thead><tr><th>Item</th><th>Requested By</th><th>Pending Since</th><th></th></tr></thead>
            <tbody>
              {items.map((it) => {
                const overdue = timeAgo(it.created_date).includes("day");
                return (
                  <tr key={it.step_id}>
                    <td>{it.contract_title}</td>
                    <td>{it.requested_by}</td>
                    <td style={overdue ? { color: "var(--amber)", fontWeight: 700 } : undefined}>
                      {timeAgo(it.created_date)} ago
                    </td>
                    <td><button className="btn btn-primary btn-sm" onClick={() => setSelected(it)}>Review</button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {selected && (
        <ReviewModal
          item={selected}
          onClose={() => setSelected(null)}
          onDecided={() => { setSelected(null); load(); }}
          setError={setError}
        />
      )}
    </div>
  );
}

function ReviewModal({ item, onClose, onDecided, setError }) {
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const { user } = useAuth();

  async function decide(decision) {
    setBusy(true); setError("");
    try {
      await api.post(`/workflow/steps/${item.step_id}/decide`, { decision, comment });
      onDecided();
    } catch (err) {
      setError(err.response?.data?.error || "Could not record decision.");
      setBusy(false);
    }
  }

  return (
    <Modal title={item.contract_title} subtitle={`Requested by ${item.requested_by}`} onClose={onClose}>
      <div className="field">
        <label>Comment (optional)</label>
        <textarea rows={3} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Add a note for the requester…" />
      </div>
      <div className="modal-actions">
        <button className="btn btn-outline" onClick={onClose} disabled={busy}>Cancel</button>
        {user?.role === "manager" ? (
          <>
            <button className="btn btn-red" onClick={() => decide("Rejected")} disabled={busy}>Reject</button>
            <button className="btn btn-green" onClick={() => decide("Approved")} disabled={busy}>Approve</button>
          </>
        ) : null}
      </div>
    </Modal>
  );
}
