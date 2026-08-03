import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../api";
import Modal from "../components/Modal";

export default function Versioning() {
  const [searchParams] = useSearchParams();
  const [docs, setDocs] = useState([]);
  const [docId, setDocId] = useState(searchParams.get("doc") || "");
  const [versions, setVersions] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => { api.get("/documents").then((res) => {
    setDocs(res.data);
    if (!docId && res.data.length) setDocId(String(res.data[0].document_id));
  }); }, []);

  function loadVersions(id) {
    if (!id) return;
    api.get(`/documents/${id}/versions`).then((res) => setVersions(res.data));
  }
  useEffect(() => { loadVersions(docId); }, [docId]);

  const currentDoc = docs.find((d) => String(d.document_id) === String(docId));

  async function rollback(versionId) {
    setError(""); setSuccess("");
    try {
      await api.post(`/documents/${docId}/versions/${versionId}/rollback`);
      setSuccess("Rolled back successfully — a new version was created reflecting the restored content.");
      loadVersions(docId);
    } catch (err) {
      setError(err.response?.data?.error || "Could not roll back this version.");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Versioning &amp; Change Management</h1>
          <p className="page-subtitle">Review a document's history and roll back if necessary</p>
        </div>
        {currentDoc && <button className="btn btn-primary" onClick={() => setShowUpload(true)}>+ Upload New Version</button>}
      </div>

      <div className="toolbar">
        <select value={docId} onChange={(e) => setDocId(e.target.value)} style={{ minWidth: 280 }}>
          {docs.map((d) => <option key={d.document_id} value={d.document_id}>{d.title}</option>)}
        </select>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <div className="card">
        <h3 className="card-title">Version History {currentDoc ? `— ${currentDoc.title}` : ""}</h3>
        {versions.length === 0 ? (
          <div className="empty-state">No versions recorded yet.</div>
        ) : (
          <ul className="timeline">
            {[...versions].reverse().map((v) => (
              <li key={v.version_id}>
                <span className="dot" />
                <div style={{ flex: 1 }}>
                  <div><strong>v{v.version_number}.0</strong> &nbsp; {v.modified_by} &nbsp; · &nbsp; {new Date(v.modified_date).toLocaleString()}</div>
                  <div className="meta">{v.note}</div>
                </div>
                {v.version_number !== versions[versions.length - 1].version_number && (
                  <button className="btn btn-amber btn-sm" onClick={() => rollback(v.version_id)}>Rollback</button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {showUpload && currentDoc && (
        <NewVersionModal
          docId={docId}
          onClose={() => setShowUpload(false)}
          onUploaded={() => { setShowUpload(false); loadVersions(docId); }}
          setError={setError}
        />
      )}
    </div>
  );
}

function NewVersionModal({ docId, onClose, onUploaded, setError }) {
  const [file, setFile] = useState(null);
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setSubmitting(true); setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("note", note);
      await api.post(`/documents/${docId}/versions`, form, { headers: { "Content-Type": "multipart/form-data" } });
      onUploaded();
    } catch (err) {
      setError(err.response?.data?.error || "Could not upload new version.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal title="Upload New Version" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>File</label>
          <input type="file" onChange={(e) => setFile(e.target.files[0])} required />
        </div>
        <div className="field">
          <label>Note (optional)</label>
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Clause 7 amended" />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "Uploading…" : "Upload"}</button>
        </div>
      </form>
    </Modal>
  );
}
