import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { format, parseISO } from "date-fns";
import { ArrowRight, BookOpen, CalendarDays, MessageSquare, NotebookPen, Plus, Target } from "lucide-react";
import { getCurrentWorkspace, getDashboard } from "../api";
import Badge from "../components/Badge";
import ChatInput from "../components/ChatInput";
import LoadingSpinner from "../components/LoadingSpinner";

const SESSION_TYPE_LABELS = {
  gi: "Gi",
  no_gi: "No-Gi",
  "no-gi": "No-Gi",
  open_mat: "Open Mat",
  drilling: "Drilling",
  competition_prep: "Comp Prep",
};

function Stat({ label, value, detail }) {
  return (
    <div className="journal-stat">
      <p>{label}</p>
      <strong>{value}</strong>
      {detail && <span>{detail}</span>}
    </div>
  );
}

function deriveSignal(recentSessions = []) {
  const latest = recentSessions[0];
  if (!latest) return "Start by logging your next class. The brief gets sharper once there is a little mat history to read.";

  const focus = latest.focus_area || SESSION_TYPE_LABELS[latest.session_type] || "your last class";
  return `Latest signal: ${focus}. Keep the next entry specific: what worked, what broke under fatigue, and what should repeat next class.`;
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const [membership, setMembership] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [dashboardResponse, workspaceResponse] = await Promise.all([
        getDashboard(),
        getCurrentWorkspace().catch(() => ({ data: {} })),
      ]);
      setData(dashboardResponse.data);
      setWorkspace(workspaceResponse.data.workspace || null);
      setMembership(workspaceResponse.data.membership || null);
    } catch (error) {
      console.error(error);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  const handleLogged = useCallback(() => {
    setTimeout(() => getDashboard().then((response) => setData(response.data)), 400);
  }, []);

  const brief = useMemo(() => deriveSignal(data?.recent_sessions || []), [data]);

  if (loading) return <LoadingSpinner />;
  if (!data) return <p className="muted-copy">Could not load dashboard.</p>;

  const {
    current_rank,
    recent_sessions = [],
    session_stats: stats = {},
    spotlight,
    technique_counts = {},
    total_techniques = 0,
  } = data;
  const hasTrainingHistory = recent_sessions.length > 0 || total_techniques > 0 || (stats.total_sessions || 0) > 0;

  return (
    <div className="journal-page">
      <section className="journal-header">
        <div>
          <p className="eyebrow">{workspace?.gym_name || "Personal mat journal"}</p>
          <h1>Coach Brief</h1>
          <p className="lede">{brief}</p>
        </div>
        <button type="button" onClick={() => navigate("/team")} className="quiet-action">
          {workspace ? "Team workspace" : "Create workspace"} <ArrowRight className="w-4 h-4" />
        </button>
      </section>

      <section className="brief-grid">
        <div className="brief-panel primary">
          <div className="panel-heading">
            <NotebookPen className="w-4 h-4" />
            <span>Quick capture</span>
          </div>
          <ChatInput onLogged={handleLogged} />
        </div>

        <div className="brief-panel">
          <div className="panel-heading">
            <Target className="w-4 h-4" />
            <span>Current rank</span>
          </div>
          <div className="rank-card">
            <span className={`rank-line belt-${current_rank?.belt || "purple"}`} />
            <div>
              <strong>{current_rank?.belt || "purple"} belt</strong>
              <p>{current_rank?.stripes || 0} stripes</p>
            </div>
          </div>
          <button type="button" onClick={() => navigate("/progress")} className="text-action">Open progress</button>
        </div>

        <div className="brief-panel">
          <div className="panel-heading">
            <MessageSquare className="w-4 h-4" />
            <span>Coach channel</span>
          </div>
          <p className="body-copy">{membership?.role === "owner" ? "Review shared athlete goals and notes from the coach inbox." : "Share only the goals or notes you explicitly want your coach to see."}</p>
          <button type="button" onClick={() => navigate("/inbox")} className="text-action">Open inbox</button>
        </div>
      </section>

      {!hasTrainingHistory && (
        <section className="launch-callout">
          <div>
            <p className="eyebrow">First week setup</p>
            <h2>Start with one honest training entry.</h2>
            <p>
              Your dashboard becomes useful after a few sessions, techniques, and goals. Log privately first, then share only the items that need coach feedback.
            </p>
          </div>
          <div className="launch-actions">
            <button type="button" onClick={() => navigate("/sessions/new")} className="primary-action">
              <Plus className="w-4 h-4" /> Log session
            </button>
            <button type="button" onClick={() => navigate("/goals")} className="quiet-action">
              Add goal <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </section>
      )}

      <section className="journal-stats" aria-label="Training stats">
        <Stat label="This week" value={stats.sessions_this_week || 0} detail="sessions" />
        <Stat label="This month" value={stats.sessions_this_month || 0} detail="sessions" />
        <Stat label="All time" value={stats.total_sessions || 0} detail="sessions logged" />
        <Stat label="Streak" value={`${stats.current_streak || 0}w`} detail="training weeks" />
      </section>

      <section className="content-grid">
        <div className="journal-panel wide">
          <div className="section-title">
            <CalendarDays className="w-4 h-4" />
            <h2>Recent sessions</h2>
          </div>
          <div className="journal-list">
            {recent_sessions.length === 0 ? (
              <div className="panel-empty">
                <strong>No sessions logged yet</strong>
                <p>Capture date, class type, focus, and one useful lesson. Even a rough note is enough to build momentum.</p>
                <button type="button" onClick={() => navigate("/sessions/new")} className="text-action">Create first session</button>
              </div>
            ) : (
              recent_sessions.slice(0, 5).map((session) => (
                <button key={session.session_id} type="button" onClick={() => navigate(`/sessions/${session.session_id}`)} className="journal-row">
                  <span>{session.date ? format(parseISO(session.date), "MMM d") : "--"}</span>
                  <div>
                    <strong>{session.focus_area || SESSION_TYPE_LABELS[session.session_type] || "Session"}</strong>
                    <p>{session.duration_minutes} min · {SESSION_TYPE_LABELS[session.session_type] || session.session_type}</p>
                  </div>
                  <Badge label={SESSION_TYPE_LABELS[session.session_type] || session.session_type} variant={session.session_type} />
                </button>
              ))
            )}
          </div>
        </div>

        <div className="journal-panel">
          <div className="section-title">
            <BookOpen className="w-4 h-4" />
            <h2>Technique work</h2>
          </div>
          <div className="tech-count">
            <strong>{total_techniques}</strong>
            <span>logged techniques</span>
          </div>
          <div className="quiet-bars">
            {["learning", "drilling", "applying", "sharp"].map((key) => (
              <div key={key}>
                <span>{key}</span>
                <i style={{ width: `${total_techniques ? ((technique_counts[key] || 0) / total_techniques) * 100 : 0}%` }} />
                <em>{technique_counts[key] || 0}</em>
              </div>
            ))}
          </div>
          {spotlight && (
            <button type="button" onClick={() => navigate(`/techniques/${spotlight.technique_id}`)} className="spotlight-note">
              <span>Review today</span>
              <strong>{spotlight.name}</strong>
            </button>
          )}
          {!spotlight && total_techniques === 0 && (
            <div className="panel-empty compact">
              <strong>No techniques yet</strong>
              <p>Add one move you are learning, then update it as it moves from drilling to live rounds.</p>
              <button type="button" onClick={() => navigate("/techniques/new")} className="text-action">Add technique</button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
