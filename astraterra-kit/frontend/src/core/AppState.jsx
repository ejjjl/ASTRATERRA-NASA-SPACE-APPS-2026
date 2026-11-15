import { createContext, useContext, useEffect, useRef, useState } from "react";
import { analyze } from "../api.js";
import { loadSaved, save } from "./storage.js";

const Ctx = createContext(null);
export const useApp = () => useContext(Ctx);

// Demo farm: hilly cropland near Bloomingdale, Wisconsin. Change these two numbers to move the demo.
export const DEMO_FARM = { lat: 43.70767, lon: -90.93577 };
export const ASSUMED_ROTATION = ["corn", "soybean"];
const DEFAULT_PRIORITIES = { water: 0.3, soil_health: 0.4, profit: 0.2, forage: 0.1 };
const DEFAULT_CONSTRAINTS = { irrigation: false, hay_equipment: false };
// null = "I don't know": the backend then uses SoilGrids and a corn-soybean assumption.
const DEFAULT_SURVEY = {
  soil: { clay_pct: null, sand_pct: null, organic_carbon_pct: null, ph: null },
  currentRotation: null,
};

// One shared store. Features read from here and never import each other.
// Answers are saved in localStorage so a returning farmer picks up where they left off.
export function AppProvider({ children }) {
  const saved = useRef(loadSaved()).current;
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false); // true only when a request takes longer than ~0.6 s
  const [field, setField] = useState({ ...(saved.point || DEMO_FARM), name: "Your field" });
  const [priorities, setPriorities] = useState(saved.priorities || DEFAULT_PRIORITIES);
  const [constraints, setConstraints] = useState(saved.constraints || DEFAULT_CONSTRAINTS);
  const [survey, setSurvey] = useState(saved.survey || DEFAULT_SURVEY);
  const reqId = useRef(0);

  useEffect(() => {
    save({ point: { lat: field.lat, lon: field.lon }, priorities, constraints, survey });
  }, [field.lat, field.lon, priorities, constraints, survey]);

  const surveyKey = JSON.stringify(survey);
  useEffect(() => {
    // A new location can take 10-30 s the first time (NASA fetch), so ignore answers
    // from older requests if the farmer clicks somewhere else in the meantime.
    const id = ++reqId.current;
    setLoading(true);
    const timer = setTimeout(() => {
      if (id === reqId.current) setSlow(true);
    }, 600);
    analyze({
      lat: field.lat,
      lon: field.lon,
      name: field.name,
      priorities,
      constraints,
      soil_overrides: survey.soil,
      current_rotation: survey.currentRotation || ASSUMED_ROTATION,
    })
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
    // Refetch when the pin, equipment or survey answers change. Priority sliders re-rank in the browser.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field.lat, field.lon, constraints.irrigation, constraints.hay_equipment, surveyKey]);

  const resetAll = () => {
    setField({ ...DEMO_FARM, name: "Your field" });
    setPriorities(DEFAULT_PRIORITIES);
    setConstraints(DEFAULT_CONSTRAINTS);
    setSurvey(DEFAULT_SURVEY);
  };

  const value = {
    data, error, loading, slow,
    field, setField,
    priorities, setPriorities,
    constraints, setConstraints,
    survey, setSurvey,
    resetAll,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
