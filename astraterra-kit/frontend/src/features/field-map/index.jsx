import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { useApp } from "../../core/AppState.jsx";

import "./field-map.css";

const LEVEL_COLOR = { high: "#c0392b", medium: "#e6a23c", low: "#4c9f70" };
const KIND_LABEL = { erosion: "Erosion risk", frost_pocket: "Frost-prone low spot" };

function slopeWords(p) {
  if (p == null) return "";
  if (p < 2) return "nearly flat";
  if (p < 6) return "gently rolling";
  if (p < 12) return "rolling to hilly";
  return "steep";
}

function Stat({ num, label, words }) {
  return (
    <div className="fm-stat">
      <span className="fm-num">{num}</span>
      <span className="fm-lab">{label}</span>
      {words ? <span className="fm-words">{words}</span> : null}
    </div>
  );
}

function FieldMap() {
  const { data, field, setField } = useApp();
  const ref = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const zonesRef = useRef(null);
  const fitKeyRef = useRef(null);
  const [note, setNote] = useState("");
  const terrain = data.field.terrain;
  const zoneCount = data.risk_zones?.features?.length ?? 0;

  // create map once
  useEffect(() => {
    const map = L.map(ref.current).setView([data.field.lat, data.field.lon], 15);
    const sat = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { attribution: "Tiles &copy; Esri, Maxar, Earthstar Geographics", maxZoom: 19 }
    ).addTo(map);
    const osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    });
    L.control.layers({ Satellite: sat, Street: osm }).addTo(map);
    markerRef.current = L.marker([data.field.lat, data.field.lon]).addTo(map);
    map.on("click", (e) => {
      const lat = +e.latlng.lat.toFixed(5);
      const lon = +e.latlng.lng.toFixed(5);
      setField({ ...(field || {}), lat, lon, name: "Selected field" });
      setNote(`Pin moved to ${lat}, ${lon}. Climate, soil and terrain update for this spot. Some rotation scores and explanations are still sample text.`);
    });
    mapRef.current = map;
    return () => map.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // move marker when field changes
  useEffect(() => {
    if (!field || !markerRef.current) return;
    markerRef.current.setLatLng([field.lat, field.lon]);
    // If the pin was set from the search box and is off screen, bring it into view.
    const map = mapRef.current;
    if (map && !map.getBounds().contains([field.lat, field.lon])) map.setView([field.lat, field.lon], 14);
  }, [field]);

  // draw risk zones
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    zonesRef.current?.remove();
    if (!data.risk_zones) return;
    zonesRef.current = L.geoJSON(data.risk_zones, {
      style: (f) => ({ color: LEVEL_COLOR[f.properties.level] || "#888", weight: 2, fillOpacity: 0.35 }),
      onEachFeature: (f, l) =>
        l.bindPopup(
          `${KIND_LABEL[f.properties.kind] || f.properties.kind}: ${f.properties.level}` +
            (f.properties.slope_pct != null ? `<br/>Slope about ${f.properties.slope_pct}%` : "")
        ),
    }).addTo(map);
    // Zoom to the zones when the location changes (not when only a toggle refetches).
    const key = `${data.field.lat},${data.field.lon}`;
    const bounds = zonesRef.current.getBounds();
    if (key !== fitKeyRef.current && bounds.isValid()) {
      map.fitBounds(bounds.pad(0.4), { maxZoom: 17 });
      fitKeyRef.current = key;
    }
  }, [data.risk_zones]);

  return (
    <>
      <p className="hint">Click the map to pick your field. Colored zones mark steep, erosion-prone ground and low spots where cold air collects.</p>
      <div ref={ref} className="map" />
      <ul className="legend">
        <li><span className="dot" style={{ background: LEVEL_COLOR.high }} /> High</li>
        <li><span className="dot" style={{ background: LEVEL_COLOR.medium }} /> Medium</li>
        <li><span className="dot" style={{ background: LEVEL_COLOR.low }} /> Low</li>
      </ul>
      {zoneCount === 0 && (
        <p className="hint">No risk zones were flagged at this spot. The land here is close to flat.</p>
      )}
      {terrain && (
        <>
          <div className="fm-stats">
            {data.field.elevation_m != null && <Stat num={`${data.field.elevation_m} m`} label="Elevation" />}
            <Stat num={`${terrain.field_slope_pct}%`} label="Average slope" words={slopeWords(terrain.field_slope_pct)} />
            <Stat num={`${terrain.max_slope_pct}%`} label="Steepest spot" words={slopeWords(terrain.max_slope_pct)} />
            <Stat num={`${terrain.relief_m} m`} label="Highest to lowest" />
          </div>
          <p className="hint">Terrain source: {terrain.source}.</p>
        </>
      )}
      {note && <p className="hint">{note}</p>}
    </>
  );
}

export default { id: "field-map", title: "Your field", order: 10, screen: "field", Component: FieldMap };
