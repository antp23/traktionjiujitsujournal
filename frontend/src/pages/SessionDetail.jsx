import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { getSession, deleteSession, getRolls, createRoll } from "../lib/api";
import LoadingSpinner from "../components/LoadingSpinner";
import Badge from "../components/Badge";
import ConfirmModal from "../components/ConfirmModal";
import { format, parseISO } from "date-fns";
import { Edit, Trash2, Plus, Clock, MapPin, User, Zap, RotateCcw } from "lucide-react";

const TYPE_LABEL = { gi: "Gi", "no-gi": "No-Gi", open_mat: "Open Mat", drilling: "Drilling", competition_prep: "Comp Prep" };
const OUTCOME_BADGE = { submission_win: "win", points_win: "win", submission_loss: "loss", points_loss: "loss", draw: "draw" };
const OUTCOME_LABEL = { submission_win: "Sub Win", points_win: "Points Win", submission_loss: "Sub Loss", points_loss: "Points Loss", draw: "Draw" };
const ENERGY_LABELS = ['', 'Low', 'Below Avg', 'Average', 'Good', 'Peak'];
const ENERGY_COLORS = ['', 'text-red-400', 'text-orange-400', 'text-yellow-400', 'text-lime-400', 'text-green-400'];

export default function SessionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [rolls, setRolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [showRollForm, setShowRollForm] = useState(false);
  const [rollForm, setRollForm] = useState({
    partner: "", duration_minutes: "", gi_nogi: "gi", outcome: "draw",
    submission_scored: "", submission_received: "", notes: ""
  });

  useEffect(() => {
    Promise.all([getSession(id), getRolls({ session_id: id })])
      .then(([s, r]) => { setSession(s.data); setRolls(r.data || []); })
      .finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    await deleteSession(id);
    navigate("/sessions");
  };

  const submitRoll = async (e) => {
    e.preventDefault();
    const payload = {
      ...rollForm,
      session_id: id,
      duration_minutes: rollForm.duration_minutes ? parseInt(rollForm.duration_minutes) : null
    };
    const r = await createRoll(payload);
    setRolls(prev => [...prev, r.data]);
    setShowRollForm(false);
    setRollForm({ partner: "", duration_minutes: "", gi_nogi: "gi", outcome: "draw", submission_scored: "", submission_received: "", notes: "" });
  };

  const rf = (k, v) => setRollForm(f => ({ ...f, [k]: v }));

  if (loading) return <LoadingSpinner />;
  if (!session) return <p className="text-gray-500">Session not found.</p>;

  const wins = rolls.filter(r => r.outcome?.includes('win')).length;
  const losses = rolls.filter(r => r.outcome?.includes('loss')).length;

  return (
    <div className="max-w-2xl space-y-5">
      <ConfirmModal isOpen={showConfirm} title="Delete Session"
        message="Permanently delete this session and all its rolls?"
        onConfirm={handleDelete} onCancel={() => setShowConfirm(false)} />

      {/* Header */}
      <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex gap-2">
            <Badge label={TYPE_LABEL[session.session_type] || session.session_type} variant={session.session_type} />
            {!session.attended && <Badge label="Missed" variant="loss" />}
          </div>
          <div className="flex gap-1.5">
            <Link to={`/sessions/${id}/edit`} className="p-2 text-gray-500 hover:text-white bg-gray-100 rounded-lg transition-colors">
              <Edit className="w-4 h-4" />
            </Link>
            <button onClick={() => setShowConfirm(true)} className="p-2 text-gray-500 hover:text-red-400 bg-gray-100 rounded-lg transition-colors">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <h1 className="text-xl font-bold text-gray-900 mb-1">{session.focus_area || "Training Session"}</h1>
        <p className="text-gray-500 text-sm mb-4">
          {format(parseISO(session.date), "EEEE, MMMM d yyyy")}
        </p>

        {/* Detail grid */}
        <div className="grid grid-cols-2 gap-x-6 gap-y-2.5">
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-gray-500">Duration</span>
            <span className="text-gray-800 ml-auto">{session.duration_minutes}min</span>
          </div>
          {session.energy_level && (
            <div className="flex items-center gap-2 text-sm">
              <Zap className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-500">Energy</span>
              <span className={`ml-auto font-medium ${ENERGY_COLORS[session.energy_level]}`}>
                {ENERGY_LABELS[session.energy_level]}
              </span>
            </div>
          )}
          {session.instructor && (
            <div className="flex items-center gap-2 text-sm">
              <User className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-500">Instructor</span>
              <span className="text-gray-800 ml-auto">{session.instructor}</span>
            </div>
          )}
          {session.gym_location && (
            <div className="flex items-center gap-2 text-sm">
              <MapPin className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-500">Location</span>
              <span className="text-gray-800 ml-auto">{session.gym_location}</span>
            </div>
          )}
          {session.rounds_rolled && (
            <div className="flex items-center gap-2 text-sm">
              <RotateCcw className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-500">Rounds</span>
              <span className="text-gray-800 ml-auto">{session.rounds_rolled}</span>
            </div>
          )}
        </div>

        {session.partners?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-gray-100">
            {session.partners.map(p => (
              <span key={p} className="text-xs bg-gray-100 text-gray-700 px-2.5 py-1 rounded-full">{p}</span>
            ))}
          </div>
        )}
      </div>

      {/* Notes */}
      {session.notes && (
        <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-4">
          <h2 className="text-gray-500 text-xs uppercase tracking-wide mb-2">Session Notes</h2>
          <p className="text-gray-800 text-sm whitespace-pre-wrap leading-relaxed">{session.notes}</p>
        </div>
      )}

      {/* Rolls section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <h2 className="text-gray-800 font-semibold">Rolls</h2>
            {rolls.length > 0 && (
              <div className="flex gap-2 text-xs">
                <span className="text-green-400">{wins}W</span>
                <span className="text-gray-400">/</span>
                <span className="text-red-400">{losses}L</span>
                <span className="text-gray-400">/</span>
                <span className="text-gray-500">{rolls.length - wins - losses}D</span>
              </div>
            )}
          </div>
          <button
            onClick={() => setShowRollForm(!showRollForm)}
            className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-colors ${
              showRollForm ? 'bg-gray-100 text-gray-700' : 'bg-purple-600 hover:bg-purple-500 text-white'
            }`}
          >
            <Plus className="w-3.5 h-3.5" />
            {showRollForm ? "Cancel" : "Add Roll"}
          </button>
        </div>

        {/* Roll form */}
        {showRollForm && (
          <form onSubmit={submitRoll} className="bg-gray-50/60 border border-purple-700/30 rounded-xl p-4 mb-3 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Partner *</label>
                <input required value={rollForm.partner} onChange={e => rf("partner", e.target.value)}
                  className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Duration (min)</label>
                <input type="number" value={rollForm.duration_minutes} onChange={e => rf("duration_minutes", e.target.value)}
                  className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500" placeholder="Optional" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Format</label>
                <select value={rollForm.gi_nogi} onChange={e => rf("gi_nogi", e.target.value)}
                  className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500">
                  <option value="gi">Gi</option>
                  <option value="no-gi">No-Gi</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Outcome</label>
                <select value={rollForm.outcome} onChange={e => rf("outcome", e.target.value)}
                  className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500">
                  <option value="submission_win">Sub Win</option>
                  <option value="submission_loss">Sub Loss</option>
                  <option value="points_win">Points Win</option>
                  <option value="points_loss">Points Loss</option>
                  <option value="draw">Draw</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Sub Scored</label>
                <input value={rollForm.submission_scored} onChange={e => rf("submission_scored", e.target.value)}
                  className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500" placeholder="Optional" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Sub Received</label>
                <input value={rollForm.submission_received} onChange={e => rf("submission_received", e.target.value)}
                  className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500" placeholder="Optional" />
              </div>
            </div>
            <textarea value={rollForm.notes} onChange={e => rf("notes", e.target.value)}
              placeholder="Notes..." rows={2}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:border-purple-500" />
            <button type="submit" className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              Save Roll
            </button>
          </form>
        )}

        {rolls.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-6">No rolls logged for this session.</p>
        ) : (
          <div className="space-y-2">
            {rolls.map(r => (
              <div key={r.roll_id} className="bg-gray-50/60 border border-gray-100 rounded-xl p-3.5 flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                    r.outcome?.includes('win') ? 'bg-green-500' : r.outcome === 'draw' ? 'bg-slate-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-gray-900 text-sm font-medium">{r.partner}</span>
                      <Badge label={OUTCOME_LABEL[r.outcome]} variant={OUTCOME_BADGE[r.outcome]} />
                      <Badge label={r.gi_nogi} variant={r.gi_nogi === "gi" ? "gi" : "nogi"} />
                    </div>
                    {r.submission_scored && <p className="text-xs text-green-400">Scored: {r.submission_scored}</p>}
                    {r.submission_received && <p className="text-xs text-red-400">Caught: {r.submission_received}</p>}
                    {r.notes && <p className="text-xs text-gray-400 mt-1">{r.notes}</p>}
                  </div>
                </div>
                {r.duration_minutes && <span className="text-gray-400 text-xs flex-shrink-0">{r.duration_minutes}min</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
