import { AppProvider, useApp } from "./core/AppState.jsx";
import FeatureBoundary from "./core/FeatureBoundary.jsx";
import { features } from "./core/registry.js";

function Shell() {
  const { data, error } = useApp();
  if (error) return <main className="wrap">Could not load analysis: {error}</main>;
  if (!data) return <main className="wrap">Loading field analysis...</main>;

  return (
    <main className="wrap">
      <h1>ASTRATERRA</h1>
      <p className="tag">
        Compare crop rotations for {data.field.name}, using NASA data and what you know about your field.
      </p>

      {features.map(({ id, title, Component }) => (
        <section key={id} id={id}>
          <h2>{title}</h2>
          <FeatureBoundary title={title}>
            <Component />
          </FeatureBoundary>
        </section>
      ))}

      <footer>
        {data.disclaimers.map((d, i) => (
          <p key={i}>{d}</p>
        ))}
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
