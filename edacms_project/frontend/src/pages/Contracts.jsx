import { useEffect, useState } from "react";
import api from "../api";
import Modal from "../components/Modal";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";

const STAGES = ["Draft", "Under Review", "Approved", "Active", "Renewal Due", "Archived"];

export default function Contracts() {
  const [contracts, setContracts] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const { user } = useAuth();

  function load() {
    api.get("/contracts").then((res) => setContracts(res.data));
  }
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Contract Lifecycle Management</h1>
          <p className="page-subtitle">Draft, route for approval, renew, and archive contracts</p>
        </div>
        {["legal_manager", "admin"].includes(user.role) && (
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ Draft New Contract</button>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="card" style={{ padding: 0 }}>
        {contracts.length === 0 ? (
          <div className="empty-state">No contracts yet. Draft your first contract to get started.</div>
        ) : (
          <table>
            <thead>
              <tr><th>Title</th><th>Party</th><th>Start</th><th>End</th><th>Owner</th><th>Status</th></tr>
            </thead>
            <tbody>
              {contracts.map((c) => (
                <tr key={c.contract_id} className="clickable" onClick={() => setSelected(c)}>
                  <td>{c.title}</td>
                  <td>{c.party_name}</td>
                  <td>{c.start_date}</td>
                  <td>{c.end_date}</td>
                  <td>{c.owner}</td>
                  <td><StatusBadge status={c.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && (
        <CreateContractModal
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); }}
          setError={setError}
        />
      )}

      {selected && (
        <ContractDetailModal
          contractId={selected.contract_id}
          onClose={() => setSelected(null)}
          onChanged={() => { load(); setSelected(null); }}
          setError={setError}
        />
      )}
    </div>
  );
}

function CreateContractModal({ onClose, onCreated, setError }) {
  const [title, setTitle] = useState("");
  const [partyName, setPartyName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await api.post("/contracts", { title, party_name: partyName, start_date: startDate, end_date: endDate });
      onCreated();
    } catch (err) {
      setError(err.response?.data?.error || "Could not create contract.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal title="Draft New Contract" subtitle="Create a new contract in Draft status" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Contract Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="e.g. Consulting Retainer Agreement" />
        </div>
        <div className="field">
          <label>Party / Client Name</label>
          <input value={partyName} onChange={(e) => setPartyName(e.target.value)} required placeholder="e.g. AUCA" />
        </div>
        <div className="field">
          <label>Start Date</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
        </div>
        <div className="field">
          <label>End Date</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Saving…" : "Create Draft"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ContractDetailModal({ contractId, onClose, onChanged, setError }) {
  const [contract, setContract] = useState(null);
  const [busy, setBusy] = useState(false);
  const [newEndDate, setNewEndDate] = useState("");
  const { user } = useAuth();

  function load() {
    api.get(`/contracts/${contractId}`).then((res) => setContract(res.data));
  }
  useEffect(() => { load(); }, [contractId]);

  async function submitForApproval() {
    setBusy(true); setError("");
    try {
      await api.post(`/contracts/${contractId}/submit`);
      onChanged();
    } catch (err) {
      setError(err.response?.data?.error || "Could not submit for approval.");
      setBusy(false);
    }
  }

  async function renew() {
    if (!newEndDate) return;
    setBusy(true); setError("");
    try {
      await api.post(`/contracts/${contractId}/renew`, { new_end_date: newEndDate });
      onChanged();
    } catch (err) {
      setError(err.response?.data?.error || "Could not renew contract.");
      setBusy(false);
    }
  }

  async function archive() {
    setBusy(true); setError("");
    try {
      await api.post(`/contracts/${contractId}/archive`);
      onChanged();
    } catch (err) {
      setError(err.response?.data?.error || "Could not archive contract.");
      setBusy(false);
    }
  }

  if (!contract) return null;

  const stageIndex = Math.max(0, STAGES.indexOf(contract.status));

  return (
    <Modal title={contract.title} subtitle={`${contract.party_name} — Owned by ${contract.owner}`} onClose={onClose} width={620}>
      <div className="steps-row">
        {STAGES.map((s, i) => (
          <span key={s} className={"step-pill" + (i < stageIndex ? " done" : i === stageIndex ? " current" : "")}>
            {s}
          </span>
        ))}
      </div>

      <p><strong>Start:</strong> {contract.start_date} &nbsp; <strong>End:</strong> {contract.end_date}</p>
      <p><strong>Status:</strong> <StatusBadge status={contract.status} /></p>

      {contract.approval_steps && contract.approval_steps.length > 0 && (
        <>
          <h4 style={{ marginBottom: 8, fontSize: 13.5 }}>Approval History</h4>
          <ul className="timeline">
            {contract.approval_steps.map((s) => (
              <li key={s.step_id}>
                <span className="dot" />
                <div>
                  <div>Approver: {s.approver} — {s.decision || "Pending"}</div>
                  {s.comment && <div className="meta">"{s.comment}"</div>}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="modal-actions" style={{ flexWrap: "wrap" }}>
        {contract.status === "Draft" && ["legal_manager", "admin"].includes(user.role) && (
          <button className="btn btn-primary" disabled={busy} onClick={submitForApproval}>Submit for Approval</button>
        )}
        {(contract.status === "Active" || contract.status === "Renewal Due") && ["legal_manager", "admin"].includes(user.role) && (
          <>
            <input type="date" value={newEndDate} onChange={(e) => setNewEndDate(e.target.value)} style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid var(--border)" }} />
            <button className="btn btn-green" disabled={busy || !newEndDate} onClick={renew}>Renew</button>
            <button className="btn btn-red" disabled={busy} onClick={archive}>Archive</button>
          </>
        )}
        <button className="btn btn-outline" onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
