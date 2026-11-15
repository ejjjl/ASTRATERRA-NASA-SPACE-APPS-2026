// Replay extras: what the colours mean, and the 12 months behind one replayed year.
// Data: replay[].months[] = {month, rain_mm, demand_mm, actual_mm, soil_water_mm, stress_pct, crop_in_field}
//       replay[].bucket_mm = how much water the soil can hold for this crop's roots

const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
  "September", "October", "November", "December"];
export const OUTCOME_LABEL = { ok: "OK", stress: "Water stress", fail: "Failed" };
export const CROP_LABEL = {
  corn: "Corn", soybean: "Soybean", wheat_winter: "Winter wheat", oats: "Oats", sorghum: "Sorghum",
  alfalfa: "Alfalfa", red_clover: "Red clover", cereal_rye: "Cereal rye",
};

// Thresholds match backend/water_balance.py (OK_BELOW = 15, FAIL_FROM = 35).
export function ReplayLegend() {
  return (
    <p className="rc-legend">
      <span><i className="rc-key ok" />OK: under 15% water shortfall</span>
      <span><i className="rc-key stress" />Stress: 15-34%</span>
      <span><i className="rc-key fail" />Failed: 35%+</span>
      <span className="rc-legend-hint">Click a year for its months.</span>
    </p>
  );
}

export function YearDetail({ year, onClose }) {
  const months = year.months || [];
  if (!months.length) return null;

  // Chart geometry (SVG scales to the card width via viewBox)
  const W = 300, H = 150, left = 26, bottom = 128, top = 10;
  const maxMm = Math.max(year.bucket_mm || 0, ...months.map((m) => Math.max(m.demand_mm, m.soil_water_mm)), 1);
  const y = (mm) => bottom - (mm / maxMm) * (bottom - top);
  const step = (W - left - 4) / 12;
  const bw = step * 0.62;
  const linePts = months.map((m, i) => `${left + step * i + step / 2},${y(m.soil_water_mm)}`).join(" ");

  const growing = months.filter((m) => m.crop_in_field);
  const worst = growing.reduce((a, m) => (m.stress_pct > (a?.stress_pct ?? 0) ? m : a), null);

  return (
    <div className="rc-detail">
      <div className="rc-detail-head">
        <strong>{year.year} · {CROP_LABEL[year.crop] || year.crop} · {OUTCOME_LABEL[year.outcome]}</strong>
        <button className="rc-close" onClick={onClose} aria-label="Close year details">×</button>
      </div>
      <p className="rc-detail-sum">
        The crop got {100 - year.water_stress_pct}% of the water it needed this season
        {worst ? `; the biggest shortfall was in ${MONTH_NAMES[worst.month - 1]} (${worst.stress_pct}% short).` : "."}
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="rc-chart" role="img"
        aria-label={`Monthly water for ${year.year}: water needed, water received and soil water left`}>
        {year.bucket_mm ? (
          <>
            <line x1={left} x2={W - 4} y1={y(year.bucket_mm)} y2={y(year.bucket_mm)} className="rc-full" />
            <text x={W - 6} y={y(year.bucket_mm) - 3} className="rc-axis" textAnchor="end">soil full ({year.bucket_mm} mm)</text>
          </>
        ) : null}
        {months.map((m, i) => {
          const x = left + step * i + (step - bw) / 2;
          const short = m.crop_in_field && m.demand_mm > m.actual_mm;
          return (
            <g key={m.month}>
              <title>{`${MONTH_NAMES[m.month - 1]}: needed ${m.demand_mm} mm, got ${m.actual_mm} mm, rain ${m.rain_mm} mm, soil water left ${m.soil_water_mm} mm`}</title>
              <rect x={x} y={y(m.demand_mm)} width={bw} height={bottom - y(m.demand_mm)} className={`rc-need ${short ? "short" : ""}`} />
              <rect x={x} y={y(m.actual_mm)} width={bw} height={bottom - y(m.actual_mm)}
                className={`rc-got ${m.crop_in_field ? "" : "off"}`} />
              <text x={left + step * i + step / 2} y={H - 8} className="rc-axis" textAnchor="middle">{MONTHS[m.month - 1]}</text>
            </g>
          );
        })}
        <polyline points={linePts} className="rc-soil" />
        <line x1={left} x2={W - 4} y1={bottom} y2={bottom} className="rc-base" />
        <text x={2} y={top + 6} className="rc-axis">mm</text>
      </svg>
      <p className="rc-legend small">
        <span><i className="rc-key need" />Water needed</span>
        <span><i className="rc-key got" />Water received</span>
        <span><i className="rc-key soil" />Soil water left</span>
        <span><i className="rc-key short" />Shortfall</span>
      </p>
    </div>
  );
}
