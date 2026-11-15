import { useApp } from "../../core/AppState.jsx";
import { PRIORITY_LABELS } from "../../core/scoring.js";

const HELP = {
  water: "Rotations that cope better with dry summers.",
  soil_health: "Less erosion, more organic matter, fewer bare months, better nitrogen.",
  profit: "Higher expected income.",
  forage: "Hay or grazing value for livestock.",
};
const pct = (v) => Math.round((v ?? 0) * 100);

function Goals() {
  const { priorities, setPriorities, constraints, setConstraints } = useApp();
  const total = Object.keys(PRIORITY_LABELS).reduce((s, k) => s + (priorities[k] ?? 0), 0);
  return (
    <>
      <div className="panel">
        <h3>What matters most to you?</h3>
        <p className="hint">Move a slider right for more important. The report re-ranks the options as you go.</p>
        {Object.entries(PRIORITY_LABELS).map(([key, label]) => (
          <div key={key}>
            <label className="slider">
              <span>{label}</span>
              <input type="range" min="0" max="1" step="0.05" value={priorities[key] ?? 0}
                aria-describedby={`help-${key}`}
                onChange={(e) => setPriorities({ ...priorities, [key]: +e.target.value })} />
              <span className="val">{pct(priorities[key])}</span>
            </label>
            <p id={`help-${key}`} className="hint">{HELP[key]}</p>
          </div>
        ))}
        {total === 0 && <p className="warn">Set at least one priority above zero.</p>}
      </div>

      <div className="panel">
        <h3>What equipment do you have?</h3>
        <p className="hint">Options that need equipment you don't have are shown for reference only.</p>
        <label className="check">
          <input type="checkbox" checked={constraints.irrigation}
            onChange={(e) => setConstraints({ ...constraints, irrigation: e.target.checked })} />
          Irrigation
        </label>
        <label className="check">
          <input type="checkbox" checked={constraints.hay_equipment}
            onChange={(e) => setConstraints({ ...constraints, hay_equipment: e.target.checked })} />
          Hay equipment (mower, baler)
        </label>
      </div>
    </>
  );
}

export default { id: "goals", title: "Goals and equipment", order: 10, screen: "goals", Component: Goals };
