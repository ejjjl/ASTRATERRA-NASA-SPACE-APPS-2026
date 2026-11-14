import { useApp } from "../../core/AppState.jsx";
import "./climate-chart.css";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const W = 720;
const H = 280;
const PAD = { l: 44, r: 12, t: 16, b: 32 };

// Round the top of the axis up to a multiple of 40 so the four tick gaps are whole numbers.
function niceMax(v) {
  return Math.ceil((v * 1.05) / 40) * 40;
}

function ClimateChart() {
  const { data } = useApp();
  const monthly = data.climate?.monthly;
  if (!monthly?.length) return <p className="empty">No monthly climate data yet.</p>;

  const max = niceMax(Math.max(...monthly.flatMap((m) => [m.rain_mm, m.et0_mm])));
  const innerW = W - PAD.l - PAD.r;
  const innerH = H - PAD.t - PAD.b;
  const slot = innerW / 12;
  const barW = slot * 0.34;
  const y = (v) => PAD.t + innerH - (v / max) * innerH;
  const ticks = [0, 1, 2, 3, 4].map((i) => (max / 4) * i);

  const deficit = monthly.filter((m) => m.water_balance_mm < 0).map((m) => m.month);
  const frost = data.climate?.frost;

  return (
    <>
      <p className="hint">
        Green bars are rain. Tan bars are how much water crops and soil would use (evaporation demand).
        Amber shading marks months when demand beats rain.
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="cc-svg" role="img"
        aria-label="Monthly rainfall compared with evaporation demand, in millimeters">
        {deficit.map((m) => (
          <rect key={m} x={PAD.l + (m - 1) * slot} y={PAD.t} width={slot} height={innerH} fill="#fbeccc" />
        ))}
        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke="#e4e0d2" />
            <text x={PAD.l - 6} y={y(t) + 4} textAnchor="end" className="cc-axis">{Math.round(t)}</text>
          </g>
        ))}
        <text x={12} y={PAD.t + innerH / 2} className="cc-axis" transform={`rotate(-90 12 ${PAD.t + innerH / 2})`} textAnchor="middle">mm per month</text>
        {monthly.map((m, i) => {
          const x0 = PAD.l + i * slot + slot / 2;
          return (
            <g key={m.month}>
              <rect x={x0 - barW - 1} y={y(m.rain_mm)} width={barW} height={y(0) - y(m.rain_mm)} fill="#2f6b45" rx="2">
                <title>{`${MONTHS[i]}: rain ${m.rain_mm} mm`}</title>
              </rect>
              <rect x={x0 + 1} y={y(m.et0_mm)} width={barW} height={y(0) - y(m.et0_mm)} fill="#c9bf9c" rx="2">
                <title>{`${MONTHS[i]}: water demand ${m.et0_mm} mm`}</title>
              </rect>
              <text x={x0} y={H - 12} textAnchor="middle" className="cc-axis">{MONTHS[i]}</text>
            </g>
          );
        })}
      </svg>
      <ul className="cc-legend">
        <li><span className="cc-sw" style={{ background: "#2f6b45" }} /> Rain</li>
        <li><span className="cc-sw" style={{ background: "#c9bf9c" }} /> Water demand</li>
        <li><span className="cc-sw" style={{ background: "#fbeccc", border: "1px solid #e6a23c" }} /> Demand beats rain</li>
      </ul>
      <p className="cc-summary">
        {deficit.length
          ? `Water demand is higher than rain in ${deficit.map((m) => MONTHS[m - 1]).join(", ")}.`
          : "Rain covers water demand in every month."}
        {frost?.frost_free_days ? ` Typical frost-free season: about ${frost.frost_free_days} days.` : ""}
      </p>
      <p className="hint">Source: NASA POWER daily data, averaged by month over {data.field.data_years?.[0]}-{data.field.data_years?.[1]}.</p>
    </>
  );
}

export default { id: "climate-chart", title: "Rain vs. water demand", order: 12, Component: ClimateChart };
