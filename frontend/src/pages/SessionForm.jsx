import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createSession, updateSession, getSession } from "../lib/api";
import LoadingSpinner from "../components/LoadingSpinner";

const TYPES = ["gi", "no-gi", "open_mat", "drilling", "competition_prep"];
const TYPE_LABELS = { gi: "Gi", "no-gi": "No-Gi", open_mat: "Open Mat", drilling: "Drilling", competition_prep: "Comp Prep" };
const FOCUS_SUGGESTIONS = ["Guard passing", "Guard play", "Back control", "Mount", "Leg locks", "Takedowns", "Side control", "Drilling", "Escapes"];

export default function SessionForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [partnerInput, setPartnerInput] = useState("");

  const [form, setForm] = useState({
    date: new Date().toISOString().split("T")[0],
    session_type: "gi",
    duration_minutes: 90,
    gym_location: "",
    instructor: "",
    focus_area: "",
    energy_level: null,
    partners: [],
    notes: "",
    rounds_rolled: "",
    attended: true,
  });

  useEffect(() => {
    if (isEdit) {
      getSession(id).then(r => {
        const s = r.data;
        setForm({
          date: s.date,
          session_type: s.session_type,
          duration_minutes: s.duration_minutes,
          gym_location: s.gym_location || "",
          instructor: s.instructor || "",
          focus_area: s.focus_area || "",
          energy_level: s.energy_level,
          partners: s.partners || [],
          notes: s.notes || "",
          rounds_rolled: s.rounds_rolled || "",
          attended: s.attended,
        });
      }).finally(() => setLoading(false));
    }
  }, [id, isEdit]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const addPartner = () => {
    if (partnerInput.trim()) {
      set("partners", [...form.partners, partnerInput.trim()]);
      setPartnerInput("");
    }
  };

  const removePartner = (i) => set("partners", form.partners.filter((_, idx) => idx !== i));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = { ...form, rounds_rolled: form.rounds_rolled ? parseInt(form.rounds_rolled) : null };
    try {
      if (isEdit) await updateSession(id, payload);
      else await createSession(payload);
      navigate("/sessions");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{isEdit ? "Edit Session" : "Log Session"}</h1>
      <form onSubmit={submit} className="space-y-5">

        {/* Date + Attended */}
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-xs text-gray-500 mb-1">Date</label>
            <input type="date" value={form.date} onChange={e => set("date", e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div className="flex items-end pb-0.5">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={form.attended} onChange={e => set("attended", e.target.checked)}
                className="w-4 h-4 rounded accent-purple-600" />
              <span className="text-sm text-gray-700">Attended</span>
            </label>
          </div>
        </div>

        {/* Session type */}
        <div>
          <label className="block text-xs text-gray-500 mb-2">Type</label>
          <div className="flex flex-wrap gap-2">
            {TYPES.map(t => (
              <button type="button" key={t} onClick={() => set("session_type", t)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${form.session_type === t ? "bg-purple-700 text-white" : "bg-gray-100 text-gray-700 hover:bg-slate-600"}`}>
                {TYPE_LABELS[t]}
              </button>
            ))}
          </div>
        </div>

        {/* Duration + Rounds */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Duration (min)</label>
            <input type="number" value={form.duration_minutes} onChange={e => set("duration_minutes", parseInt(e.target.value))}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Rounds Rolled</label>
            <input type="number" value={form.rounds_rolled} onChange={e => set("rounds_rolled", e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Optional" />
          </div>
        </div>

        {/* Gym + Instructor */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Gym / Location</label>
            <input type="text" value={form.gym_location} onChange={e => set("gym_location", e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Optional" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Instructor</label>
            <input type="text" value={form.instructor} onChange={e => set("instructor", e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Optional" />
          </div>
        </div>

        {/* Focus area */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Focus Area</label>
          <input type="text" value={form.focus_area} onChange={e => set("focus_area", e.target.value)}
            list="focus-suggestions" className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="e.g. Guard passing" />
          <datalist id="focus-suggestions">
            {FOCUS_SUGGESTIONS.map(f => <option key={f} value={f} />)}
          </datalist>
        </div>

        {/* Energy level */}
        <div>
          <label className="block text-xs text-gray-500 mb-2">Energy Level</label>
          <div className="flex gap-2">
            {[1,2,3,4,5].map(n => (
              <button type="button" key={n} onClick={() => set("energy_level", form.energy_level === n ? null : n)}
                className={`w-9 h-9 rounded-lg text-sm font-bold transition-colors ${form.energy_level >= n ? "bg-purple-700 text-white" : "bg-gray-100 text-gray-500"}`}>
                {n}
              </button>
            ))}
          </div>
        </div>

        {/* Partners */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Training Partners</label>
          <div className="flex gap-2">
            <input type="text" value={partnerInput} onChange={e => setPartnerInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addPartner())}
              className="flex-1 bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Name + Enter to add" />
            <button type="button" onClick={addPartner} className="bg-gray-100 hover:bg-slate-600 text-white px-3 py-2 rounded-lg text-sm">Add</button>
          </div>
          {form.partners.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {form.partners.map((p, i) => (
                <span key={i} className="flex items-center gap-1 bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">
                  {p}
                  <button type="button" onClick={() => removePartner(i)} className="text-gray-500 hover:text-white">x</button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Notes */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Notes</label>
          <textarea value={form.notes} onChange={e => set("notes", e.target.value)} rows={5}
            className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm resize-none"
            placeholder="What happened? What clicked? What do you need to work on?" />
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={saving}
            className="bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors">
            {saving ? "Saving..." : isEdit ? "Update Session" : "Save Session"}
          </button>
          <button type="button" onClick={() => navigate("/sessions")}
            className="text-gray-500 hover:text-white px-4 py-2 text-sm transition-colors">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
