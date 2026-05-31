import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { getCurrentRank } from "../api";
import { useAuth } from "../auth";
import {
  BookOpen,
  Building2,
  Calendar,
  HeartPulse,
  Inbox,
  LayoutDashboard,
  LogOut,
  Menu,
  Swords,
  StickyNote,
  Target,
  TrendingUp,
  X,
} from "lucide-react";

const nav = [
  { to: "/", label: "Brief", icon: LayoutDashboard },
  { to: "/sessions", label: "Sessions", icon: Calendar },
  { to: "/techniques", label: "Techniques", icon: BookOpen },
  { to: "/rolls", label: "Rolls", icon: Swords },
  { to: "/progress", label: "Progress", icon: TrendingUp },
  { to: "/team", label: "Team", icon: Building2 },
  { to: "/goals", label: "Goals", icon: Target },
  { to: "/notes", label: "Notes", icon: StickyNote },
  { to: "/inbox", label: "Coach Inbox", icon: Inbox },
  { to: "/recovery", label: "Recovery", icon: HeartPulse },
];

function BeltMark({ rank }) {
  if (!rank) return <div className="belt-mark belt-purple" />;

  return (
    <div className={`belt-mark belt-${rank.belt || "purple"}`} aria-label={`${rank.belt} belt`}>
      <span />
      <div>
        {Array.from({ length: 4 }).map((_, index) => (
          <i key={index} className={index < (rank.stripes || 0) ? "earned" : ""} />
        ))}
      </div>
    </div>
  );
}

function Sidebar({ closeMenu, onSignOut, rank, user }) {
  return (
    <aside className="app-sidebar">
      <div className="sidebar-brand">
        <div>
          <p className="brand-kicker">Mat Journal</p>
          <h1>BJJ Tracker</h1>
        </div>
        <BeltMark rank={rank} />
      </div>

      <nav className="sidebar-nav" aria-label="Primary navigation">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/"} onClick={closeMenu} className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}>
            <Icon className="sidebar-icon" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {user?.email && <p className="sidebar-email">{user.email}</p>}
        <p className="sidebar-note">Private journal. Shared by choice.</p>
        <button type="button" onClick={onSignOut} className="sidebar-signout">
          <LogOut className="w-4 h-4" /> Sign out
        </button>
      </div>
    </aside>
  );
}

export default function Layout({ children }) {
  const [rank, setRank] = useState(null);
  const [open, setOpen] = useState(false);
  const { signOut, user } = useAuth();

  useEffect(() => {
    getCurrentRank().then((response) => setRank(response.data)).catch(() => {});
  }, []);

  return (
    <div className="app-shell">
      <div className="desktop-sidebar">
        <Sidebar rank={rank} closeMenu={() => setOpen(false)} onSignOut={signOut} user={user} />
      </div>

      {open && (
        <div className="mobile-sidebar">
          <Sidebar rank={rank} closeMenu={() => setOpen(false)} onSignOut={signOut} user={user} />
          <button type="button" className="mobile-scrim" onClick={() => setOpen(false)} aria-label="Close menu" />
        </div>
      )}

      <div className="app-main">
        <header className="mobile-topbar">
          <button type="button" onClick={() => setOpen((value) => !value)} className="mobile-menu-button" aria-label="Open menu">
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <span>BJJ Tracker</span>
        </header>
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
