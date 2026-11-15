// Farm Journal: the farmer's own record of each season, kept in this browser.
// - Season calendar: what was in the field each month, year by year
// - Entries: year, crop, planting/harvest month, outcome stamp, notes
// - USDA satellite records pre-fill past years (the farmer adds their own notes)
// - Clues: the backend (POST /api/journal-clues) looks for patterns using rules, not AI
import { useEffect, useMemo, useRef, useState } from "react";
import { useApp } from "../../core/AppState.jsx";
import { useFlow } from "../../core/flowContext.js";
import { loadSaved, save } from "../../core/storage.js";
import CropArt from "./crop-art.jsx";
import "./journal.css";

const CROPS = [
  ["corn", "Corn"], ["soybean", "Soybean"], ["wheat_winter", "Winter wheat"], ["oats", "Oats"],
  ["sorghum", "Sorghum"], ["alfalfa", "Alfalfa"], ["red_clover", "Red clover"], ["cereal_rye", "Cereal rye"],
];
const CROP_NAME = Object.fromEntries(CROPS);
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const OUTCOMES = [
  { id: "good", label: "Worked well", mark: "✓" },
  { id: "so_so", label: "So-so", mark: "~" },
  { id: "failed", label: "Failed", mark: "✗" },
];
const OUTCOME = Object.fromEntries(OUTCOMES.map((o) => [o.id, o]));
const THIS_YEAR = new Date().getFullYear();
const EMPTY_FORM = { year: THIS_YEAR, crop: "corn", planted: "", harvested: "", outcome: "", notes: "" };

// Saved with the rest of the farm's answers (core/storage.js), so "Start over with a new farm"
// clears the journal too. Those helpers already handle blocked storage.
function loadEntries() {
  return loadSaved().journal || [];
}
function saveEntries(entries) {
  save({ journal: entries });
}

// Months a season covers. A winter crop (planted Oct, harvested Jul) wraps over New Year.
function seasonMonths(planted, harvested) {
  if (!planted || !harvested) return [];
  const out = [];
  for (let m = planted; ; m = (m % 12) + 1) {
    out.push(m);
    if (m === harvested || out.length > 12) break;
  }
  return out;
}

function Stamp({ outcome, small }) {
  const o = OUTCOME[outcome];
  if (!o) return null;
  return <span className={`cj-stamp ${outcome} ${small ? "small" : ""}`}>{o.mark} {o.label}</span>;
}

function SeasonCalendar({ entries }) {
  const rows = entries.filter((e) => e.planted && e.harvested).slice(0, 8);
  if (!rows.length) {
    return <p className="hint">Add planting and harvest months to an entry to see it on the season calendar.</p>;
  }
  return (
    <div className="cj-cal" role="table" aria-label="Season calendar">
      <div className="cj-cal-row head" role="row">
        <span role="columnheader" />
        {MONTHS.map((m) => <span key={m} role="columnheader">{m}</span>)}
      </div>
      {rows.map((e) => {
        const covered = seasonMonths(Number(e.planted), Number(e.harvested));
        return (
          <div className="cj-cal-row" role="row" key={e.id}>
            <span className="cj-cal-label" role="rowheader">
              <CropArt crop={e.crop} size={26} title={CROP_NAME[e.crop]} /> {e.year}
            </span>
            {MONTHS.map((m, i) => {
              const on = covered.includes(i + 1);
              const edge = i + 1 === Number(e.planted) ? "plant" : i + 1 === Number(e.harvested) ? "harvest" : "";
              return (
                <span key={m} role="cell" className={`cj-cal-cell ${on ? `on ${e.crop}` : ""} ${edge}`}
                  title={on ? `${CROP_NAME[e.crop]} in the field${edge ? ` (${edge === "plant" ? "planted" : "harvested"})` : ""}` : "No crop logged"}>
                  {edge === "plant" ? "🌱" : edge === "harvest" ? "🌾" : ""}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

function Clues({ clues, loading }) {
  if (loading && !clues.length) return <p className="hint">Looking for patterns…</p>;
  return (
    <div className="cj-clues">
      {clues.map((c, i) => (
        <article key={c.kind + i} className={`cj-note ${c.kind}`} style={{ "--tilt": `${(i % 3) - 1}deg` }}>
          <h4>{c.title}</h4>
          <p>{c.text}</p>
          {c.evidence?.length > 0 && (
            <ul className="cj-ev">
              {c.evidence.map((ev) => <li key={ev.claim}>{ev.claim}: <b>{ev.value}</b> <span>({ev.source})</span></li>)}
            </ul>
          )}
        </article>
      ))}
    </div>
  );
}

function FarmJournal() {
  const { data, field, survey } = useApp();
  const { farmName } = useFlow();
  const [entries, setEntries] = useState(loadEntries);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editing, setEditing] = useState(null);
  const [clues, setClues] = useState([]);
  const [cluesLoading, setCluesLoading] = useState(false);
  const formRef = useRef(null);

  useEffect(() => saveEntries(entries), [entries]);

  // USDA satellite records for years the farmer has not written about yet.
  const usda = useMemo(() => {
    const logged = new Set(entries.map((e) => e.year));
    return (data?.field?.crop_history || [])
      .filter((h) => h.crop && !logged.has(h.year))
      .map((h) => ({ year: h.year, crop: h.crop, name: h.name }))
      .sort((a, b) => b.year - a.year);
  }, [data, entries]);

  const sorted = useMemo(() => [...entries].sort((a, b) => b.year - a.year), [entries]);

  // Ask the backend for clues whenever the journal changes (short delay so typing does not spam it).
  useEffect(() => {
    const timer = setTimeout(() => {
      setCluesLoading(true);
      fetch("/api/journal-clues", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat: field?.lat, lon: field?.lon, soil_overrides: survey?.soil || {},
          entries: [
            ...entries.map((e) => ({ year: e.year, crop: e.crop, outcome: e.outcome || null, notes: e.notes || "" })),
            ...usda.map((h) => ({ year: h.year, crop: h.crop, outcome: null })),
          ],
        }),
      })
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((res) => setClues(res.clues || []))
        .catch(() => setClues([]))
        .finally(() => setCluesLoading(false));
    }, 400);
    return () => clearTimeout(timer);
  }, [entries, usda, field?.lat, field?.lon, survey]);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    const entry = {
      ...form,
      year: Number(form.year),
      planted: form.planted ? Number(form.planted) : "",
      harvested: form.harvested ? Number(form.harvested) : "",
      id: editing || `${Date.now()}`,
    };
    setEntries(editing ? entries.map((x) => (x.id === editing ? entry : x)) : [...entries, entry]);
    setForm(EMPTY_FORM);
    setEditing(null);
  };

  const startFrom = (values, id = null) => {
    setForm({ ...EMPTY_FORM, ...values });
    setEditing(id);
    formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const remove = (id) => {
    if (window.confirm("Delete this journal entry?")) setEntries(entries.filter((x) => x.id !== id));
  };

  return (
    <div className="cj">
      <p className="cj-intro">
        {farmName ? <b>{farmName}</b> : "Your farm"}'s field notebook. Log each season in a minute: what you planted,
        when, and how it went. Entries stay in this browser. The journal looks for patterns, such as soil pH,
        dry summers or crops that follow themselves, and suggests causes worth checking.
      </p>

      <div className="cj-layout">
        <div className="cj-main">
          <h3 className="cj-h">Clues from your records</h3>
          <Clues clues={clues} loading={cluesLoading} />

          <h3 className="cj-h">Season calendar</h3>
          <SeasonCalendar entries={sorted} />

          <h3 className="cj-h">Pages</h3>
          <div className="cj-pages">
            {sorted.length === 0 && usda.length === 0 && <p className="hint">No entries yet. Add your first season below.</p>}
            {sorted.map((e) => (
              <article key={e.id} className="cj-page">
                <CropArt crop={e.crop} size={64} title={CROP_NAME[e.crop]} />
                <div className="cj-page-body">
                  <div className="cj-page-top">
                    <span className="cj-year">{e.year}</span>
                    <span className="cj-crop">{CROP_NAME[e.crop] || e.crop}</span>
                    <Stamp outcome={e.outcome} />
                  </div>
                  {(e.planted || e.harvested) && (
                    <p className="cj-dates">
                      {e.planted ? `Planted ${MONTHS[e.planted - 1]}` : ""}{e.planted && e.harvested ? " · " : ""}
                      {e.harvested ? `Harvested ${MONTHS[e.harvested - 1]}` : ""}
                    </p>
                  )}
                  {e.notes && <p className="cj-notes">{e.notes}</p>}
                  <div className="cj-actions">
                    <button className="fl-link" onClick={() => startFrom(e, e.id)}>Edit</button>
                    <button className="fl-link" onClick={() => remove(e.id)}>Delete</button>
                  </div>
                </div>
              </article>
            ))}
            {usda.map((h) => (
              <article key={`usda-${h.year}`} className="cj-page ghost">
                <CropArt crop={h.crop} size={48} title={CROP_NAME[h.crop]} />
                <div className="cj-page-body">
                  <div className="cj-page-top">
                    <span className="cj-year">{h.year}</span>
                    <span className="cj-crop">{CROP_NAME[h.crop] || h.name}</span>
                    <span className="cj-source">USDA satellite record</span>
                  </div>
                  <button className="fl-link" onClick={() => startFrom({ year: h.year, crop: h.crop })}>
                    Add how this season went
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>

        <form ref={formRef} className="cj-form" onSubmit={submit}>
          <h3 className="cj-h">{editing ? "Edit entry" : "New entry"}</h3>
          <div className="cj-form-art"><CropArt crop={form.crop} size={72} title={CROP_NAME[form.crop]} /></div>
          <label>Year
            <input type="number" min="1990" max={THIS_YEAR + 1} value={form.year} onChange={set("year")} required />
          </label>
          <label>Crop
            <select value={form.crop} onChange={set("crop")}>
              {CROPS.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
            </select>
          </label>
          <div className="cj-two">
            <label>Planted
              <select value={form.planted} onChange={set("planted")}>
                <option value="">Month…</option>
                {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
              </select>
            </label>
            <label>Harvested
              <select value={form.harvested} onChange={set("harvested")}>
                <option value="">Month…</option>
                {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
              </select>
            </label>
          </div>
          <fieldset className="cj-outcomes">
            <legend>How did it go?</legend>
            {OUTCOMES.map((o) => (
              <button type="button" key={o.id} aria-pressed={form.outcome === o.id}
                className={`cj-stamp-btn ${o.id} ${form.outcome === o.id ? "on" : ""}`}
                onClick={() => setForm({ ...form, outcome: form.outcome === o.id ? "" : o.id })}>
                {o.mark} {o.label}
              </button>
            ))}
          </fieldset>
          <label>Notes
            <textarea rows="4" value={form.notes} onChange={set("notes")}
              placeholder="Weather, pests, yield, what you would do differently…" />
          </label>
          <div className="fl-actions">
            <button className="fl-btn primary" type="submit">{editing ? "Save changes" : "Add to journal"}</button>
            {editing && (
              <button className="fl-btn ghost" type="button" onClick={() => { setForm(EMPTY_FORM); setEditing(null); }}>
                Cancel
              </button>
            )}
          </div>
          <p className="hint">Clues suggest causes worth checking. They do not replace a soil test or local advice.</p>
        </form>
      </div>
    </div>
  );
}

export default { id: "farm-journal", title: "Farm journal", order: 90, screen: "journal", Component: FarmJournal };
