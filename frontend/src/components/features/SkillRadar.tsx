/**
 * SVG skill radar chart for roadmap progress visualization.
 */

interface SkillRadarProps {
  skills: { name: string; value: number }[];
  size?: number;
}

export function SkillRadar({ skills, size = 220 }: SkillRadarProps) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.38;
  const n = Math.max(skills.length, 3);
  const points = skills.slice(0, 8);

  const angle = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;

  const gridLevels = [0.25, 0.5, 0.75, 1];

  const dataPoints = points.map((s, i) => {
    const a = angle(i);
    const v = Math.min(1, Math.max(0, s.value / 100));
    return { x: cx + Math.cos(a) * r * v, y: cy + Math.sin(a) * r * v };
  });

  const polygon = dataPoints.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <div className="skill-radar-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-label="Skill progress radar">
        {gridLevels.map((lvl) => (
          <polygon
            key={lvl}
            points={Array.from({ length: n }, (_, i) => {
              const a = angle(i);
              return `${cx + Math.cos(a) * r * lvl},${cy + Math.sin(a) * r * lvl}`;
            }).join(" ")}
            fill="none"
            stroke="var(--border-subtle)"
            strokeWidth="1"
          />
        ))}
        {points.map((s, i) => {
          const a = angle(i);
          const lx = cx + Math.cos(a) * (r + 18);
          const ly = cy + Math.sin(a) * (r + 18);
          return (
            <text key={s.name} x={lx} y={ly} textAnchor="middle" dominantBaseline="middle" fill="var(--text-secondary)" fontSize="8">
              {s.name.length > 10 ? `${s.name.slice(0, 9)}…` : s.name}
            </text>
          );
        })}
        {dataPoints.length >= 3 && (
          <polygon points={polygon} fill="rgba(139,92,246,0.25)" stroke="var(--accent-violet)" strokeWidth="2" />
        )}
        {dataPoints.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3" fill="var(--accent-cyan)" />
        ))}
      </svg>
    </div>
  );
}
