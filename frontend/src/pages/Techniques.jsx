import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTechniques } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import Badge from '../components/Badge';
import { motion } from 'framer-motion';
import { BookOpen, ChevronRight, Plus, Search } from 'lucide-react';

const PROFICIENCY = ['learning', 'drilling', 'applying', 'sharp'];
const PROFICIENCY_COLOR = { learning: 'bg-slate-600', drilling: 'bg-blue-500', applying: 'bg-purple-500', sharp: 'bg-green-500' };
const PROFICIENCY_WIDTH = { learning: 'w-1/4', drilling: 'w-2/4', applying: 'w-3/4', sharp: 'w-full' };

export default function Techniques() {
  const [techniques, setTechniques] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [profFilter, setProfFilter] = useState('all');
  const navigate = useNavigate();

  useEffect(() => {
    getTechniques()
      .then(res => { setTechniques(res.data || []); setLoading(false); })
      .catch(err => { setError(err.message || 'Failed to load techniques'); setLoading(false); });
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="bg-red-900/20 border border-red-500/30 text-red-400 p-4 rounded-xl">{error}</div>;

  const filtered = techniques.filter(t => {
    const matchSearch = !search || t.name?.toLowerCase().includes(search.toLowerCase()) || t.category?.toLowerCase().includes(search.toLowerCase());
    const matchProf = profFilter === 'all' || t.proficiency === profFilter;
    return matchSearch && matchProf;
  });

  // Count by proficiency
  const counts = PROFICIENCY.reduce((acc, p) => ({ ...acc, [p]: techniques.filter(t => t.proficiency === p).length }), {});

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Techniques</h1>
        <button
          onClick={() => navigate('/techniques/new')}
          className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" /> Add Technique
        </button>
      </div>

      {/* Proficiency breakdown */}
      {techniques.length > 0 && (
        <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-gray-500 text-xs uppercase tracking-wide">Library Breakdown</p>
            <p className="text-gray-900 font-bold">{techniques.length} total</p>
          </div>
          <div className="space-y-2">
            {PROFICIENCY.map(p => (
              <div key={p} className="flex items-center gap-3">
                <span className="text-gray-500 text-xs w-16 capitalize">{p}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all ${PROFICIENCY_COLOR[p]}`}
                    style={{ width: techniques.length ? `${(counts[p] / techniques.length) * 100}%` : '0%' }}
                  />
                </div>
                <span className="text-gray-500 text-xs w-4 text-right">{counts[p]}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search + filter row */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name or category..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-4 py-2 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-purple-500 transition-colors"
          />
        </div>
        <div className="flex gap-1.5">
          {['all', ...PROFICIENCY].map(p => (
            <button
              key={p}
              onClick={() => setProfFilter(p)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                profFilter === p ? 'bg-purple-600 text-white' : 'bg-gray-50 border border-gray-200 text-gray-500 hover:text-white'
              }`}
            >
              {p === 'all' ? 'All' : p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <div className="bg-gray-50/60 border border-gray-100 rounded-xl p-12 text-center">
          <BookOpen className="w-8 h-8 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-500 mb-3">{techniques.length === 0 ? 'No techniques logged yet.' : 'No techniques match your search.'}</p>
          {techniques.length === 0 && (
            <button onClick={() => navigate('/techniques/new')} className="text-purple-600 hover:text-purple-700 text-sm">
              Add your first technique
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((tech, i) => (
            <motion.div
              key={tech.technique_id || i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              onClick={() => navigate(`/techniques/${tech.technique_id}`)}
              className="bg-gray-50/60 border border-gray-100 hover:border-purple-500/40 rounded-xl p-4 cursor-pointer transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  {/* Proficiency bar indicator */}
                  <div className="flex flex-col gap-0.5 flex-shrink-0">
                    {[...Array(4)].map((_, idx) => (
                      <div
                        key={idx}
                        className={`w-1 h-1.5 rounded-sm ${idx < PROFICIENCY.indexOf(tech.proficiency) + 1 ? PROFICIENCY_COLOR[tech.proficiency] : 'bg-gray-100'}`}
                      />
                    ))}
                  </div>
                  <div className="min-w-0">
                    <p className="text-gray-800 font-medium text-sm">{tech.name}</p>
                    <p className="text-gray-400 text-xs capitalize">
                      {tech.category}{tech.position ? ` -- ${tech.position}` : ''} &middot; {tech.gi_nogi}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Badge label={tech.proficiency} variant={tech.proficiency} />
                  <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-gray-500 transition-colors" />
                </div>
              </div>
              {tech.notes && (
                <p className="text-gray-400 text-xs mt-2 pl-7 truncate">{tech.notes}</p>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
