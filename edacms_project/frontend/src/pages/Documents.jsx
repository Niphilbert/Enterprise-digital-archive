import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import Modal from "../components/Modal";

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function load() {
    api.get("/documents", { params: { q, category } }).then((res) => setDocs(res.data));
  }

  async function downloadDocument(documentId, title) {
    try {
      const res = await api.get(`/documents/${documentId}/download`, { responseType: "blob" });
      const blob = new Blob([res.data], { type: res.headers["content-type"] || "application/octet-stream" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = title || `document-${documentId}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error || "Download failed.");
    }
  }

  useEffect(() => { load(); }, [q, category]);
  useEffect(() => { api.get("/documents/categories").then((res) => setCategories(res.data)); }, [showUpload]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Document Repository</h1>
          <p className="page-subtitle">Upload, classify, and retrieve enterprise documents</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(true)}>+ Upload Document</button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="toolbar">
        <input className="search-input" placeholder="Search documents…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {docs.length === 0 ? (
          <div className="empty-state">No documents found. Try adjusting your search or upload a new one.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Title</th><th>Category</th><th>Uploaded By</th><th>Date</th><th>Versions</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.document_id} className="clickable" onClick={() => navigate(`/versioning?doc=${d.document_id}`)}>
                  <td>{d.title}</td>
                  <td>{d.category}</td>
                  <td>{d.uploaded_by}</td>
                  <td>{d.upload_date ? new Date(d.upload_date).toLocaleDateString() : "—"}</td>
                  <td>{d.version_count}</td>
                  <td><span className="badge badge-active">{d.status}</span></td>
                  <td>
                    <button
                      className="link-btn"
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        downloadDocument(d.document_id, d.title);
                      }}
                    >
                      Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onUploaded={() => { setShowUpload(false); load(); }}
          setError={setError}
        />
      )}
    </div>
  );
}

function UploadModal({ onClose, onUploaded, setError }) {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("General");
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setSubmitting(true);
    setError("");
    try {
      const form = new FormData();
      form.append("title", title);
      form.append("category", category);
      form.append("file", file);
      await api.post("/documents", form, { headers: { "Content-Type": "multipart/form-data" } });
      onUploaded();
    } catch (err) {
      setError(err.response?.data?.error || "Upload failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal title="Upload Document" subtitle="Add a new document to the digital archive" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="e.g. Master Service Agreement.pdf" />
        </div>
        <div className="field">
          <label>Category</label>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {["General", "Contracts", "Legal", "Policy", "Compliance", "Finance"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>File</label>
          <input type="file" onChange={(e) => setFile(e.target.files[0])} required />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Uploading…" : "Upload"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
