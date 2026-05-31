export default function Badge({ label, variant = "default", className = "" }) {
  const variants = {
    default:          "bg-gray-100 text-gray-600 border border-gray-200",
    gi:               "bg-blue-50 text-blue-700 border border-blue-200",
    nogi:             "bg-orange-50 text-orange-700 border border-orange-200",
    "no-gi":          "bg-orange-50 text-orange-700 border border-orange-200",
    both:             "bg-gray-100 text-gray-600 border border-gray-200",
    learning:         "bg-gray-100 text-gray-500 border border-gray-200",
    drilling:         "bg-blue-50 text-blue-700 border border-blue-200",
    applying:         "bg-violet-50 text-violet-700 border border-violet-200",
    sharp:            "bg-emerald-50 text-emerald-700 border border-emerald-200",
    win:              "bg-emerald-50 text-emerald-700 border border-emerald-200",
    loss:             "bg-red-50 text-red-600 border border-red-200",
    draw:             "bg-gray-100 text-gray-500 border border-gray-200",
    purple:           "bg-purple-50 text-purple-700 border border-purple-200",
    open_mat:         "bg-cyan-50 text-cyan-700 border border-cyan-200",
    drilling_type:    "bg-amber-50 text-amber-700 border border-amber-200",
    competition_prep: "bg-rose-50 text-rose-700 border border-rose-200",
    offensive:        "bg-red-50 text-red-600 border border-red-200",
    defensive:        "bg-sky-50 text-sky-700 border border-sky-200",
    transition:       "bg-violet-50 text-violet-700 border border-violet-200",
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium tracking-wide ${variants[variant] || variants.default} ${className}`}>
      {label}
    </span>
  );
}
