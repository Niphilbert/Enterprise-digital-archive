import { useState } from "react";
import { NavLink, Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "📊", end: true },
  { to: "/documents", label: "Document Repository", icon: "📁" },
  { to: "/contracts", label: "Contract Lifecycle", icon: "📄" },
  { to: "/search", label: "Search & Retrieval", icon: "🔍" },
  { to: "/workflow", label: "Workflow & Approvals", icon: "✅" },
  { to: "/versioning", label: "Versioning", icon: "🕓" },
  { to: "/access", label: "Security & Access", icon: "🔐", roles: ["admin"] },
  { to: "/reports", label: "Reports & Compliance", icon: "📈" },
];

function initials(name) {
  if (!name) return "?";
  const parts = name.trim().split(" ");
  return (parts[0][0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
}

export default function Layout() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="mark">ED</div>
          <div className="name">Enterprise Digital Archive &amp; Contract Management</div>
        </div>
        <nav>
          {NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(user.role)).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="main-col">
        <header className="topbar">
          <div className="topbar-title">Olympe Consulting</div>
          <div className="topbar-user">
            <span className="role-badge">{user.role.replace("_", " ")}</span>
            <div className="user-menu">
              <div className="avatar" onClick={() => setMenuOpen((v) => !v)} style={{ cursor: "pointer" }}>
                {initials(user.full_name)}
              </div>
              {menuOpen && (
                <div className="user-dropdown" onMouseLeave={() => setMenuOpen(false)}>
                  <div style={{ padding: "8px 10px", fontSize: 13, fontWeight: 700 }}>{user.full_name}</div>
                  <div style={{ padding: "0 10px 8px", fontSize: 12, color: "var(--muted)" }}>{user.email}</div>
                  <button onClick={logout}>Log out</button>
                </div>
              )}
            </div>
          </div>
        </header>
        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
