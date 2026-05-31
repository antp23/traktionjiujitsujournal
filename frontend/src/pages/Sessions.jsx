import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSessions, getSessionStats } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import Badge from '../components/Badge';
import { motion } from 'framer-motion';
import { Calendar, Clock, ChevronRight, Plus, Filter, Zap } from 'lucide-react';
import { format, parseISO } from 'date-fns';

const TYPES = ['all', 'gi', 'no-gi', 'open_mat', 'drilling', 'competition_prep'];
const TYPE_LABELS = { all: 'All', gi: 'Gi', 'no-gi': 'No-Gi', open_mat: 'Open Mat', drilling: 'Drilling', competition_prep: 'Comp Prep' };

const ENERGY_COLORS = ['', 'bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-lime-500', 'bg-green-500'];

export default function Sessions() {
  const [sessions, setSessions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [typeFilter, setTypeFilter] = useState('all');
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getSessions(), getSessionStats()])
      .then(([s, st]) => {
        setSessions(s.data || []);
        setStats(st.data || null);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load sessions');
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="bg-red-900/20 border border-red-500/30 text-red-400 p-4 rounded-xl text-center">{error}</div>;

  const filtered = typeFilter === 'all' ? sessions : sessions.filter(s => s.session_type === typeFilter);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Sessions</h1>
        <button
          onClick={() => navigate('/sessions/new')}
          className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" /> Log Session
        </button>
      </div>

      {/* Stats strip */}
      {stats && (
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Total', value: stats.total_sessions },
            { label: 'This Week', value: stats.sessions_this_week },
            { label: 'This Month', value: stats.sessions_this_month },
            { label: 'Streak', value: `${stats.current_streak}w` },
          ].map(({ label, value }) => (
            <div key={label} className="bg-gray-50/60 border border-gray-100 rounded-xl p-3 text-center">
              <p className="text-gray-900 font-bold text-lg">{value}</p>
              <p className="text-gray-400 text-xs">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Type filter */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
        {TYPES.map(t => (
          <button
            key={t}
            onClick={() => setTypeFilter(t)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              typeFilter === t ? 'bg-purple-600 text-white' : 'bg-gray-50 text-gray-500 hover:text-white border border-gray-200'
            }`}
          >
            {TYPE_LABELS[t]}
          </button>
        ))}
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-12 text-center">
          <Calendar className="w-8 h-8 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-500 mb-3">{sessions.length === 0 ? 'No sessions logged yet.' : 'No sessions match this filter.'}</p>
          {sessions.length === 0 && (
            <button onClick={() => navigate('/sessions/new')} className="text-purple-600 hover:text-purple-700 text-sm transition-colors">
              Log your first session
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((session, i) => (
            <motion.div
              key={session.session_id || i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              onClick={() => navigate(`/sessions/${session.session_id}`)}
              className="bg-gray-50/60 border border-gray-100 hover:border-purple-500/40 rounded-xl p-4 cursor-pointer transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  {/* Energy dot */}
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${ENERGY_COLORS[session.energy_level] || 'bg-slate-600'}`} />
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="text-gray-800 font-medium text-sm truncate">
                        {session.focus_area || TYPE_LABELS[session.session_type] || 'Session'}
                      </p>
                      <Badge label={TYPE_LABELS[session.session_type] || session.session_type} variant={session.session_type} />
                    </div>
                    <div className="flex items-center gap-3 text-gray-400 text-xs">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {session.date ? format(parseISO(session.date), 'MMM d, yyyy') : '--'}
                      </span>
                      {session.duration_minutes && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {session.duration_minutes}m
                        </span>
                      )}
                      {session.partners?.length > 0 && (
                        <span>{session.partners.join(', ')}</span>
                      )}
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-gray-500 flex-shrink-0 transition-colors ml-2" />
              </div>
              {session.notes && (
                <p className="text-gray-400 text-xs mt-2 pl-5 truncate">{session.notes}</p>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
