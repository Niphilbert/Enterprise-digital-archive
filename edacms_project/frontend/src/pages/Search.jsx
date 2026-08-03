import { useEffect, useState } from "react";
import api, { API_BASE } from "../api";

export default function Search() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [categories, setCategories] = useState([]);
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);

  useEffect(() => { api.get("/documents/categories").then((res) => setCategories(res.data)); }, []);

  async function runSearch(e) {
    e?.preventDefault();
    const res = await api.get("/documents", { params: { q, category, date_from: dateFrom, date_to: dateTo } });
    setResults(res.data);
    setSearched(true);
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Search &amp; Retrieval</h1>
          <p className="page-subtitle">Find documents by keyword, category, or date range</p>
        </div>
      </div>

      <form className="card" onSubmit={runSearch}>
        <div className="toolbar" style={{ marginBottom: 0 }}>
          <input className="search-input" placeholder="Keyword…" value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} title="From date" />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} title="To date" />
          <button className="btn btn-primary" type="submit">Search</button>
        </div>
      </form>

      {searched && (
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: "14px 20px 0", fontWeight: 700, fontSize: 14 }}>
            Results ({results.length} document{results.length === 1 ? "" : "s"} found)
          </div>
          {results.length === 0 ? (
            <div className="empty-state">No documents match your search criteria. Try broadening your filters.</div>
          ) : (
            <table>
              <thead><tr><th>Title</th><th>Category</th><th>Uploaded By</th><th>Date</th><th></th></tr></thead>
              <tbody>
                {results.map((d) => (
                  <tr key={d.document_id}>
                    <td>📄 {d.title}</td>
                    <td>{d.category}</td>
                    <td>{d.uploaded_by}</td>
                    <td>{d.upload_date ? new Date(d.upload_date).toLocaleDateString() : "—"}</td>
                    <td>
                      <a className="link-btn" href={`${API_BASE}/documents/${d.document_id}/download`} target="_blank" rel="noreferrer">
                        Download
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
