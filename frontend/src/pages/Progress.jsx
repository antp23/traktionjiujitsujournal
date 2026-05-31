import { useEffect, useState } from 'react';
import { getDashboard, getSessionStats, getRollStats } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import { motion } from 'framer-motion';
import { Target, Flame, Award, TrendingUp } from 'lucide-react';

export default function Progress() {
  const [dash, setDash] = useState(null);
  const [sessionStats, setSessionStats] = useState(null);
  const [rollStats, setRollStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getDashboard(), getSessionStats(), getRollStats()])
      .then(([d, s, r]) => {
        setDash(d.data);
        setSessionStats(s.data);
        setRollStats(r.data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || "Failed to load progress data");
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingSpinner />;

  if (error) return (
    <div className="bg-red-900/20 border border-red-500/30 text-red-400 p-4 rounded-xl text-center">{error}</div>
  );

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
              <p className="text-green-400 font-bold text-xl">{rolls.submissions_applied || 0}</p>
              <p className="text-gray-500 text-xs">Subs Applied</p>
            </div>
            <div>
              <p className="text-red-400 font-bold text-xl">{rolls.submissions_received || 0}</p>
              <p className="text-gray-500 text-xs">Subs Received</p>
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
