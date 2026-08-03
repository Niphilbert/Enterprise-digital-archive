import { useState } from "react";
import api from "../api";

export default function Reports() {
  const [reportType, setReportType] = useState("Activity Summary");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generate(e) {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const res = await api.get("/reports/compliance", {
        params: { report_type: reportType, date_from: dateFrom, date_to: dateTo },
      });
      setReport(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Could not generate report.");
    } finally {
      setLoading(false);
    }
  }

  function printReport() {
    window.print();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reporting &amp; Compliance</h1>
          <p className="page-subtitle">Generate activity and compliance reports for audit purposes</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-2">
        <div className="card">
          <h3 className="card-title">Generate Report</h3>
          <form onSubmit={generate}>
            <div className="field">
              <label>Report Type</label>
              <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
                <option>Activity Summary</option>
                <option>Document Access Log</option>
                <option>Contract Approval Audit</option>
              </select>
            </div>
            <div className="field">
              <label>Date From</label>
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </div>
            <div className="field">
              <label>Date To</label>
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
              {loading ? "Generating…" : "Generate Report"}
            </button>
          </form>
        </div>

        <div className="card">
          <h3 className="card-title">Result</h3>
          {!report ? (
            <div className="empty-state">Configure and generate a report to see results here.</div>
          ) : (
            <div>
              <p><strong>{report.report_type}</strong> — {report.date_range}</p>
              <p className="muted">Total logged events: {report.total_events}</p>
              <table>
                <thead><tr><th>Action</th><th>Count</th></tr></thead>
                <tbody>
                  {Object.entries(report.action_breakdown).map(([action, count]) => (
                    <tr key={action}><td>{action.replace(/_/g, " ")}</td><td>{count}</td></tr>
                  ))}
                </tbody>
              </table>
              <button className="btn btn-outline" style={{ marginTop: 14 }} onClick={printReport}>Export as PDF</button>
            </div>
          )}
        </div>
      </div>

      {report && report.events.length > 0 && (
        <div className="card">
          <h3 className="card-title">Event Detail</h3>
          <table>
            <thead><tr><th>User</th><th>Action</th><th>Details</th><th>Timestamp</th></tr></thead>
            <tbody>
              {report.events.slice(0, 20).map((ev) => (
                <tr key={ev.log_id}>
                  <td>{ev.user}</td>
                  <td>{ev.action.replace(/_/g, " ")}</td>
                  <td>{ev.details}</td>
                  <td>{new Date(ev.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
