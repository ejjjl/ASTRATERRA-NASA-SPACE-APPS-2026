import { useMemo, useState } from "react";
import { useApp } from "../../core/AppState.jsx";
import { CRITERIA_GROUPS, PRIORITY_LABELS, rankRotations } from "../../core/scoring.js";
import "./rotation-compare.css";

const pct = (v) => Math.round((v ?? 0) * 100);
const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

function Priorities() {
  const { priorities, setPriorities, constraints, setConstraints } = useApp();
  return (
    <div className="panel">
      <h3>What matters most to you?</h3>
      {Object.entries(PRIORITY_LABELS).map(([key, label]) => (
        <label key={key} className="slider">
          <span>{label}</span>
          <input
            type="range" min="0" max="1" step="0.05"
            value={priorities[key]}
            onChange={(e) => setPriorities({ ...priorities, [key]: +e.target.value })}
          />
          <span className="val">{pct(priorities[key])}</span>
        </label>
      ))}
      <h3>What do you have?</h3>
      <label className="check">
        <input type="checkbox" checked={constraints.irrigation}
          onChange={(e) => setConstraints({ ...constraints, irrigation: e.target.checked })} />
        Irrigation available
      </label>
      <label className="check">
        <input type="checkbox" checked={constraints.hay_equipment}
          onChange={(e) => setConstraints({ ...constraints, hay_equipment: e.target.checked })} />
        Hay equipment available
      </label>
    </div>
  );
}

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

function ReplayStrip({ replay }) {
  if (!replay?.length) return null;
  const bad = replay.filter((y) => y.outcome !== "ok").length;
  return (
    <div className="rc-replay">
      <div className="rc-replay-head">
        <strong>Past {replay.length} years replayed</strong>
        <span>{bad === 0 ? "No stressed years" : `${bad} stressed or failed`}</span>
      </div>
      <div className="rc-strip" role="img"
        aria-label={`Replay of ${replay.length} past years: ${bad} years with water stress or failure`}>
        {replay.map((y) => (
          <span key={y.year} className={`rc-sq ${y.outcome}`}
            title={`${y.year}: ${y.outcome}, ${y.water_stress_pct}% water stress`} />
        ))}
      </div>
      <div className="rc-years"><span>{replay[0].year}</span><span>{replay[replay.length - 1].year}</span></div>
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

function RotationCard({ r, rank }) {
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
      <Priorities />
      <div className="grid">
        {ranked.map((r, i) => <RotationCard key={r.id} r={r} rank={i + 1} />)}
      </div>
    </>
  );
}

export default { id: "rotation-compare", title: "Rotation comparison", order: 20, Component: RotationCompare };
