import { createContext, useContext, useEffect, useRef, useState } from "react";
import { analyze } from "../api.js";

const Ctx = createContext(null);
export const useApp = () => useContext(Ctx);

// One shared store. Features read from here and never import each other.
// `loading` is true while a request is in flight. Old data stays visible meanwhile.
export function AppProvider({ children }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false); // true only when a request takes longer than ~0.6 s
  // Demo farm: the starting pin. Change these two numbers to move the demo.
  const [field, setField] = useState({ lat: 43.70767, lon: -90.93577, name: "Your field" }); // {lat, lon, name}
  const [priorities, setPriorities] = useState({ water: 0.3, soil_health: 0.4, profit: 0.2, forage: 0.1 });
  const [constraints, setConstraints] = useState({ irrigation: false, hay_equipment: false });
  const reqId = useRef(0);

  useEffect(() => {
    // A new location can take 10-30 s the first time (NASA fetch), so ignore answers
    // from older requests if the farmer clicks somewhere else in the meantime.
    const id = ++reqId.current;
    setLoading(true);
    // Cached spots answer in ~50 ms, so only show the "Fetching..." banner if it is really slow.
    const timer = setTimeout(() => {
      if (id === reqId.current) setSlow(true);
    }, 600);
    analyze({ ...(field || {}), priorities, constraints })
      .then((d) => {
        if (id !== reqId.current) return;
        clearTimeout(timer);
        setData(d);
        setError(null);
        setLoading(false);
        setSlow(false);
      })
      .catch((e) => {
        if (id !== reqId.current) return;
        clearTimeout(timer);
        setError(e.message);
        setLoading(false);
        setSlow(false);
      });
    return () => clearTimeout(timer);
    // Re-run when the farmer moves the pin or changes constraints. Priority sliders re-rank client-side.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field?.lat, field?.lon, constraints.irrigation, constraints.hay_equipment]);

  const value = { data, error, loading, slow, field, setField, priorities, setPriorities, constraints, setConstraints };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
