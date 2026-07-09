import { useCallback, useState } from "react";
import { getRolls, getRollStats } from "../lib/api";
import { useAsyncData } from "../hooks/useAsyncData";
import Badge from "../components/Badge";
import LoadingSpinner from "../components/LoadingSpinner";
import { Swords, TrendingUp, Search } from "lucide-react";
import { motion } from "framer-motion";

const OUTCOME_BADGE = { submission_win: "win", points_win: "win", submission_loss: "loss", points_loss: "loss", draw: "draw" };
const OUTCOME_LABEL = { submission_win: "Sub Win", points_win: "Pts Win", submission_loss: "Sub Loss", points_loss: "Pts Loss", draw: "Draw" };

export default function Rolls() {
  const [partnerFilter, setPartnerFilter] = useState("");

  const loader = useCallback(async () => {
    const params = partnerFilter ? { partner: partnerFilter } : {};
    const [rollsResponse, statsResponse] = await Promise.all([getRolls(params), getRollStats()]);
    return { rolls: rollsResponse.data || [], stats: statsResponse.data || null };
  }, [partnerFilter]);
  const { data, loading, error } = useAsyncData(loader, { fallbackError: "Failed to load rolls" });

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="bg-red-900/20 border border-red-500/30 text-red-400 p-4 rounded-xl text-center">{error}</div>;

  const { rolls, stats } = data;
  const winRate = stats?.total_rolls > 0 ? Math.round((stats.wins / stats.total_rolls) * 100) : 0;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Roll Log</h1>

      {/* Stats */}
      {stats && stats.total_rolls > 0 && (
        <div className="space-y-3">
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-3 text-center">
              <p className="text-gray-900 font-bold text-xl">{stats.total_rolls}</p>
              <p className="text-gray-400 text-xs">Total</p>
            </div>
            <div className="bg-green-50 border border-green-100 rounded-xl p-3 text-center">
              <p className="text-green-600 font-bold text-xl">{stats.wins}</p>
              <p className="text-gray-400 text-xs">Wins</p>
            </div>
            <div className="bg-red-50 border border-red-100 rounded-xl p-3 text-center">
              <p className="text-red-600 font-bold text-xl">{stats.losses}</p>
              <p className="text-gray-400 text-xs">Losses</p>
            </div>
            <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-3 text-center">
              <p className="text-gray-900 font-bold text-xl">{winRate}%</p>
              <p className="text-gray-400 text-xs">Win Rate</p>
            </div>
          </div>

          {/* Win rate bar */}
          <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-500 text-xs">Win / Draw / Loss split</span>
              <span className="text-gray-700 text-xs font-medium">{stats.total_rolls} rolls</span>
            </div>
            <div className="flex h-2 rounded-full overflow-hidden">
              <div className="bg-green-400 transition-all" style={{ width: `${(stats.wins / stats.total_rolls) * 100}%` }} />
              <div className="bg-gray-300 transition-all" style={{ width: `${(stats.draws / stats.total_rolls) * 100}%` }} />
              <div className="bg-red-400 transition-all" style={{ width: `${(stats.losses / stats.total_rolls) * 100}%` }} />
            </div>
          </div>

          {/* Submission breakdown */}
          {(stats.top_submissions_scored?.length > 0 || stats.top_submissions_received?.length > 0) && (
            <div className="grid grid-cols-2 gap-3">
              {stats.top_submissions_scored?.length > 0 && (
                <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-4">
                  <p className="text-gray-500 text-xs mb-2 flex items-center gap-1.5">
                    <TrendingUp className="w-3 h-3 text-green-400" /> Scored
                  </p>
                  {stats.top_submissions_scored.map(([sub, count]) => (
                    <div key={sub} className="flex justify-between text-sm py-0.5">
                      <span className="text-gray-700 truncate">{sub}</span>
                      <span className="text-green-400 ml-2 flex-shrink-0">{count}x</span>
                    </div>
                  ))}
                </div>
              )}
              {stats.top_submissions_received?.length > 0 && (
                <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-4">
                  <p className="text-gray-500 text-xs mb-2 flex items-center gap-1.5">
                    <Swords className="w-3 h-3 text-red-400" /> Got Caught
                  </p>
                  {stats.top_submissions_received.map(([sub, count]) => (
                    <div key={sub} className="flex justify-between text-sm py-0.5">
                      <span className="text-gray-700 truncate">{sub}</span>
                      <span className="text-red-600 ml-2 flex-shrink-0">{count}x</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Filter */}
      <div className="relative w-full max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={partnerFilter}
          onChange={e => setPartnerFilter(e.target.value)}
          placeholder="Filter by partner..."
          className="w-full bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-purple-500 transition-colors"
        />
      </div>

      {/* Rolls list */}
      {rolls.length === 0 ? (
        <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-12 text-center">
          <Swords className="w-8 h-8 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-500">No rolls logged. Add them from a session detail page.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {rolls.map((r, i) => (
            <motion.div
              key={r.roll_id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="bg-gray-50/60 border border-gray-100 rounded-xl p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${
                    r.outcome?.includes('win') ? 'bg-green-500' : r.outcome === 'draw' ? 'bg-slate-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-gray-800 font-medium text-sm">{r.partner || 'Unknown'}</span>
                      <Badge label={OUTCOME_LABEL[r.outcome] || r.outcome} variant={OUTCOME_BADGE[r.outcome] || "default"} />
                      <Badge label={r.gi_nogi} variant={r.gi_nogi === "gi" ? "gi" : "nogi"} />
                    </div>
                    {r.submission_scored && (
                      <p className="text-xs text-green-400">Scored: {r.submission_scored}</p>
                    )}
                    {r.submission_received && (
                      <p className="text-xs text-red-400">Caught: {r.submission_received}</p>
                    )}
                    {r.notes && <p className="text-xs text-gray-400 mt-1">{r.notes}</p>}
                  </div>
                </div>
                {r.duration_minutes && (
                  <span className="text-gray-400 text-xs flex-shrink-0">{r.duration_minutes}min</span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
