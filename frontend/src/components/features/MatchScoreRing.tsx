/**
 * Circular profile match score indicator — color-coded per creative directive.
 */

interface MatchScoreRingProps {
  score: number | null;
  size?: number;
}

function tier(score: number) {
  if (score >= 90) return { cls: "match-ring--excellent", label: "Excellent" };
  if (score >= 70) return { cls: "match-ring--good", label: "Good" };
  if (score >= 50) return { cls: "match-ring--partial", label: "Partial" };
  return { cls: "match-ring--low", label: "Low" };
}

export function MatchScoreRing({ score, size = 56 }: MatchScoreRingProps) {
  if (score == null) {
    return (
      <div className="match-ring" style={{ width: size, height: size }} aria-label="Match not rated">
        <div className="match-ring__label" style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>N/A</div>
      </div>
    );
  }

  const pct = Math.min(100, Math.max(0, score));
  const { cls, label } = tier(pct);
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (pct / 100) * c;

  return (
    <div className={`match-ring ${cls}`} style={{ width: size, height: size }} aria-label={`${Math.round(pct)} percent match — ${label}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border-subtle)" strokeWidth="4" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--ring-color)"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="match-ring__label">
        {Math.round(pct)}%
        <small>{label}</small>
      </div>
    </div>
  );
}
