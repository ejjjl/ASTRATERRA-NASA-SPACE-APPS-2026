import { useState } from "react";
import { useApp } from "./AppState.jsx";
import FeatureBoundary from "./FeatureBoundary.jsx";
import Busy from "./Busy.jsx";
import { features } from "./registry.js";
import { FlowCtx } from "./flowContext.js";
import { loadSaved, save, clearSaved } from "./storage.js";
import "./flow.css";

// A feature picks its screen with `screen: "field" | "survey" | "goals" | "report" | "journal"`.
// No `screen` means it appears on the report.
const STEPS = [
  { id: "field", label: "Your field", next: "Next: soil and crops" },
  { id: "survey", label: "Soil and crops", next: "Next: goals and equipment" },
  { id: "goals", label: "Goals and equipment", next: "See my report" },
  { id: "report", label: "Report" },
];
const ORDER = ["welcome", ...STEPS.map((s) => s.id)];
const featuresFor = (screen) => features.filter((f) => (f.screen || "report") === screen);

function Welcome({ farmName, onStart, onContinue, onReset }) {
  const [name, setName] = useState("");
  if (farmName) {
    return (
      <div className="fl-welcome">
        <h2>Welcome back, {farmName}</h2>
        <p>Your answers were saved in this browser, so you can pick up where you left off.</p>
        <div className="fl-actions">
          <button className="fl-btn primary" onClick={onContinue}>Continue</button>
          <button className="fl-btn ghost" onClick={onReset}>Start over</button>
        </div>
      </div>
    );
  }
  return (
    <div className="fl-welcome">
      <h2>Welcome to your farm</h2>
      <p>
        Pick a field, tell us a little about your soil and what you grow, and we will compare your
        rotation with alternatives using 21 years of NASA data. It takes about three minutes.
      </p>
      <form onSubmit={(e) => { e.preventDefault(); onStart(name.trim() || "My farm"); }}>
        <label className="fl-label">
          What should we call your farm?
          <input className="fl-input" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="For example: North 40" maxLength={60} autoFocus />
        </label>
        <button className="fl-btn primary" type="submit">Start</button>
      </form>
      <p className="hint">No account needed. Your answers stay in this browser.</p>
    </div>
  );
}

export default function Flow() {
  const { data, error, loading, slow, resetAll } = useApp();
  const saved = useState(() => loadSaved())[0];
  const [farmName, setFarmName] = useState(saved.farmName || "");
  const [screen, setScreen] = useState("welcome");
  const hasJournal = featuresFor("journal").length > 0;

  const go = (id) => {
    setScreen(id);
    if (id !== "welcome") save({ screen: id });
    window.scrollTo?.(0, 0);
  };
  const start = (name) => {
    setFarmName(name);
    save({ farmName: name });
    go("field");
  };
  const reset = () => {
    resetAll();
    clearSaved();
    setFarmName("");
    setScreen("welcome");
  };

  const idx = ORDER.indexOf(screen);
  const prev = idx > 1 ? ORDER[idx - 1] : null;
  const step = STEPS.find((s) => s.id === screen);
  const nextId = idx >= 1 && idx < ORDER.length - 1 ? ORDER[idx + 1] : null;

  return (
    <FlowCtx.Provider value={{ screen, go, farmName }}>
      <header className="fl-hero no-print">
        <div className="wrap">
          <h1>ASTRATERRA</h1>
          <p className="tag">Compare crop rotations for your field using NASA data and what you know about your land.</p>
          {farmName && screen !== "welcome" && <span className="fl-chip">{farmName}</span>}
        </div>
      </header>

      <main className="wrap">
        {/* The welcome screen never waits on data, so no banner or dimming there. */}
        {screen !== "welcome" && slow && <Busy />}
        {screen !== "welcome" && error && data && !loading && (
          <div className="err-banner no-print">Could not update for this location: {error}. Showing the last result.</div>
        )}
        {screen === "welcome" ? (
          <Welcome farmName={farmName} onStart={start}
            onContinue={() => go(saved.screen && saved.screen !== "welcome" ? saved.screen : "field")}
            onReset={reset} />
        ) : (
          <div className={slow ? "dim" : ""}>
            <nav className="fl-steps no-print" aria-label="Progress">
              {STEPS.map((s, i) => (
                <button key={s.id} onClick={() => go(s.id)}
                  className={`fl-step ${screen === s.id ? "on" : ""} ${idx > i + 1 ? "done" : ""}`}
                  aria-current={screen === s.id ? "step" : undefined}>
                  <span className="fl-n">{i + 1}</span>
                  <span className="fl-t">{s.label}</span>
                </button>
              ))}
              {hasJournal && (
                <button onClick={() => go("journal")} className={`fl-step journal ${screen === "journal" ? "on" : ""}`}>
                  <span className="fl-t">Farm journal</span>
                </button>
              )}
            </nav>

            {!data ? (
              <p className="empty">{error ? `Could not load analysis: ${error}` : "Loading your field..."}</p>
            ) : (
              featuresFor(screen).map((f) => (
                <section key={f.id} id={f.id} className="fl-card">
                  {f.title && <h2>{f.title}</h2>}
                  <FeatureBoundary title={f.title || f.id}>
                    <f.Component />
                  </FeatureBoundary>
                </section>
              ))
            )}

            <div className="fl-nav no-print">
              {prev ? <button className="fl-btn ghost" onClick={() => go(prev)}>Back</button> : <span />}
              {step?.next && nextId ? (
                <button className="fl-btn primary" onClick={() => go(nextId)}>{step.next}</button>
              ) : null}
            </div>
            <p className="fl-reset no-print">
              <button className="fl-link" onClick={reset}>Start over with a new farm</button>
            </p>
          </div>
        )}
      </main>
    </FlowCtx.Provider>
  );
}
