import { useEffect, useState } from "react";
import { useApp, DEMO_FARM } from "./AppState.jsx";

// Shown while a new location loads. Counts seconds and offers a way out after a few seconds.
export default function Busy() {
  const { setField } = useApp();
  const [secs, setSecs] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setSecs((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="busy no-print" role="status" aria-live="polite">
      <span className="spin" aria-hidden="true" />
      <div className="busy-text">
        <strong>Fetching 21 years of NASA data and soil information for this spot...</strong>
        <div className="busy-sub">
          {secs < 20
            ? "The first time at a new location can take a while. After that it loads instantly."
            : `Still working (${secs} s). Busy NASA and terrain servers can make a new spot take a minute or two.`}
        </div>
      </div>
      {secs >= 8 && (
        <button className="busy-btn" onClick={() => setField({ ...DEMO_FARM, name: "Your field" })}>
          Back to the demo farm
        </button>
      )}
    </div>
  );
}
