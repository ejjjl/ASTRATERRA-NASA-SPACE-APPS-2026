import { AppProvider, useApp } from "./core/AppState.jsx";
import Flow from "./core/Flow.jsx";
import "./app-ui.css";

// Loading and error banners live in core/Flow.jsx so they never appear on the welcome screen.
function Shell() {
  const { data } = useApp();
  return (
    <>
      <Flow />
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
