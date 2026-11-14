import { useApp } from "../../core/AppState.jsx";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const RAIN_LABEL = { low: "Low rain", medium: "Moderate rain", high: "Heavy rain" };

function BareCalendar() {
  const { data } = useApp();
  const cal = data.bare_field_calendar;
  if (!cal) return <p className="empty">No calendar data yet.</p>;
  const exposed = cal.months.filter((m) => m.bare && m.heavy_rain_risk === "high").length;
  return (
    <>
      <p className="hint">
        Months with no crop cover are shown in tan. Heavy-rain months (when erosion is worst) are marked with a drop.
        {exposed > 0 && <strong> {exposed} bare month(s) overlap heavy rain.</strong>}
      </p>
      <div className="cal">
        {cal.months.map((m) => (
          <div key={m.month} className={`cell ${m.bare ? "bare" : "cover"} ${m.bare && m.heavy_rain_risk === "high" ? "exposed" : ""}`}
            title={`${MONTHS[m.month - 1]}: ${m.bare ? "bare" : "covered"}, ${RAIN_LABEL[m.heavy_rain_risk]} (NDVI ${m.ndvi_median})`}>
            <span className="m">{MONTHS[m.month - 1]}</span>
            <span className="s">{m.bare ? "Bare" : "Crop"}</span>
            {m.heavy_rain_risk === "high" && <span className="drop" aria-label="Heavy rain">&#128167;</span>}
          </div>
        ))}
      </div>
      <p className="hint">Source: {cal.source}</p>
    </>
  );
}

export default { id: "bare-calendar", title: "Bare-field calendar", order: 15, Component: BareCalendar };
