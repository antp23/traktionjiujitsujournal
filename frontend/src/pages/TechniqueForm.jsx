import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createTechnique, updateTechnique, getTechnique } from "../api";
import LoadingSpinner from "../components/LoadingSpinner";
import { Plus, X } from "lucide-react";

const CATEGORIES = [
  "Takedowns & Trips", "Guard Passing", "Guard Play", "Back Control & Attacks",
  "Mount & Attacks", "Side Control & Attacks", "Knee on Belly", "Turtle Position",
  "Leg Locks", "Arm Locks", "Chokes & Strangles", "Escapes & Reversals",
  "Transitions", "Competition-Specific", "Conditioning & Concepts"
];

function DynamicList({ label, items, onChange }) {
  const [input, setInput] = useState("");
  const add = () => { if (input.trim()) { onChange([...items, input.trim()]); setInput(""); } };
  const remove = (i) => onChange(items.filter((_, idx) => idx !== i));
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <div className="flex gap-2 mb-1.5">
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && (e.preventDefault(), add())}
          className="flex-1 bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-1.5 text-sm" placeholder="Add item..." />
        <button type="button" onClick={add} className="bg-gray-100 hover:bg-slate-600 text-white px-2 py-1.5 rounded-lg">
          <Plus className="w-4 h-4" />
        </button>
      </div>
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-2 bg-gray-50/60 rounded px-2 py-1 mb-1 text-sm text-gray-700">
          <span className="flex-1">{item}</span>
          <button type="button" onClick={() => remove(i)} className="text-gray-400 hover:text-red-400"><X className="w-3 h-3" /></button>
        </div>
      ))}
    </div>
  );
}

export default function TechniqueForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [tagInput, setTagInput] = useState("");

  const [form, setForm] = useState({
    name: "", category: CATEGORIES[0], position: "", direction: "offensive",
    gi_nogi: "both", description: "", key_details: [], common_mistakes: [],
    counters: [], counters_to_counters: [], video_urls: [], proficiency: "learning",
    last_drilled: "", last_hit_in_roll: "", notes: "", source: "", tags: [],
  });

  useEffect(() => {
    if (isEdit) {
      getTechnique(id).then(r => {
        const t = r.data;
        setForm({ ...t, last_drilled: t.last_drilled || "", last_hit_in_roll: t.last_hit_in_roll || "" });
      }).finally(() => setLoading(false));
    }
  }, [id, isEdit]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const addTag = () => { if (tagInput.trim() && !form.tags.includes(tagInput.trim())) { set("tags", [...form.tags, tagInput.trim()]); setTagInput(""); } };
  const removeTag = (t) => set("tags", form.tags.filter(x => x !== t));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = { ...form, last_drilled: form.last_drilled || null, last_hit_in_roll: form.last_hit_in_roll || null };
    try {
      if (isEdit) await updateTechnique(id, payload);
      else await createTechnique(payload);
      navigate("/techniques");
    } finally { setSaving(false); }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{isEdit ? "Edit Technique" : "Add Technique"}</h1>
      <form onSubmit={submit} className="space-y-5">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Name *</label>
          <input required value={form.name} onChange={e => set("name", e.target.value)}
            className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="e.g. Rear Naked Choke" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Category *</label>
            <select required value={form.category} onChange={e => set("category", e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm">
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Position</label>
            <input value={form.position} onChange={e => set("position", e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Starting position" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-2">Direction</label>
            <div className="flex gap-1">
              {["offensive", "defensive", "transition"].map(d => (
                <button type="button" key={d} onClick={() => set("direction", d)}
                  className={`px-2 py-1 rounded text-xs capitalize ${form.direction === d ? "bg-purple-700 text-white" : "bg-gray-100 text-gray-700"}`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-2">Gi / No-Gi</label>
            <div className="flex gap-1">
              {["gi", "no-gi", "both"].map(g => (
                <button type="button" key={g} onClick={() => set("gi_nogi", g)}
                  className={`px-2 py-1 rounded text-xs capitalize ${form.gi_nogi === g ? "bg-purple-700 text-white" : "bg-gray-100 text-gray-700"}`}>
                  {g}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-2">Proficiency</label>
          <div className="flex gap-2">
            {["learning", "drilling", "applying", "sharp"].map(p => (
              <button type="button" key={p} onClick={() => set("proficiency", p)}
                className={`px-3 py-1.5 rounded-lg text-xs capitalize ${form.proficiency === p ? "bg-purple-700 text-white" : "bg-gray-100 text-gray-700"}`}>
                {p}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Description</label>
          <textarea value={form.description} onChange={e => set("description", e.target.value)} rows={4}
            className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm resize-none"
            placeholder="Step-by-step breakdown..." />
        </div>

        <DynamicList label="Key Details" items={form.key_details} onChange={v => set("key_details", v)} />
        <DynamicList label="Common Mistakes" items={form.common_mistakes} onChange={v => set("common_mistakes", v)} />
        <DynamicList label="Counters" items={form.counters} onChange={v => set("counters", v)} />
        <DynamicList label="Counters to Counters" items={form.counters_to_counters} onChange={v => set("counters_to_counters", v)} />
        <DynamicList label="Video URLs" items={form.video_urls} onChange={v => set("video_urls", v)} />

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Last Drilled</label>
            <input type="date" value={form.last_drilled} onChange={e => set("last_drilled", e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Last Hit in Roll</label>
            <input type="date" value={form.last_hit_in_roll} onChange={e => set("last_hit_in_roll", e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Source</label>
          <input value={form.source} onChange={e => set("source", e.target.value)}
            className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm"
            placeholder="Seminar, YouTube, class, etc." />
        </div>

        {/* Tags */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Tags</label>
          <div className="flex gap-2 mb-1.5">
            <input value={tagInput} onChange={e => setTagInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addTag())}
              className="flex-1 bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-1.5 text-sm" placeholder="Add tag..." />
            <button type="button" onClick={addTag} className="bg-gray-100 text-white px-2 py-1.5 rounded-lg"><Plus className="w-4 h-4" /></button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {form.tags.map(t => (
              <span key={t} className="flex items-center gap-1 bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">
                #{t} <button type="button" onClick={() => removeTag(t)} className="text-gray-500 hover:text-white">x</button>
              </span>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Notes</label>
          <textarea value={form.notes} onChange={e => set("notes", e.target.value)} rows={3}
            className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm resize-none" />
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={saving}
            className="bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm font-medium">
            {saving ? "Saving..." : isEdit ? "Update" : "Add Technique"}
          </button>
          <button type="button" onClick={() => navigate("/techniques")} className="text-gray-500 hover:text-white px-4 py-2 text-sm">Cancel</button>
        </div>
      </form>
    </div>
  );
}
