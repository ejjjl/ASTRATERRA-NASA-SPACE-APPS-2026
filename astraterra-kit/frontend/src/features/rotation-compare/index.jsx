import { useMemo, useState } from "react";
import { useApp } from "../../core/AppState.jsx";
import { CRITERIA_GROUPS, PRIORITY_LABELS, fitParts, rankRotations } from "../../core/scoring.js";
import { CROP_LABEL, OUTCOME_LABEL, ReplayLegend, YearDetail } from "./replay-detail.jsx";
import "./rotation-compare.css";

const pct = (v) => Math.round((v ?? 0) * 100);
const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

function ScoreBars({ scores }) {
  return (
    <div className="rc-bars">
      {Object.entries(CRITERIA_GROUPS).map(([group, keys]) => {
        const v = mean(keys.map((k) => scores[k]).filter((x) => x != null));
        return (
          <div key={group} className="rc-barrow" title={`${PRIORITY_LABELS[group]}: ${pct(v)} out of 100`}>
            <span className="rc-barlabel">{PRIORITY_LABELS[group]}</span>
            <span className="rc-track"><span className="rc-fill" style={{ width: pct(v) + "%" }} /></span>
            <span className="rc-barval">{pct(v)}</span>
          </div>
        );
      })}
    </div>
  );
}

function FitBreakdown({ scores, fit, priorities }) {
  const parts = fitParts(scores, priorities);
  if (!parts.length) return null;
  return (
    <div className="rc-fit">
      <table>
        <caption>How this fit score is built</caption>
        <thead><tr><th>Priority</th><th>Score</th><th>Your weight</th><th>Points</th></tr></thead>
        <tbody>
          {parts.map((p) => (
            <tr key={p.group}>
              <td>{p.label}</td><td>{pct(p.score)}</td><td>{p.weight_pct}%</td><td>{p.points.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot><tr><td colSpan="3">Fit score</td><td>{pct(fit)}</td></tr></tfoot>
      </table>
    </div>
  );
}

function ReplayStrip({ replay }) {
  const [picked, setPicked] = useState(null);           // the year whose months are shown
  if (!replay?.length) return null;
  const bad = replay.filter((y) => y.outcome !== "ok").length;
  const year = replay.find((y) => y.year === picked);
  return (
    <div className="rc-replay">
      <div className="rc-replay-head">
        <strong>Past {replay.length} years replayed</strong>
        <span>{bad === 0 ? "No stressed years" : `${bad} stressed or failed`}</span>
      </div>
      <div className="rc-strip" role="group"
        aria-label={`Replay of ${replay.length} past years: ${bad} years with water stress or failure`}>
        {replay.map((y) => (
          <button key={y.year} type="button" className={`rc-sq ${y.outcome} ${picked === y.year ? "on" : ""}`}
            aria-pressed={picked === y.year}
            onClick={() => setPicked(picked === y.year ? null : y.year)}
            title={`${y.year} · ${CROP_LABEL[y.crop] || y.crop} · ${y.water_stress_pct}% of water need not met · ${OUTCOME_LABEL[y.outcome]}`} />
        ))}
      </div>
      <div className="rc-years"><span>{replay[0].year}</span><span>{replay[replay.length - 1].year}</span></div>
      <ReplayLegend />
      {year && <YearDetail year={year} onClose={() => setPicked(null)} />}
    </div>
  );
}

function MiniCalendar({ bareMonths }) {
  if (!bareMonths) return null;
  const bare = new Set(bareMonths);
  return (
    <div className="rc-mini" aria-label="Months with no crop cover">
      {MONTHS.map((m, i) => (
        <span key={i} className={`rc-mo ${bare.has(i + 1) ? "bare" : "cover"}`} title={bare.has(i + 1) ? "Bare" : "Covered"}>{m}</span>
      ))}
    </div>
  );
}

function RotationCard({ r, rank, priorities }) {
  const [open, setOpen] = useState(false);
  const blocked = r.blockedBy.length > 0;
  return (
    <article className={`card ${r.is_current ? "current" : ""} ${blocked ? "blocked" : ""}`}>
      <header>
        <h3>{r.name}</h3>
        {r.is_current && <span className="badge">Current</span>}
        {!blocked && rank === 1 && !r.is_current && <span className="badge gold">Top fit</span>}
      </header>

      <div className="overall">
        <span className="big">{pct(r.fit)}</span>
        <span className="sub">fit for your priorities</span>
      </div>
      <FitBreakdown scores={r.scores} fit={r.fit} priorities={priorities} />

      {blocked && (
        <p className="warn">Needs {r.blockedBy.map((b) => b.replace("_", " ")).join(", ")}. Shown for reference only.</p>
      )}

      <ScoreBars scores={r.scores} />
      {r.water_stress && (
        <p className="stress">Water stress in {r.water_stress.years_with_stress} of {r.water_stress.years_total} past years</p>
      )}
      <ReplayStrip replay={r.replay} />
      <MiniCalendar bareMonths={r.bare_months} />
      <p>{r.why}</p>

      <button className="link" onClick={() => setOpen(!open)} aria-expanded={open}>
        {open ? "Hide details" : "Why this recommendation?"}
      </button>

      {open && (
        <div className="why">
          {r.summary && <p className="rc-summary">{r.summary}</p>}
          <Section title="Benefits" items={r.benefits} />
          <Section title="Evidence"
            items={(r.evidence || []).map((e) => `${e.claim}: ${e.value} ${e.unit} (${e.source})`)} />
          <Section title="Information gaps" items={r.data_gaps} />
          <Section title="Check with local experts" items={r.risks_for_local_review} />
          <p className="conf">Confidence: {r.confidence}</p>
        </div>
      )}
    </article>
  );
}

function Section({ title, items }) {
  return (
    <div>
      <h4>{title}</h4>
      {items?.length ? <ul>{items.map((t, i) => <li key={i}>{t}</li>)}</ul> : <p className="empty">None listed yet.</p>}
    </div>
  );
}

function RotationCompare() {
  const { data, priorities, constraints } = useApp();
  const ranked = useMemo(
    () => rankRotations(data.rotations, priorities, constraints),
    [data.rotations, priorities, constraints]
  );
  return (
    <>
      <div className="grid">
        {ranked.map((r, i) => <RotationCard key={r.id} r={r} rank={i + 1} priorities={priorities} />)}
      </div>
    </>
  );
}

export default { id: "rotation-compare", title: "All rotations compared", order: 20, screen: "report", Component: RotationCompare };
