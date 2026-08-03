export default function StatusBadge({ status }) {
  const cls = "badge-" + (status || "").toLowerCase().replace(/\s+/g, "");
  return <span className={`badge ${cls}`}>{status}</span>;
}
