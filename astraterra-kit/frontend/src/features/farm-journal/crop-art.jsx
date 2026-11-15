// Small hand-drawn-style crop illustrations (inline SVG: no image files, no licences).
// Usage: <CropArt crop="corn" size={56} />
const STEM = "#4f7a3a";
const LEAF = "#6a9a4b";

function Corn() {
  return (
    <g>
      <path d="M32 60 V14" stroke={STEM} strokeWidth="3" strokeLinecap="round" />
      <path d="M32 44 C20 40 12 30 10 22 C20 28 26 34 32 38" fill={LEAF} />
      <path d="M32 34 C44 30 52 22 55 14 C46 20 38 26 32 29" fill={LEAF} />
      <ellipse cx="38" cy="30" rx="6" ry="13" fill="#f2c94c" transform="rotate(18 38 30)" />
      {[0, 1, 2, 3, 4].map((r) => [0, 1].map((c) => (
        <circle key={`${r}${c}`} cx={35 + c * 4 + r * 1.3} cy={21 + r * 4.5} r="1.3" fill="#d9a72b" />
      )))}
      <path d="M33 42 C30 32 32 22 36 16 C34 26 36 34 40 40 Z" fill="#8fb36a" />
    </g>
  );
}

function Soybean() {
  const leaf = (x, y, r) => <ellipse cx={x} cy={y} rx="6" ry="9" fill={LEAF} transform={`rotate(${r} ${x} ${y})`} />;
  return (
    <g>
      <path d="M32 60 C31 46 33 34 32 18" stroke={STEM} strokeWidth="3" fill="none" strokeLinecap="round" />
      {leaf(24, 16, -35)}{leaf(32, 10, 0)}{leaf(40, 16, 35)}
      {leaf(22, 34, -50)}{leaf(42, 32, 50)}
      {[[25, 46, -25], [39, 44, 25], [32, 50, 0]].map(([x, y, r]) => (
        <g key={x} transform={`rotate(${r} ${x} ${y})`}>
          <rect x={x - 3.5} y={y - 8} width="7" height="16" rx="3.5" fill="#b9a564" />
          <circle cx={x} cy={y - 4} r="2" fill="#9c8a4c" /><circle cx={x} cy={y + 3} r="2" fill="#9c8a4c" />
        </g>
      ))}
    </g>
  );
}

function Wheat({ color = "#d9a93f", awn = "#c08f2c" }) {
  return (
    <g>
      <path d="M32 62 V24" stroke="#b58f45" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M32 50 C24 46 18 40 16 34 C24 38 28 42 32 44" fill="#a7b56b" />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <g key={i}>
          <ellipse cx="28" cy={26 - i * 3.6} rx="3.2" ry="4.6" fill={color} transform={`rotate(-25 28 ${26 - i * 3.6})`} />
          <ellipse cx="36" cy={26 - i * 3.6} rx="3.2" ry="4.6" fill={color} transform={`rotate(25 36 ${26 - i * 3.6})`} />
          <path d={`M27 ${23 - i * 3.6} l-7 -7 M37 ${23 - i * 3.6} l7 -7`} stroke={awn} strokeWidth="1" />
        </g>
      ))}
    </g>
  );
}

function Rye() {
  return <Wheat color="#a8b88a" awn="#7f9466" />;
}

function Oats() {
  return (
    <g>
      <path d="M32 62 V12" stroke="#a89a5a" strokeWidth="2.5" strokeLinecap="round" />
      {[[22, 20], [42, 24], [20, 34], [44, 38], [26, 46]].map(([x, y]) => (
        <g key={`${x}${y}`}>
          <path d={`M32 ${y - 4} Q${(32 + x) / 2} ${y - 8} ${x} ${y}`} stroke="#a89a5a" strokeWidth="1.2" fill="none" />
          <ellipse cx={x} cy={y + 4} rx="3" ry="5.5" fill="#e3d49a" />
        </g>
      ))}
    </g>
  );
}

function Sorghum() {
  return (
    <g>
      <path d="M32 62 V22" stroke={STEM} strokeWidth="3" strokeLinecap="round" />
      <path d="M32 48 C22 44 14 36 12 28 C22 34 28 38 32 42" fill={LEAF} />
      <path d="M32 40 C42 36 50 28 53 20" stroke={LEAF} strokeWidth="5" fill="none" strokeLinecap="round" />
      <ellipse cx="32" cy="16" rx="9" ry="12" fill="#a0522d" />
      {[0, 1, 2, 3, 4, 5, 6].map((i) => (
        <circle key={i} cx={27 + (i % 3) * 5} cy={9 + Math.floor(i / 3) * 6} r="2.2" fill="#7d3c1f" />
      ))}
    </g>
  );
}

function Alfalfa() {
  return (
    <g>
      <path d="M32 62 C30 48 34 36 32 24" stroke={STEM} strokeWidth="2.5" fill="none" strokeLinecap="round" />
      {[[24, 44, -40], [40, 40, 40], [26, 30, -30]].map(([x, y, r]) => (
        <ellipse key={x + y} cx={x} cy={y} rx="4" ry="7" fill={LEAF} transform={`rotate(${r} ${x} ${y})`} />
      ))}
      {[[32, 12], [27, 16], [37, 16], [29, 21], [35, 21], [32, 7]].map(([x, y]) => (
        <circle key={`${x}${y}`} cx={x} cy={y} r="3.6" fill="#8e6cc4" />
      ))}
    </g>
  );
}

function RedClover() {
  return (
    <g>
      <path d="M32 62 C33 50 31 40 32 26" stroke={STEM} strokeWidth="2.5" fill="none" strokeLinecap="round" />
      {[[22, 44, -30], [30, 40, 0], [38, 44, 30]].map(([x, y, r]) => (
        <ellipse key={x} cx={x} cy={y} rx="5" ry="7" fill={LEAF} transform={`rotate(${r} ${x} ${y})`} />
      ))}
      <circle cx="32" cy="18" r="11" fill="#c94c6a" />
      {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
        <path key={i} d={`M32 18 L${32 + 9 * Math.cos(i * 0.785)} ${18 + 9 * Math.sin(i * 0.785)}`} stroke="#e98aa1" strokeWidth="2" />
      ))}
    </g>
  );
}

function Sprout() {
  return (
    <g>
      <path d="M32 60 V34" stroke={STEM} strokeWidth="3" strokeLinecap="round" />
      <path d="M32 40 C22 40 16 32 16 24 C26 26 32 32 32 40" fill={LEAF} />
      <path d="M32 36 C42 34 48 26 48 18 C38 20 32 28 32 36" fill={LEAF} />
    </g>
  );
}

const ART = {
  corn: Corn, soybean: Soybean, wheat_winter: Wheat, oats: Oats, sorghum: Sorghum,
  alfalfa: Alfalfa, red_clover: RedClover, cereal_rye: Rye,
};

export default function CropArt({ crop, size = 56, title }) {
  const Art = ART[crop] || Sprout;
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label={title || crop} className="cj-art">
      <ellipse cx="32" cy="61" rx="18" ry="2.5" fill="#d9cfb4" />
      <Art />
    </svg>
  );
}
