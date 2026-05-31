import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Sessions from "./pages/Sessions";
import SessionForm from "./pages/SessionForm";
import SessionDetail from "./pages/SessionDetail";
import Techniques from "./pages/Techniques";
import TechniqueForm from "./pages/TechniqueForm";
import TechniqueDetail from "./pages/TechniqueDetail";
import Rolls from "./pages/Rolls";
import Progress from "./pages/Progress";
import Notes from "./pages/Notes";
import Recovery from "./pages/Recovery";
import Login from "./pages/Login";
import JoinWorkspace from "./pages/JoinWorkspace";
import Onboarding from "./pages/Onboarding";
import Goals from "./pages/Goals";
import SharedInbox from "./pages/SharedInbox";
import SetupWorkspace from "./pages/SetupWorkspace";
import TeamWorkspace from "./pages/TeamWorkspace";

function ProtectedApp() {
  const { isAuthenticated, loading, memberships, profile } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="p-8 text-sm text-gray-500">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  }

  if (!memberships.length && location.pathname !== "/join") {
    return <Navigate to="/join" replace />;
  }

  if (memberships.length && !profile && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/sessions" element={<Sessions />} />
        <Route path="/sessions/new" element={<SessionForm />} />
        <Route path="/sessions/:id" element={<SessionDetail />} />
        <Route path="/sessions/:id/edit" element={<SessionForm />} />
        <Route path="/techniques" element={<Techniques />} />
        <Route path="/techniques/new" element={<TechniqueForm />} />
        <Route path="/techniques/:id" element={<TechniqueDetail />} />
        <Route path="/techniques/:id/edit" element={<TechniqueForm />} />
        <Route path="/rolls" element={<Rolls />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/team" element={<TeamWorkspace />} />
        <Route path="/notes" element={<Notes />} />
        <Route path="/inbox" element={<SharedInbox />} />
        <Route path="/recovery" element={<Recovery />} />
        <Route path="/join" element={<JoinWorkspace />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/setup" element={<SetupWorkspace />} />
          <Route path="/join" element={<JoinWorkspace />} />
          <Route path="/join/:code" element={<JoinWorkspace />} />
          <Route path="/*" element={<ProtectedApp />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
