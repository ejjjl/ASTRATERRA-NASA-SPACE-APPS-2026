import { useState } from "react";
import { useApp, DEMO_FARM } from "../../core/AppState.jsx";
import "./location-search.css";

// Free OpenStreetMap geocoder (Nominatim). Light use only: one request per search click.
async function geocode(q) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(q)}`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`Search failed (${res.status})`);
  return res.json();
}

function LocationSearch() {
  const { field, setField } = useApp();
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const pick = (lat, lon) => {
    setField({ lat: +(+lat).toFixed(5), lon: +(+lon).toFixed(5), name: "Your field" });
    setResults([]);
    setMsg("");
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!q.trim()) return;
    setBusy(true);
    setMsg("");
    try {
      const r = await geocode(q.trim());
      setResults(r);
      if (!r.length) setMsg("No places found. Try a town, county, or address, or click the map instead.");
    } catch (err) {
      setMsg(`${err.message}. You can still click the map to pick your field.`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="ls">
      <form onSubmit={submit} className="ls-form" role="search">
        <input
          className="ls-input" value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Search for a town, address or place" aria-label="Search for a place"
        />
        <button className="fl-btn primary" type="submit" disabled={busy}>{busy ? "Searching..." : "Search"}</button>
        <button className="fl-btn ghost" type="button" onClick={() => pick(DEMO_FARM.lat, DEMO_FARM.lon)}>
          Use the demo farm
        </button>
      </form>
      {msg && <p className="hint">{msg}</p>}
      {results.length > 0 && (
        <ul className="ls-results">
          {results.map((r) => (
            <li key={r.place_id}>
              <button type="button" onClick={() => pick(r.lat, r.lon)}>{r.display_name}</button>
            </li>
          ))}
        </ul>
      )}
      <p className="hint">Selected spot: {field.lat}, {field.lon}. Search is by OpenStreetMap.</p>
    </div>
  );
}

export default { id: "location-search", title: "", order: 5, screen: "field", Component: LocationSearch };
