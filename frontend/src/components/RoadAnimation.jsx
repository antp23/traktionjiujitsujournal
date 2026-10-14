import { useEffect, useRef, useState } from 'react';

const ROAD = 'M 30 150 C 140 150, 150 60, 260 70 S 380 160, 480 130 S 600 40, 690 70 S 760 110, 770 100';
const STORAGE_KEY = 'roadToBrown:lastSeenHours';

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

function Minifig({ walking }) {
  return (
    <g className={walking ? 'rtb-walk' : ''} transform="translate(-12,-46)">
      <rect x="9" y="0" width="6" height="3" rx="1" fill="#f5c518" stroke="#14161c" strokeWidth="0.8" />
      <rect x="5" y="2" width="14" height="11" rx="3" fill="#f5c518" stroke="#14161c" strokeWidth="0.9" />
      <circle cx="9.5" cy="7" r="1" fill="#14161c" />
      <circle cx="14.5" cy="7" r="1" fill="#14161c" />
      <path d="M9 10 Q12 12 15 10" fill="none" stroke="#14161c" strokeWidth="0.9" strokeLinecap="round" />
      <path d="M4 14 H20 L22 27 H2 Z" fill="#fff" stroke="#14161c" strokeWidth="0.9" strokeLinejoin="round" />
      <path d="M9 14 L12 21 L15 14" fill="none" stroke="#14161c" strokeWidth="1" />
      <rect x="2" y="25" width="20" height="3" fill="#0b0b0d" />
      <g className="rtb-leg-l"><rect x="3" y="28" width="8" height="16" fill="#fff" stroke="#14161c" strokeWidth="0.9" /></g>
      <g className="rtb-leg-r"><rect x="13" y="28" width="8" height="16" fill="#fff" stroke="#14161c" strokeWidth="0.9" /></g>
    </g>
  );
}

export default function RoadAnimation({ hours, total = 150, milestones = [] }) {
  const pathRef = useRef(null);
  const [pos, setPos] = useState(null);
  const [walking, setWalking] = useState(false);
  const [burst, setBurst] = useState(false);
  const [len, setLen] = useState(0);
  const [marks, setMarks] = useState(null);

  useEffect(() => {
    const path = pathRef.current;
    if (!path) return undefined;
    const length = path.getTotalLength();
    setLen(length);
    setMarks([0, 75, 150].map((h) => path.getPointAtLength(length * (h / total))));
    const at = (h) => path.getPointAtLength(length * Math.min(1, Math.max(0, h / total)));
    const stored = parseFloat(window.localStorage.getItem(STORAGE_KEY));
    const isNew = Number.isFinite(stored) && hours > stored;
    const from = isNew ? stored : Number.isFinite(stored) ? Math.min(stored, hours) : 0;
    window.localStorage.setItem(STORAGE_KEY, String(hours));

    if (prefersReducedMotion() || from === hours) {
      setPos(at(hours));
      return undefined;
    }
    let frame;
    const duration = 1600;
    const start = performance.now();
    setWalking(true);
    const step = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      setPos(at(from + (hours - from) * eased));
      if (t < 1) frame = requestAnimationFrame(step);
      else {
        setWalking(false);
        if (isNew) setBurst(true);
      }
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [hours, total]);

  const done = (h) => milestones.find((m) => m.hours === h)?.reached;

  return (
    <svg viewBox="0 0 800 225" className="w-full h-auto" role="img" aria-label={`Road to brown belt: ${hours} of ${total} hours`}>
      <style>{`
        .rtb-walk { animation: rtb-bob .32s ease-in-out infinite; }
        .rtb-walk .rtb-leg-l { animation: rtb-step .32s ease-in-out infinite; transform-origin: 7px 28px; transform-box: view-box; }
        .rtb-walk .rtb-leg-r { animation: rtb-step .32s ease-in-out infinite reverse; transform-origin: 17px 28px; transform-box: view-box; }
        @keyframes rtb-bob { 50% { transform: translate(-12px,-48px); } }
        @keyframes rtb-step { 0% { transform: rotate(-14deg); } 100% { transform: rotate(14deg); } }
        .rtb-burst circle { animation: rtb-pop .9s ease-out forwards; transform-box: fill-box; transform-origin: center; }
        @keyframes rtb-pop { 0% { opacity: 1; transform: translate(0,0) scale(1); } 100% { opacity: 0; transform: translate(var(--dx), var(--dy)) scale(.4); } }
        @media (prefers-reduced-motion: reduce) { .rtb-walk, .rtb-walk * , .rtb-burst circle { animation: none !important; } }
      `}</style>
      <path d={ROAD} fill="none" stroke="#e5e7eb" strokeWidth="22" strokeLinecap="round" />
      <path d={ROAD} fill="none" stroke="#fff" strokeWidth="2" strokeDasharray="10 10" />
      <path ref={pathRef} d={ROAD} fill="none" stroke="url(#rtbGrad)" strokeWidth="22" strokeLinecap="round"
        strokeDasharray={len ? `${len * Math.min(1, hours / total)} ${len}` : '0 9999'} opacity="0.55" />
      <defs>
        <linearGradient id="rtbGrad" x1="0" x2="1"><stop offset="0" stopColor="#7e22ce" /><stop offset="1" stopColor="#92400e" /></linearGradient>
      </defs>
      {marks && (() => {
        const [s, f, g] = marks;
        return (
          <>
            <g transform={`translate(${s.x + 6},${s.y + 72})`}>
              <rect x="-2" y="-46" width="4" height="40" fill="#6b7280" />
              <rect x="-26" y="-58" width="52" height="16" rx="3" fill="#7e22ce" />
              <text x="0" y="-46.5" textAnchor="middle" fontSize="9" fill="#fff" fontWeight="700">PURPLE</text>
            </g>
            <g transform={`translate(${f.x},${f.y - 8})`}>
              <rect x="-1.5" y="-50" width="3" height="50" fill="#374151" />
              <path d="M1.5 -50 L32 -42 L1.5 -34 Z" fill={done(75) ? '#7e22ce' : '#111827'} />
              <rect x="20" y="-46" width="3" height="8" fill="#fff" />
              <text x="0" y="16" textAnchor="middle" fontSize="10" fill="#4b5563" fontWeight="600">4th stripe · 75h</text>
            </g>
            <g transform={`translate(${g.x},${g.y - 6})`}>
              <rect x="-22" y="-52" width="5" height="52" fill="#78350f" />
              <rect x="17" y="-52" width="5" height="52" fill="#78350f" />
              <rect x="-26" y="-60" width="52" height="10" rx="2" fill="#92400e" />
              <text x="0" y="-52" textAnchor="middle" fontSize="7.5" fill="#fff" fontWeight="700">BROWN</text>
              <text x="0" y="18" textAnchor="middle" fontSize="10" fill="#4b5563" fontWeight="600">Test · 150h</text>
            </g>
          </>
        );
      })()}
      {pos && (
        <g transform={`translate(${pos.x},${pos.y})`}>
          {burst && (
            <g className="rtb-burst">
              {Array.from({ length: 10 }).map((_, i) => {
                const a = (i / 10) * Math.PI * 2;
                return <circle key={i} cx="0" cy="-30" r="3" fill={i % 2 ? '#7e22ce' : '#f5c518'}
                  style={{ '--dx': `${Math.cos(a) * 30}px`, '--dy': `${Math.sin(a) * 30}px` }} />;
              })}
            </g>
          )}
          <Minifig walking={walking} />
        </g>
      )}
    </svg>
  );
}
