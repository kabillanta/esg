import { useState, useEffect } from "react";
import { Outlet, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  UploadCloud,
  Database,
  ChevronDown,
} from "lucide-react";
import { AuthService } from "../../api";
import toast from "react-hot-toast";

const Layout = () => {
  const [user, setUser] = useState<any>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  useEffect(() => {
    const checkAuth = async () => {
      let currentUser = AuthService.getCurrentUser();
      if (!currentUser) {
        // Auto-login as Analyst for demo purposes
        try {
          const data = await AuthService.getDemoToken("ANALYST");
          currentUser = data.user;
          toast.success("Auto-logged in as Demo Analyst");
        } catch (e) {
          console.error("Failed to auto-login", e);
        }
      }
      setUser(currentUser);
    };
    checkAuth();
  }, []);

  const switchRole = async (role: "ADMIN" | "ANALYST") => {
    try {
      const data = await AuthService.getDemoToken(role);
      setUser(data.user);
      setIsDropdownOpen(false);
      toast.success(`Switched to ${role} role`);
      // Reload to fetch data with new role permissions if needed
      window.location.reload();
    } catch (e) {
      toast.error(`Failed to switch to ${role}`);
    }
  };

  if (!user) {
    return <div className="centered">Loading...</div>;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div>
            <h2 className="brand-title">Breathe ESG</h2>
            <p className="brand-subtitle">Enterprise climate ledger</p>
          </div>
        </div>

        <nav className="nav">
          <div className="nav-section">
            <p className="nav-label">Core</p>
            <NavLink
              to="/"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              <LayoutDashboard size={20} />
              Dashboard
            </NavLink>

            <NavLink
              to="/upload"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              <UploadCloud size={20} />
              Data Ingestion
            </NavLink>

            {user?.role === "ADMIN" && (
              <NavLink
                to="/records"
                className={({ isActive }) =>
                  isActive ? "nav-link active" : "nav-link"
                }
              >
                <Database size={20} />
                Review Records
              </NavLink>
            )}
          </div>
        </nav>
        <div className="sidebar-footer">
          <div className="status-pill">Operational · Live ingestion</div>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">Enterprise ESG Pulse</span>
            <span className="topbar-meta">
              Last sync: moments ago · Review queue ready
            </span>
          </div>
          <div className="topbar-actions">
            <NavLink to="/upload" className="button button-primary">
              Ingest data
            </NavLink>
            <div style={{ position: "relative" }}>
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="role-button"
              >
                Viewing as:{" "}
                <span
                  style={{ fontWeight: 600, color: "var(--accent-primary)" }}
                >
                  {user.role}
                </span>
                <ChevronDown size={16} />
              </button>

              {isDropdownOpen && (
                <div className="dropdown">
                  <button
                    onClick={() => switchRole("ANALYST")}
                    className="dropdown-item"
                  >
                    Switch to Analyst
                  </button>
                  <button
                    onClick={() => switchRole("ADMIN")}
                    className="dropdown-item"
                  >
                    Switch to Admin
                  </button>
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
};

export default Layout;
