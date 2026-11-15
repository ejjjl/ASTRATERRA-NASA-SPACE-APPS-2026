import { useEffect, useMemo, useState } from "react";
import { useApp, ASSUMED_ROTATION } from "../../core/AppState.jsx";
import "./farm-survey.css";

// Crop ids must match the backend crop database. Add more here once Elaa's crops.csv loader supports them.
const CROPS = [
  ["corn", "Corn"],
  ["soybean", "Soybean"],
  ["wheat_winter", "Winter wheat"],
  ["alfalfa", "Alfalfa"],
  ["red_clover", "Red clover"],
  ["cereal_rye", "Cereal rye"],
];
const SOIL_FIELDS = [
  { key: "clay_pct", label: "Clay", unit: "%", min: 0, max: 100, step: 1 },
  { key: "sand_pct", label: "Sand", unit: "%", min: 0, max: 100, step: 1 },
  { key: "organic_carbon_pct", label: "Organic carbon", unit: "%", min: 0, max: 20, step: 0.1 },
  { key: "ph", label: "Soil pH", unit: "", min: 3, max: 10, step: 0.1 },
];

const toText = (v) => (v == null ? "" : String(v));

function FarmSurvey() {
  const { data, survey, setSurvey } = useApp();
  const [soilText, setSoilText] = useState(() =>
    Object.fromEntries(SOIL_FIELDS.map((f) => [f.key, toText(survey.soil?.[f.key])]))
  );
  const [unknownRot, setUnknownRot] = useState(survey.currentRotation == null);
  const [years, setYears] = useState(survey.currentRotation || ASSUMED_ROTATION);

  // Turn the form into a survey object, or a list of problems. Blank = "I don't know".
  const { next, errors } = useMemo(() => {
    const errs = [];
    const soil = {};
    for (const f of SOIL_FIELDS) {
      const t = soilText[f.key].trim();
      if (t === "") { soil[f.key] = null; continue; }
      const n = Number(t);
      if (Number.isNaN(n) || n < f.min || n > f.max) {
        errs.push(`${f.label} should be a number from ${f.min} to ${f.max}.`);
        soil[f.key] = null;
      } else soil[f.key] = n;
    }
    if (soil.clay_pct != null && soil.sand_pct != null && soil.clay_pct + soil.sand_pct > 100) {
      errs.push("Clay and sand together cannot be more than 100%.");
    }
    return { next: { soil, currentRotation: unknownRot ? null : years }, errors: errs };
  }, [soilText, unknownRot, years]);

  // Save automatically a moment after the farmer stops typing.
  useEffect(() => {
    if (errors.length || JSON.stringify(next) === JSON.stringify(survey)) return undefined;
    const t = setTimeout(() => setSurvey(next), 700);
    return () => clearTimeout(t);
  }, [next, errors, survey, setSurvey]);

  const soil = data.soil || {};
  const setYear = (i, v) => setYears(years.map((y, j) => (j === i ? v : y)));

  return (
    <div className="fs">
      <h3>What does your soil look like?</h3>
      <p className="hint">
        We already filled in an estimate from SoilGrids, a global soil map. If you have a soil test, enter your own
        numbers. Leave a box empty if you don't know.
      </p>
      <div className="fs-grid">
        {SOIL_FIELDS.map((f) => {
          const mine = soilText[f.key].trim() !== "";
          const auto = soil[f.key];
          const src = soil.source?.[f.key];
          return (
            <label key={f.key} className="fs-field">
              <span className="fs-lab">{f.label}{f.unit ? ` (${f.unit})` : ""}</span>
              <input
                type="number" inputMode="decimal" min={f.min} max={f.max} step={f.step}
                value={soilText[f.key]} placeholder="I don't know"
                onChange={(e) => setSoilText({ ...soilText, [f.key]: e.target.value })}
              />
              <span className="fs-help">
                {mine
                  ? "Using your value."
                  : auto != null
                    ? `We'll use ${auto}${f.unit} (${src && src !== "farmer_override" ? src : "SoilGrids"}).`
                    : "No estimate available yet."}
              </span>
            </label>
          );
        })}
      </div>
      {soil.water_per_metre_mm != null && (
        <p className="fs-note">This soil can hold about {soil.water_per_metre_mm} mm of water per metre of root zone.</p>
      )}
      {errors.map((e) => <p key={e} className="warn">{e}</p>)}

      <h3>What do you grow now?</h3>
      <p className="hint">List your crops in the order you plant them, one per year.</p>
      <label className="check">
        <input type="checkbox" checked={unknownRot} onChange={(e) => setUnknownRot(e.target.checked)} />
        I don't know (we'll assume corn one year, then soybean)
      </label>
      <div className={`fs-years ${unknownRot ? "off" : ""}`}>
        {years.map((y, i) => (
          <label key={i} className="fs-year">
            <span>Year {i + 1}</span>
            <select value={y} disabled={unknownRot} onChange={(e) => setYear(i, e.target.value)}>
              {CROPS.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
            </select>
          </label>
        ))}
      </div>
      {!unknownRot && (
        <div className="fs-years-actions">
          <button type="button" className="fl-btn ghost" disabled={years.length >= 4}
            onClick={() => setYears([...years, "corn"])}>Add a year</button>
          <button type="button" className="fl-btn ghost" disabled={years.length <= 2}
            onClick={() => setYears(years.slice(0, -1))}>Remove last year</button>
        </div>
      )}
    </div>
  );
}

export default { id: "farm-survey", title: "Soil and crops", order: 10, screen: "survey", Component: FarmSurvey };
