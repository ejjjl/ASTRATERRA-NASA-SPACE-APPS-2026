import { createContext, useContext, useEffect, useState } from "react";
import { analyze } from "../api.js";

const Ctx = createContext(null);
export const useApp = () => useContext(Ctx);

// One shared store. Features read from here and never import each other.
export function AppProvider({ children }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [field, setField] = useState(null); // {lat, lon, name}
  const [priorities, setPriorities] = useState({ water: 0.3, soil_health: 0.4, profit: 0.2, forage: 0.1 });
  const [constraints, setConstraints] = useState({ irrigation: false, hay_equipment: false });

  useEffect(() => {
    analyze({ ...(field || {}), priorities, constraints })
      .then((d) => {
        setData(d);
        setError(null);
        setField((f) => f || { lat: d.field.lat, lon: d.field.lon, name: d.field.name });
      })
      .catch((e) => setError(e.message));
    // Re-run when the farmer moves the pin or changes constraints. Priority sliders re-rank client-side.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field?.lat, field?.lon, constraints.irrigation, constraints.hay_equipment]);

  const value = { data, error, field, setField, priorities, setPriorities, constraints, setConstraints };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
