import { AppProvider, useApp } from "./core/AppState.jsx";
import FeatureBoundary from "./core/FeatureBoundary.jsx";
import { features } from "./core/registry.js";
import "./app-ui.css";

const FETCH_MSG = "Fetching 21 years of NASA data and soil information for this spot...";
const FETCH_SUB = "The first time at a new location takes 10-30 seconds. After that it loads instantly.";

function Busy() {
  return (
    <div className="busy" role="status" aria-live="polite">
      <span className="spin" aria-hidden="true" />
      <div>
        <strong>{FETCH_MSG}</strong>
        <div className="busy-sub">{FETCH_SUB}</div>
      </div>
    </div>
  );
}

function Shell() {
  const { data, error, loading, slow } = useApp();

  // First load: nothing to show yet. Only show the banner if it is actually slow.
  if (!data) {
    return (
      <main className="wrap">
        <h1>ASTRATERRA</h1>
        {error ? <div className="err-banner">Could not load analysis: {error}</div> : slow && <Busy />}
      </main>
    );
  }

  return (
    <main className="wrap">
      {slow && <Busy />}
      {error && !loading && (
        <div className="err-banner">
          Could not update for this location: {error}. Showing the last result.
        </div>
      )}

      <h1>ASTRATERRA</h1>
      <p className="tag">
        Compare crop rotations for {data.field.name}, using NASA data and what you know about your field.
      </p>

      <div className={slow ? "dim" : ""}>
        {features.map(({ id, title, Component }) => (
          <section key={id} id={id}>
            <h2>{title}</h2>
            <FeatureBoundary title={title}>
              <Component />
            </FeatureBoundary>
          </section>
        ))}
      </div>

      <footer>
        {(data.disclaimers || []).map((d, i) => (
          <p key={i}>{d}</p>
        ))}
        <p className="data-credit">
          Data: <a href="https://power.larc.nasa.gov/" target="_blank" rel="noreferrer">NASA POWER</a>,{" "}
          <a href="https://www.earthdata.nasa.gov/data/instruments/srtm" target="_blank" rel="noreferrer">NASA SRTM</a>,{" "}
          <a href="https://soilgrids.org/" target="_blank" rel="noreferrer">SoilGrids 2.0</a>{" "}
          (ISRIC, CC-BY 4.0)
        </p>
      </footer>
    </main>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}
