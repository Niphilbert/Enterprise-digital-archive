export default function Modal({ title, subtitle, onClose, children, width }) {
  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-box" style={width ? { maxWidth: width } : undefined}>
        <h3 className="modal-title">{title}</h3>
        {subtitle && <p className="modal-subtitle">{subtitle}</p>}
        {children}
      </div>
    </div>
  );
}
