export default function StatCard({ label, value, sub, icon: Icon, accent = false }) {
  return (
    <div className={`rounded-xl p-4 ${accent ? "bg-purple-900/30 border border-purple-700/40" : "bg-slate-800/60 border border-slate-700/40"}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
          <p className={`text-2xl font-bold mt-1 ${accent ? "text-purple-300" : "text-white"}`}>{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
        </div>
        {Icon && <Icon className={`w-5 h-5 ${accent ? "text-purple-400" : "text-slate-500"}`} />}
      </div>
    </div>
  );
}
