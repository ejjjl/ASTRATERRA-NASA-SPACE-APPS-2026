import { useMemo, useState } from "react";
import { useApp } from "../../core/AppState.jsx";
import { PRIORITY_LABELS, rankRotations } from "../../core/scoring.js";

const pct = (v) => Math.round((v ?? 0) * 100);

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
      {r.water_stress && (
        <p className="stress">Water stress in {r.water_stress.years_with_stress} of {r.water_stress.years_total} past years</p>
      )}
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
