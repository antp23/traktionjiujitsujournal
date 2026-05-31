import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { getTechnique, deleteTechnique, updateTechnique } from "../api";
import LoadingSpinner from "../components/LoadingSpinner";
import Badge from "../components/Badge";
import ConfirmModal from "../components/ConfirmModal";
import { Edit, Trash2, ChevronDown, ChevronRight, ExternalLink, CheckCircle, Target } from "lucide-react";
import { format, parseISO } from "date-fns";

function Section({ title, items, text }) {
  const [open, setOpen] = useState(true);
  const hasContent = (items && items.length > 0) || Boolean(text);
  if (!hasContent) return null;
  return (
    <div className="border-b border-gray-100 pb-3 last:border-0 last:pb-0">
      <button onClick={() => setOpen(!open)} className="flex items-center gap-2 w-full text-left py-1 group">
        {open
          ? <ChevronDown className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-700 transition-colors" />
          : <ChevronRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-700 transition-colors" />}
        <span className="text-gray-700 font-medium text-sm">{title}</span>
      </button>
      {open && (
        <div className="mt-2 pl-5">
          {items ? (
            <ul className="space-y-1.5">
              {items.map((item, i) => (
                <li key={i} className="text-gray-500 text-sm flex gap-2">
                  <span className="text-gray-500 mt-0.5 flex-shrink-0">--</span>
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 text-sm whitespace-pre-wrap leading-relaxed">{text}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function TechniqueDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [technique, setTechnique] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [marking, setMarking] = useState(null);

  useEffect(() => {
    getTechnique(id).then(r => setTechnique(r.data)).finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    await deleteTechnique(id);
    navigate("/techniques");
  };

  const markDrilled = async () => {
    setMarking("drilled");
    const today = new Date().toISOString().split("T")[0];
    const updated = await updateTechnique(id, { last_drilled: today });
    setTechnique(updated.data);
    setMarking(null);
  };

  const markHit = async () => {
    setMarking("hit");
    const today = new Date().toISOString().split("T")[0];
    const updated = await updateTechnique(id, { last_hit_in_roll: today });
    setTechnique(updated.data);
    setMarking(null);
  };

  if (loading) return <LoadingSpinner />;
  if (!technique) return <p className="text-gray-500">Technique not found.</p>;

  const t = technique;
  const today = new Date().toISOString().split("T")[0];
  const drilledToday = t.last_drilled === today;
  const hitToday = t.last_hit_in_roll === today;

  return (
    <div className="max-w-2xl space-y-5">
      <ConfirmModal isOpen={showConfirm} title="Delete Technique"
        message="Permanently delete this technique?"
        onConfirm={handleDelete} onCancel={() => setShowConfirm(false)} />

      {/* Header card */}
      <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex flex-wrap gap-1.5">
            <Badge label={t.category} />
            <Badge label={t.gi_nogi} variant={t.gi_nogi === "gi" ? "gi" : t.gi_nogi === "no-gi" ? "nogi" : "default"} />
            <Badge label={t.proficiency} variant={t.proficiency} />
            {t.direction && <Badge label={t.direction} />}
          </div>
          <div className="flex gap-1.5 ml-3">
            <Link to={`/techniques/${id}/edit`} className="p-2 text-gray-500 hover:text-white bg-gray-100 rounded-lg transition-colors">
              <Edit className="w-4 h-4" />
            </Link>
            <button onClick={() => setShowConfirm(true)} className="p-2 text-gray-500 hover:text-red-400 bg-gray-100 rounded-lg transition-colors">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-0.5">{t.name}</h1>
        {t.position && <p className="text-gray-500 text-sm">from {t.position}</p>}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={markDrilled}
          disabled={marking === "drilled"}
          className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
            drilledToday
              ? "bg-green-50 border border-green-200 text-green-700"
              : "bg-gray-50/60 border border-gray-100 text-gray-700 hover:border-purple-500/40 hover:text-white"
          }`}
        >
          <CheckCircle className={`w-4 h-4 ${drilledToday ? "text-green-400" : "text-gray-400"}`} />
          {drilledToday ? "Drilled today" : "Mark drilled"}
          {t.last_drilled && !drilledToday && (
            <span className="text-gray-500 text-xs ml-1">({format(parseISO(t.last_drilled), "MMM d")})</span>
          )}
        </button>
        <button
          onClick={markHit}
          disabled={marking === "hit"}
          className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
            hitToday
              ? "bg-purple-50 border border-purple-200 text-purple-700"
              : "bg-gray-50/60 border border-gray-100 text-gray-700 hover:border-purple-500/40 hover:text-white"
          }`}
        >
          <Target className={`w-4 h-4 ${hitToday ? "text-purple-400" : "text-gray-400"}`} />
          {hitToday ? "Hit in roll today" : "Hit in roll"}
          {t.last_hit_in_roll && !hitToday && (
            <span className="text-gray-500 text-xs ml-1">({format(parseISO(t.last_hit_in_roll), "MMM d")})</span>
          )}
        </button>
      </div>

      {/* Content sections */}
      <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-4 space-y-3">
        <Section title="Description" text={t.description} />
        <Section title="Key Details" items={t.key_details} />
        <Section title="Common Mistakes" items={t.common_mistakes} />
        <Section title="Counters" items={t.counters} />
        <Section title="Counters to Counters" items={t.counters_to_counters} />
        {t.notes && <Section title="Notes" text={t.notes} />}
      </div>

      {/* Videos */}
      {t.video_urls?.length > 0 && (
        <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-4">
          <h3 className="text-gray-500 text-xs uppercase tracking-wide mb-3">Video References</h3>
          {t.video_urls.map((url, i) => (
            <a key={i} href={url} target="_blank" rel="noreferrer"
              className="flex items-center gap-2 text-purple-600 hover:text-purple-700 text-sm mb-1.5 transition-colors">
              <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="truncate">{url}</span>
            </a>
          ))}
        </div>
      )}

      {/* Tags + meta footer */}
      <div className="flex flex-wrap items-center gap-3 pt-1">
        {t.tags?.map(tag => (
          <span key={tag} className="text-xs text-gray-400 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-200">#{tag}</span>
        ))}
        {t.source && <span className="text-xs text-gray-400">Source: {t.source}</span>}
        <span className="text-xs text-gray-500 ml-auto">
          Added {t.date_added ? format(parseISO(t.date_added), "MMM d, yyyy") : "--"}
        </span>
      </div>
    </div>
  );
}
