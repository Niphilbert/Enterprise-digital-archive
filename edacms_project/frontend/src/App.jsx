import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Contracts from "./pages/Contracts";
import Search from "./pages/Search";
import Workflow from "./pages/Workflow";
import Versioning from "./pages/Versioning";
import Access from "./pages/Access";
import Reports from "./pages/Reports";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/contracts" element={<Contracts />} />
            <Route path="/search" element={<Search />} />
            <Route path="/workflow" element={<Workflow />} />
            <Route path="/versioning" element={<Versioning />} />
            <Route path="/access" element={<Access />} />
            <Route path="/reports" element={<Reports />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
