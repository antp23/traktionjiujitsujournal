import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { updateProfile } from "../api";
import { useAuth } from "../auth";

const BELTS = ["white", "blue", "purple", "brown", "black"];

function splitList(value) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

export default function Onboarding() {
  const navigate = useNavigate();
  const { user, refreshMe } = useAuth();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    name: user?.name || "",
    preferred_name: user?.preferred_name || "",
    whatsapp_phone: "",
    belt: "white",
    stripes: 0,
    years_training: "",
    typical_training_frequency: "",
    gi_nogi_preference: "both",
    competition_interest: "",
    current_focus: "",
    favorite_positions: "",
    problem_positions: "",
    injuries_or_limitations: "",
  });

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setBusy(true);

    const payload = {
      ...form,
      stripes: Number(form.stripes) || 0,
      years_training: form.years_training === "" ? null : Number(form.years_training),
      favorite_positions: splitList(form.favorite_positions),
      problem_positions: splitList(form.problem_positions),
    };

    try {
      await updateProfile(payload);
      await refreshMe();
      navigate("/", { replace: true });
    } catch {
      setError("Could not save profile details. Check the backend and try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-purple-700">Student profile</p>
        <h1 className="text-2xl font-bold text-gray-950 mt-1">Finish onboarding</h1>
        <p className="text-sm text-gray-500 mt-1">Set the training context that helps coaches understand shared goals and notes. Your journal history stays private unless you share a specific item.</p>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}

      <form onSubmit={submit} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Full name
            <input value={form.name} onChange={(event) => update("name", event.target.value)} className="w-full rounded-lg px-3 py-2 text-sm" required />
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Preferred name
            <input value={form.preferred_name} onChange={(event) => update("preferred_name", event.target.value)} className="w-full rounded-lg px-3 py-2 text-sm" />
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            WhatsApp phone <span className="text-gray-400 font-normal">(optional)</span>
            <input value={form.whatsapp_phone} onChange={(event) => update("whatsapp_phone", event.target.value)} placeholder="+15555555555" className="w-full rounded-lg px-3 py-2 text-sm" />
            <span className="block text-xs font-normal text-gray-500">For contact reference only. WhatsApp capture is not active.</span>
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Belt
            <select value={form.belt} onChange={(event) => update("belt", event.target.value)} className="w-full rounded-lg px-3 py-2 text-sm">
              {BELTS.map((belt) => <option key={belt} value={belt}>{belt}</option>)}
            </select>
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Stripes
            <input type="number" min="0" max="4" value={form.stripes} onChange={(event) => update("stripes", event.target.value)} className="w-full rounded-lg px-3 py-2 text-sm" />
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Years training
            <input type="number" min="0" step="0.5" value={form.years_training} onChange={(event) => update("years_training", event.target.value)} className="w-full rounded-lg px-3 py-2 text-sm" />
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Training frequency
            <input value={form.typical_training_frequency} onChange={(event) => update("typical_training_frequency", event.target.value)} placeholder="3x/week" className="w-full rounded-lg px-3 py-2 text-sm" />
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Gi/no-gi preference
            <select value={form.gi_nogi_preference} onChange={(event) => update("gi_nogi_preference", event.target.value)} className="w-full rounded-lg px-3 py-2 text-sm">
              <option value="both">Both</option>
              <option value="gi">Gi</option>
              <option value="no_gi">No-gi</option>
            </select>
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Competition interest
            <input value={form.competition_interest} onChange={(event) => update("competition_interest", event.target.value)} placeholder="yes, no, maybe" className="w-full rounded-lg px-3 py-2 text-sm" />
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Current focus
            <input value={form.current_focus} onChange={(event) => update("current_focus", event.target.value)} placeholder="guard retention" className="w-full rounded-lg px-3 py-2 text-sm" />
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Favorite positions
            <input value={form.favorite_positions} onChange={(event) => update("favorite_positions", event.target.value)} placeholder="De La Riva, front headlock" className="w-full rounded-lg px-3 py-2 text-sm" />
          </label>
          <label className="space-y-1 text-sm font-medium text-gray-700">
            Problem positions
            <input value={form.problem_positions} onChange={(event) => update("problem_positions", event.target.value)} placeholder="bottom half, mount escapes" className="w-full rounded-lg px-3 py-2 text-sm" />
          </label>
        </div>

        <label className="block space-y-1 text-sm font-medium text-gray-700">
          Injuries or limitations
          <textarea value={form.injuries_or_limitations} onChange={(event) => update("injuries_or_limitations", event.target.value)} rows={3} className="w-full rounded-lg px-3 py-2 text-sm resize-none" />
        </label>

        <button disabled={busy} className="bg-purple-700 hover:bg-purple-600 disabled:opacity-60 text-white text-sm font-medium rounded-lg px-4 py-2">
          Save profile
        </button>
      </form>
    </div>
  );
}
