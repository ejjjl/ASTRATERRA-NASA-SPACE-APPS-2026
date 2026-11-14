import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { useApp } from "../../core/AppState.jsx";

const LEVEL_COLOR = { high: "#c0392b", medium: "#e6a23c", low: "#4c9f70" };
const KIND_LABEL = { erosion: "Erosion risk", frost_pocket: "Frost-prone low spot" };
const MOCK_NOTE = "Pin moved. Zones will update when the backend is connected.";

function FieldMap() {
  const { data, field, setField } = useApp();
  const ref = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const zonesRef = useRef(null);
  const [note, setNote] = useState("");

  // create map once
  useEffect(() => {
    const map = L.map(ref.current).setView([data.field.lat, data.field.lon], 15);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);
    markerRef.current = L.marker([data.field.lat, data.field.lon]).addTo(map);
    map.on("click", (e) => {
      setField({ ...(field || {}), lat: +e.latlng.lat.toFixed(5), lon: +e.latlng.lng.toFixed(5), name: "Selected field" });
      setNote(MOCK_NOTE);
    });
    mapRef.current = map;
    return () => map.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // move marker when field changes
  useEffect(() => {
    if (field && markerRef.current) markerRef.current.setLatLng([field.lat, field.lon]);
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
  }, [data.risk_zones]);

  return (
    <>
      <p className="hint">Click the map to pick your field. Colored zones show erosion and frost risk.</p>
      <div ref={ref} className="map" />
      <ul className="legend">
        <li><span className="dot" style={{ background: LEVEL_COLOR.high }} /> High</li>
        <li><span className="dot" style={{ background: LEVEL_COLOR.medium }} /> Medium</li>
        <li><span className="dot" style={{ background: LEVEL_COLOR.low }} /> Low</li>
      </ul>
      {note && <p className="hint">{note}</p>}
    </>
  );
}

export default { id: "field-map", title: "Your field", order: 10, Component: FieldMap };
