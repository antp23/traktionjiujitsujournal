import { useCallback } from 'react';
import { format, parseISO } from 'date-fns';
import { Flag, Gauge, Milestone, Timer } from 'lucide-react';
import { getRoadToBrown } from '../lib/api';
import { useAsyncData } from '../hooks/useAsyncData';
import LoadingSpinner from '../components/LoadingSpinner';
import RoadAnimation from '../components/RoadAnimation';

const fmt = (n) => (n == null ? '—' : Number(n).toFixed(1).replace(/\.0$/, ''));

function Stat({ icon: Icon, label, value, hint }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        <Icon className="w-4 h-4 text-purple-500" /> {label}
      </div>
      <p className="text-2xl font-bold text-gray-950 mt-2">{value}</p>
      {hint && <p className="text-xs text-gray-500 mt-1">{hint}</p>}
    </div>
  );
}

export default function RoadToBrown() {
  const loader = useCallback(async () => (await getRoadToBrown()).data, []);
  const { data, loading, error } = useAsyncData(loader, { fallbackError: 'Could not load your road to brown belt.' });

  if (loading) return <LoadingSpinner />;
  if (error || !data) {
    return <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>;
  }

  const total = data.total_hours;
  const pct = Math.min(100, (data.hours_logged / total) * 100);
  const onPace = data.weekly_pace_needed != null && data.four_week_avg_pace >= data.weekly_pace_needed;

  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-purple-700">Since 3rd stripe · {format(parseISO(data.start_date), 'MMM d, yyyy')}</p>
        <h1 className="text-2xl font-bold text-gray-950 mt-1">Road to Brown Belt</h1>
        <p className="text-sm text-gray-500 mt-1">{fmt(data.hours_logged)} of {fmt(total)} hours on the mat.</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-3">
        <RoadAnimation hours={data.hours_logged} total={total} milestones={data.milestones} />
      </div>

      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
        <div className="relative pt-8 pb-10">
          <div className="h-4 rounded-full bg-gray-100 overflow-hidden" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={data.hours_logged}>
            <div className="h-full rounded-full bg-gradient-to-r from-purple-600 to-amber-800" style={{ width: `${Math.max(pct, 1)}%` }} />
          </div>
          {data.milestones.map((m) => {
            const left = (m.hours / total) * 100;
            return (
              <div key={m.label} className="absolute top-0 bottom-0" style={{ left: `${left}%` }}>
                <div className="absolute top-6 h-8 border-l-2 border-dashed border-gray-400" />
                <div className={`absolute top-16 whitespace-nowrap text-xs font-semibold ${left > 90 ? '-translate-x-full' : '-translate-x-1/2'} ${m.reached ? 'text-purple-700' : 'text-gray-600'}`}>
                  {m.reached ? '✓ ' : ''}{m.label} · {fmt(m.hours)}h
                </div>
              </div>
            );
          })}
          <div className="absolute top-0 text-xs font-semibold text-purple-700 -translate-x-1/2" style={{ left: `${Math.max(pct, 1)}%` }}>
            {fmt(data.hours_logged)}h
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat
          icon={Flag}
          label="Next milestone"
          value={data.next_milestone ? `${fmt(data.hours_to_next_milestone)}h` : 'Done'}
          hint={data.next_milestone ? `to ${data.next_milestone.label}` : 'Ready for the brown belt test'}
        />
        <Stat icon={Milestone} label="To brown belt test" value={`${fmt(data.hours_remaining)}h`} hint={`of ${fmt(total)}h total`} />
        <Stat
          icon={Timer}
          label="Pace needed"
          value={data.weekly_pace_needed == null ? '—' : `${fmt(data.weekly_pace_needed)}h/wk`}
          hint={`to hit 150h by ${format(parseISO(data.goal_date), 'MMM d, yyyy')}`}
        />
        <Stat
          icon={Gauge}
          label="4-week average"
          value={`${fmt(data.four_week_avg_pace)}h/wk`}
          hint={onPace ? 'On pace' : 'Behind pace'}
        />
      </div>
    </div>
  );
}
