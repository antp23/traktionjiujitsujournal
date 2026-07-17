import { useCallback, useState } from 'react';
import { addRank, getDashboard, getRankHistory, getRollStats, getSessionStats } from '../lib/api';
import { useAsyncData } from '../hooks/useAsyncData';
import LoadingSpinner from '../components/LoadingSpinner';
import { motion } from 'framer-motion';
import { Award, Flame, Medal, Target, TrendingUp } from 'lucide-react';

const BELTS = ['white', 'blue', 'purple', 'brown', 'black'];
const BELT_COLORS = {
  white: 'bg-gray-200', blue: 'bg-blue-600', purple: 'bg-purple-600',
  brown: 'bg-amber-800', black: 'bg-gray-900',
};

function RankCard({ history, onSaved }) {
  const current = history[0] || null;
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    belt: current?.belt || 'white',
    stripes: current?.stripes ?? 0,
    date_awarded: new Date().toISOString().split('T')[0],
  });

  const save = async (event) => {
    event.preventDefault();
    setError('');
    setSaving(true);
    try {
      await addRank(form);
      setEditing(false);
      onSaved();
    } catch {
      setError('Could not save the rank entry. Try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Medal className="w-5 h-5 text-purple-500" />
          <h2 className="text-gray-800 font-semibold">Belt Rank</h2>
        </div>
        <button
          type="button"
          onClick={() => setEditing((value) => !value)}
          className="text-sm text-purple-700 hover:text-purple-600 font-medium"
        >
          {editing ? 'Cancel' : current ? 'Record promotion' : 'Set my rank'}
        </button>
      </div>

      {current ? (
        <div className="flex items-center gap-3">
          <span className={`inline-block w-16 h-3 rounded-sm ${BELT_COLORS[current.belt] || 'bg-gray-300'}`} />
          <p className="text-gray-800 text-sm">
            <span className="font-semibold capitalize">{current.belt} belt</span>
            {' · '}{current.stripes} {current.stripes === 1 ? 'stripe' : 'stripes'}
            <span className="text-gray-400"> · awarded {current.date_awarded}</span>
          </p>
        </div>
      ) : (
        <p className="text-gray-500 text-sm">No rank recorded yet. Set your current belt and stripes so the dashboard and sidebar show them.</p>
      )}

      {editing && (
        <form onSubmit={save} className="mt-4 space-y-3 border-t border-gray-200 pt-4">
          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>}
          <div>
            <label className="block text-xs text-gray-500 mb-2">Belt</label>
            <div className="flex flex-wrap gap-2">
              {BELTS.map((belt) => (
                <button type="button" key={belt} onClick={() => setForm((f) => ({ ...f, belt }))}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                    form.belt === belt ? 'bg-purple-700 text-white' : 'bg-gray-100 text-gray-700'
                  }`}>
                  {belt}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-2">Stripes</label>
            <div className="flex gap-2">
              {[0, 1, 2, 3, 4].map((n) => (
                <button type="button" key={n} onClick={() => setForm((f) => ({ ...f, stripes: n }))}
                  className={`w-9 h-9 rounded-lg text-sm font-bold transition-colors ${
                    form.stripes === n ? 'bg-purple-700 text-white' : 'bg-gray-100 text-gray-500'
                  }`}>
                  {n}
                </button>
              ))}
            </div>
          </div>
          <div className="max-w-xs">
            <label className="block text-xs text-gray-500 mb-1">Date awarded</label>
            <input type="date" value={form.date_awarded}
              onChange={(event) => setForm((f) => ({ ...f, date_awarded: event.target.value }))}
              className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 text-sm" required />
          </div>
          <button type="submit" disabled={saving}
            className="bg-purple-700 hover:bg-purple-600 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-medium">
            {saving ? 'Saving...' : 'Save rank'}
          </button>
        </form>
      )}

      {history.length > 1 && (
        <div className="mt-4 border-t border-gray-200 pt-3 space-y-1">
          {history.slice(1).map((entry) => (
            <p key={entry.rank_id} className="text-xs text-gray-500 capitalize">
              {entry.belt} belt · {entry.stripes} stripes · {entry.date_awarded}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Progress() {
  const loader = useCallback(async () => {
    const [dashboard, sessionStats, rollStats, rankHistory] = await Promise.all([
      getDashboard(), getSessionStats(), getRollStats(),
      getRankHistory().catch(() => ({ data: [] })),
    ]);
    return {
      dash: dashboard.data,
      sessionStats: sessionStats.data,
      rollStats: rollStats.data,
      rankHistory: rankHistory.data || [],
    };
  }, []);
  const { data, loading, error, reload } = useAsyncData(loader, { fallbackError: 'Failed to load progress data' });

  if (loading) return <LoadingSpinner />;
  if (error) return (
    <div className="bg-red-900/20 border border-red-500/30 text-red-400 p-4 rounded-xl text-center">{error}</div>
  );

  const { dash, sessionStats, rollStats, rankHistory } = data;
  const stats = dash?.session_stats || sessionStats || {};
  const rolls = rollStats || dash?.roll_stats || {};
  const total = stats.total_sessions || 0;
  const streak = stats.current_streak || 0;
  const thisWeek = stats.sessions_this_week || 0;
  const thisMonth = stats.sessions_this_month || 0;
  const totalMinutes = stats.total_minutes || 0;

  const GOAL = 100;
  const progress = Math.min(Math.round((total / GOAL) * 100), 100);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Progress</h1>

      {/* Belt rank */}
      <RankCard history={rankHistory} onSaved={reload} />

      {/* Annual goal */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Target className="w-5 h-5 text-indigo-400" />
          <h2 className="text-gray-800 font-semibold">Annual Goal</h2>
        </div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-500 text-sm">{total} / {GOAL} sessions</span>
          <span className="text-indigo-400 font-semibold text-sm">{progress}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2.5">
          <motion.div
            className="bg-indigo-500 h-2.5 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          />
        </div>
        <p className="text-gray-400 text-xs mt-2">{Math.max(GOAL - total, 0)} sessions remaining to goal</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "This Week", value: thisWeek, unit: "sessions" },
          { label: "This Month", value: thisMonth, unit: "sessions" },
          { label: "Total Sessions", value: total, unit: "all time" },
          { label: "Mat Time", value: Math.round(totalMinutes / 60), unit: "hours" },
        ].map(({ label, value, unit }) => (
          <div key={label} className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-center">
            <p className="text-gray-500 text-xs mb-1">{label}</p>
            <p className="text-gray-900 text-2xl font-bold">{value}</p>
            <p className="text-gray-400 text-xs">{unit}</p>
          </div>
        ))}
      </div>

      {/* Streak */}
      <div className="bg-amber-50 border border-amber-100 rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-2">
          <Flame className="w-5 h-5 text-amber-400" />
          <h2 className="text-gray-800 font-semibold">Weekly Streak</h2>
        </div>
        <motion.p
          className="text-4xl font-bold text-amber-400"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {streak} <span className="text-lg font-medium text-amber-400/70">{streak === 1 ? 'week' : 'weeks'}</span>
        </motion.p>
        <p className="text-gray-500 text-sm mt-1">Consecutive weeks with at least one session</p>
      </div>

      {/* Roll stats */}
      {rolls && Object.keys(rolls).length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-5 h-5 text-purple-400" />
            <h2 className="text-gray-800 font-semibold">Roll Stats</h2>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-gray-900 font-bold text-xl">{rolls.total_rolls || 0}</p>
              <p className="text-gray-500 text-xs">Total Rolls</p>
            </div>
            <div>
              <p className="text-green-400 font-bold text-xl">{rolls.wins || 0}</p>
              <p className="text-gray-500 text-xs">Wins</p>
            </div>
            <div>
              <p className="text-red-400 font-bold text-xl">{rolls.losses || 0}</p>
              <p className="text-gray-500 text-xs">Losses</p>
            </div>
          </div>
        </div>
      )}

      {/* Achievements placeholder */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-2">
          <Award className="w-5 h-5 text-amber-400" />
          <h2 className="text-gray-800 font-semibold">Achievements</h2>
        </div>
        <p className="text-gray-500 text-sm text-center py-4">Badges and milestones coming soon.</p>
      </div>
    </div>
  );
}
