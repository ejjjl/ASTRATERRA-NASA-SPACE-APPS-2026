import { AppProvider, useApp } from "./core/AppState.jsx";
import Flow from "./core/Flow.jsx";
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
  return (
    <>
      {slow && <div className="wrap no-print"><Busy /></div>}
      {error && data && !loading && (
        <div className="wrap no-print">
          <div className="err-banner">Could not update for this location: {error}. Showing the last result.</div>
        </div>
      )}

      <div className={slow ? "dim" : ""}>
        <Flow />
      </div>

      {data && (
        <footer className="wrap">
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
      )}
    </>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}
