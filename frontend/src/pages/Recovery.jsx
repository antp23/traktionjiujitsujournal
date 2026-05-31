import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getOuraStatus, getOuraData, syncOura, getSessions } from "../api";
import { Activity, Heart, Moon, Zap, RefreshCw, Wifi, WifiOff } from "lucide-react";

function ScoreBadge({ value, label, color }) {
  if (value == null) return (
    <div className="flex flex-col items-center">
      <span className="text-2xl font-bold text-gray-300">--</span>
      <span className="text-xs text-gray-400 mt-0.5">{label}</span>
    </div>
  );
  const pct = Math.min(100, value);
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-14 h-14">
        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="22" fill="none" stroke="#e4e8f0" strokeWidth="5" />
          <circle cx="28" cy="28" r="22" fill="none" stroke={color} strokeWidth="5"
            strokeDasharray={`${(pct / 100) * 138.2} 138.2`} strokeLinecap="round" />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-800">{value}</span>
      </div>
      <span className="text-xs text-gray-500 mt-1">{label}</span>
    </div>
  );
}

function MetricPill({ icon: Icon, value, label, iconColor = "text-purple-500" }) {
  return (
    <div className="flex items-center gap-2 bg-gray-50 border border-gray-100 rounded-xl px-3 py-2.5">
      <Icon className={`w-4 h-4 flex-shrink-0 ${iconColor}`} />
      <div>
        <div className="text-sm font-semibold text-gray-800">{value != null ? value : "--"}</div>
        <div className="text-xs text-gray-400">{label}</div>
      </div>
    </div>
  );
}

function ReadinessBar({ score }) {
  if (score == null) return null;
  const color = score >= 70 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
  const label = score >= 70 ? "Good to train" : score >= 50 ? "Train light" : "Rest day";
  const textColor = score >= 70 ? "text-emerald-600" : score >= 50 ? "text-amber-600" : "text-red-500";
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-400 mb-1.5">
        <span>Readiness</span>
        <span className={`font-medium ${textColor}`}>{label}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

export default function Recovery() {
  const [status, setStatus] = useState(null);
  const [ouraData, setOuraData] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, d, sess] = await Promise.all([
        getOuraStatus(),
        getOuraData(60),
        getSessions({ limit: 50 }),
      ]);
      setStatus(s.data);
      setOuraData(d.data);
      setSessions(Array.isArray(sess.data) ? sess.data : []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleSync() {
    setSyncing(true);
    try {
      await syncOura(60);
      const d = await getOuraData(60);
      setOuraData(d.data);
    } catch (e) { console.error(e); }
    setSyncing(false);
  }

  const today = ouraData[0] || null;
  const sessionDates = new Set(sessions.map(s => s.date));
  const timeline = ouraData.slice(0, 14);

  function fmtSleep(mins) {
    if (!mins) return "--";
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-gray-400 text-sm">Loading recovery data...</div>
    </div>
  );

  if (!status?.connected) return (
    <div className="max-w-md mx-auto mt-20 text-center">
      <WifiOff className="w-12 h-12 text-gray-300 mx-auto mb-4" />
      <h2 className="text-gray-800 font-semibold text-lg mb-2">Oura Not Connected</h2>
      <p className="text-gray-400 text-sm mb-6">Connect your Oura ring to see recovery data alongside your training.</p>
      <a href="http://localhost:8000/oura/auth"
        className="inline-block px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-xl transition-colors">
        Connect Oura Ring
      </a>
    </div>
  );

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Recovery</h1>
          <p className="text-sm text-gray-400 mt-0.5">Oura ring data + training correlation</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
            <Wifi className="w-3.5 h-3.5" />
            <span>Oura Connected</span>
          </div>
          <button onClick={handleSync} disabled={syncing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 text-xs rounded-lg transition-colors disabled:opacity-40">
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
            {syncing ? "Syncing..." : "Sync"}
          </button>
        </div>
      </div>

      {/* Today card */}
      {today && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1 mr-4">
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Today — {today.date}</div>
              <ReadinessBar score={today.readiness_score} />
            </div>
            {sessionDates.has(today.date) && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-purple-50 border border-purple-200 rounded-lg flex-shrink-0">
                <span className="text-xs text-purple-600 font-medium">🥋 Trained today</span>
              </div>
            )}
          </div>
          <div className="grid grid-cols-4 gap-3 mt-5">
            <ScoreBadge value={today.readiness_score} label="Readiness"
              color={today.readiness_score >= 70 ? "#10b981" : today.readiness_score >= 50 ? "#f59e0b" : "#ef4444"} />
            <ScoreBadge value={today.sleep_score} label="Sleep" color="#6366f1" />
            <ScoreBadge value={today.hrv_avg} label="HRV (ms)" color="#8b5cf6" />
            <ScoreBadge value={today.resting_hr} label="RHR (bpm)" color="#ec4899" />
          </div>
          <div className="grid grid-cols-2 gap-3 mt-4">
            <MetricPill icon={Moon} value={fmtSleep(today.total_sleep_minutes)} label="Sleep duration" iconColor="text-indigo-400" />
            <MetricPill icon={Activity} value={today.temperature_deviation ? `+${today.temperature_deviation}%` : "--"} label="Temp deviation" iconColor="text-orange-400" />
          </div>
        </motion.div>
      )}

      {/* 14-day timeline */}
      {timeline.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-4">14-Day Overview</h2>
          <div className="space-y-1">
            <div className="grid grid-cols-[90px_1fr_56px_56px_56px_56px] gap-2 text-xs text-gray-400 px-2 pb-2 border-b border-gray-100">
              <span>Date</span>
              <span>Readiness</span>
              <span className="text-center">Sleep</span>
              <span className="text-center">HRV</span>
              <span className="text-center">RHR</span>
              <span className="text-center">BJJ</span>
            </div>
            {timeline.map((row, i) => {
              const trained = sessionDates.has(row.date);
              const barColor = row.readiness_score >= 70 ? "#10b981" : row.readiness_score >= 50 ? "#f59e0b" : "#ef4444";
              const scoreColor = row.readiness_score >= 70 ? "text-emerald-600" : row.readiness_score >= 50 ? "text-amber-500" : "text-red-500";
              return (
                <motion.div key={row.date}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className={`grid grid-cols-[90px_1fr_56px_56px_56px_56px] gap-2 items-center px-2 py-2 rounded-xl ${trained ? "bg-purple-50" : "hover:bg-gray-50"}`}>
                  <span className="text-xs text-gray-500">{row.date.slice(5)}</span>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${row.readiness_score || 0}%`, background: barColor }} />
                    </div>
                    <span className={`text-xs font-semibold w-7 text-right ${scoreColor}`}>
                      {row.readiness_score ?? "--"}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500 text-center">{row.sleep_score ?? "--"}</span>
                  <span className="text-xs text-gray-500 text-center">{row.hrv_avg ? `${row.hrv_avg}` : "--"}</span>
                  <span className="text-xs text-gray-500 text-center">{row.resting_hr ?? "--"}</span>
                  <div className="flex justify-center">
                    {trained ? <span className="text-base">🥋</span> : <span className="text-gray-200 text-xs">—</span>}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Insights */}
      {ouraData.length >= 3 && (
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">Insights</h2>
          <div className="space-y-3">
            {(() => {
              const insights = [];
              const trainingDays = ouraData.filter(d => sessionDates.has(d.date) && d.readiness_score);
              const restDays = ouraData.filter(d => !sessionDates.has(d.date) && d.readiness_score);

              if (trainingDays.length > 0 && restDays.length > 0) {
                const avgT = Math.round(trainingDays.reduce((a, d) => a + d.readiness_score, 0) / trainingDays.length);
                const avgR = Math.round(restDays.reduce((a, d) => a + d.readiness_score, 0) / restDays.length);
                insights.push({
                  icon: Zap,
                  text: `Avg readiness on training days: ${avgT} — rest days: ${avgR}`,
                  color: "text-purple-500"
                });
              }

              const lowDays = ouraData.filter(d => (d.readiness_score || 100) < 50);
              if (lowDays.length > 0) {
                insights.push({
                  icon: Activity,
                  text: `${lowDays.length} day${lowDays.length > 1 ? "s" : ""} with readiness below 50 in the last 60 days`,
                  color: "text-red-500"
                });
              }

              const hrv = ouraData.filter(d => d.hrv_avg).map(d => d.hrv_avg);
              if (hrv.length >= 3) {
                const avgHrv = Math.round(hrv.reduce((a, b) => a + b, 0) / hrv.length);
                insights.push({
                  icon: Heart,
                  text: `Average HRV: ${avgHrv}ms over last ${hrv.length} nights`,
                  color: "text-pink-500"
                });
              }

              const sleepDays = ouraData.filter(d => d.total_sleep_minutes);
              if (sleepDays.length >= 3) {
                const avgSleep = Math.round(sleepDays.reduce((a, d) => a + d.total_sleep_minutes, 0) / sleepDays.length);
                insights.push({
                  icon: Moon,
                  text: `Average sleep: ${Math.floor(avgSleep / 60)}h ${avgSleep % 60}m per night`,
                  color: "text-indigo-500"
                });
              }

              return insights.map((ins, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <ins.icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${ins.color}`} />
                  <span className="text-sm text-gray-600">{ins.text}</span>
                </div>
              ));
            })()}
          </div>
        </div>
      )}

      {ouraData.length === 0 && (
        <div className="text-center py-12 text-gray-400 text-sm">
          No Oura data yet. Hit Sync to pull your data.
        </div>
      )}
    </div>
  );
}
