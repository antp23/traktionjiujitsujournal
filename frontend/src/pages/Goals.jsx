import { useCallback, useEffect, useState } from "react";
import { LockKeyhole, MessageSquare, Plus, Target } from "lucide-react";
import { createGoal, createShareThread, getGoals, updateGoal } from "../lib/api";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";

const STATUS_OPTIONS = ["active", "completed", "paused", "archived"];
const VISIBILITY_OPTIONS = ["private", "shared"];

function goalId(goal) {
  return goal.goal_id || goal.id;
}

export default function Goals() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sharingId, setSharingId] = useState(null);
  const [shareBody, setShareBody] = useState("Can you look at this?");
  const [form, setForm] = useState({
    title: "",
    description: "",
    status: "active",
    visibility: "private",
    target_date: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getGoals();
      setGoals(Array.isArray(response.data) ? response.data : response.data.goals || []);
    } catch {
      setError("Could not load goals.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    try {
      await createGoal({
        ...form,
        target_date: form.target_date || null,
      });
      setForm({ title: "", description: "", status: "active", visibility: "private", target_date: "" });
      load();
    } catch {
      setError("Could not create goal.");
    }
  };

  const changeStatus = async (goal, status) => {
    try {
      await updateGoal(goalId(goal), { ...goal, status });
      load();
    } catch {
      setError("Could not update goal.");
    }
  };

  const shareGoal = async (goal) => {
    setError("");
    try {
      await createShareThread({
        source_type: "goal",
        source_id: goalId(goal),
        body: shareBody.trim() || "Can you look at this?",
      });
      setSharingId(null);
      setShareBody("Can you look at this?");
      load();
    } catch {
      setError("Could not share this goal with coach.");
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-purple-700">Accountability</p>
        <h1 className="text-2xl font-bold text-gray-950 mt-1">Goals</h1>
        <p className="text-sm text-gray-500 mt-1">Goals are private unless you choose Shared or use Ask coach to open a coach thread.</p>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}

      <form onSubmit={submit} className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            placeholder="Goal title"
            className="rounded-lg px-3 py-2 text-sm"
            required
          />
          <input
            type="date"
            value={form.target_date}
            onChange={(event) => setForm((current) => ({ ...current, target_date: event.target.value }))}
            className="rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <textarea
          value={form.description}
          onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
          placeholder="What should change in your training?"
          rows={3}
          className="w-full rounded-lg px-3 py-2 text-sm resize-none"
        />
        <div className="flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between">
          <div className="flex gap-2">
            <select value={form.status} onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))} className="rounded-lg px-3 py-2 text-sm">
              {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
            <select value={form.visibility} onChange={(event) => setForm((current) => ({ ...current, visibility: event.target.value }))} className="rounded-lg px-3 py-2 text-sm">
              {VISIBILITY_OPTIONS.map((visibility) => (
                <option key={visibility} value={visibility}>
                  {visibility === "private" ? "private - only me" : "shared - coach visible"}
                </option>
              ))}
            </select>
          </div>
          <button className="inline-flex items-center justify-center gap-2 bg-purple-700 hover:bg-purple-600 text-white text-sm font-medium rounded-lg px-4 py-2">
            <Plus className="w-4 h-4" /> Add goal
          </button>
        </div>
      </form>

      <div className="privacy-note">
        <LockKeyhole className="w-4 h-4" />
        <span>Private means it stays in your journal. Ask coach creates a shared inbox thread with your message attached.</span>
      </div>

      {goals.length === 0 ? (
        <EmptyState
          message="No goals yet. Turn the next coaching cue into one measurable training target."
          icon={Target}
          action={<span className="text-xs text-gray-500">Example: improve knee shield retention before the next comp class.</span>}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {goals.map((goal) => (
            <article key={goalId(goal)} className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-gray-950">{goal.title}</h2>
                  {goal.description && <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">{goal.description}</p>}
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">{goal.visibility || "private"}</span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select value={goal.status || "active"} onChange={(event) => changeStatus(goal, event.target.value)} className="rounded-lg px-2 py-1.5 text-xs">
                  {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
                </select>
                {goal.target_date && <span className="text-xs text-gray-500">Target: {goal.target_date}</span>}
              </div>

              {sharingId === goalId(goal) ? (
                <div className="space-y-2 bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-xs text-gray-500">This sends the goal and your message to Coach Inbox.</p>
                  <textarea value={shareBody} onChange={(event) => setShareBody(event.target.value)} rows={2} className="w-full rounded-lg px-3 py-2 text-sm resize-none" />
                  <div className="flex gap-2">
                    <button type="button" onClick={() => shareGoal(goal)} className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-lg px-3 py-1.5">Send to coach</button>
                    <button onClick={() => setSharingId(null)} className="text-xs text-gray-500 px-2">Cancel</button>
                  </div>
                </div>
              ) : (
                <button onClick={() => setSharingId(goalId(goal))} className="inline-flex items-center gap-1.5 text-sm text-purple-700 hover:text-purple-600 font-medium">
                  <MessageSquare className="w-4 h-4" /> Ask coach
                </button>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
