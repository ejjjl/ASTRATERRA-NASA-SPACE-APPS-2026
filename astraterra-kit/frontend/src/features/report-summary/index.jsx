import { useMemo, useState } from "react";
import { useApp } from "../../core/AppState.jsx";
import { useFlow } from "../../core/flowContext.js";
import { CRITERIA_GROUPS, PRIORITY_LABELS, rankRotations } from "../../core/scoring.js";
import "./report-summary.css";

const pct = (v) => Math.round((v ?? 0) * 100);
const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
const lower = (s) => s.toLowerCase();

function groupScore(scores, g) {
  const vals = CRITERIA_GROUPS[g].map((k) => scores[k]).filter((v) => v != null);
  return vals.length ? mean(vals) : null;
}

function Report() {
  const { data, priorities, constraints, field } = useApp();
  const { go, farmName } = useFlow();
  const [showEvidence, setShowEvidence] = useState(false);

  const ranked = useMemo(
    () => rankRotations(data.rotations, priorities, constraints),
    [data.rotations, priorities, constraints]
  );
  const winner = ranked.find((r) => !r.blockedBy.length);
  const current = ranked.find((r) => r.is_current);
  const totalWeight = Object.keys(PRIORITY_LABELS).reduce((s, g) => s + (priorities[g] ?? 0), 0);

  if (!winner) return <p className="empty">No rotations are available yet.</p>;
  if (totalWeight === 0) {
    return (
      <p className="warn">
        Every priority is set to zero, so the options cannot be ranked.{" "}
        <button className="fl-link" onClick={() => go("goals")}>Change your priorities</button>
      </p>
    );
  }

  const winnerIsCurrent = winner.id === current?.id;
  const rows = Object.keys(PRIORITY_LABELS)
    .filter((g) => (priorities[g] ?? 0) > 0)
    .map((g) => {
      const share = priorities[g] / totalWeight;
      const ws = groupScore(winner.scores, g);
      const cs = current ? groupScore(current.scores, g) : null;
      return { g, share, ws, cs, points: share * (ws ?? 0) * 100 };
    });
  const strengths = rows
    .filter((r) => r.cs != null && r.ws > r.cs)
    .sort((a, b) => b.share * (b.ws - b.cs) - a.share * (a.ws - a.cs))
    .slice(0, 2);
  const tradeoffs = rows.filter((r) => r.cs != null && r.ws - r.cs <= -0.03);

  const wStress = winner.water_stress;
  const cStress = current?.water_stress;
  const worst = (winner.replay || []).reduce((m, y) => (!m || y.water_stress_pct > m.water_stress_pct ? y : m), null);
  const years = data.field?.data_years;

  return (
    <div className="rs">
      <div className="rs-print-title">
        <h1>Rotation report for {farmName || "your farm"}</h1>
        <p>
          Field at {field.lat}, {field.lon}. Based on NASA data for {years ? `${years[0]} to ${years[1]}` : "the past 21 years"}.
          Prepared {new Date().toLocaleDateString()}.
        </p>
      </div>

      <div className="rs-winner">
        <span className="rs-kicker">{winnerIsCurrent ? "Your current rotation fits best" : "Best fit for your priorities"}</span>
        <h2 className="rs-name">{winner.name}</h2>
        <div className="rs-score">
          <span className="rs-big">{pct(winner.fit)}</span>
          <span className="rs-outof">out of 100</span>
          {current && !winnerIsCurrent && (
            <span className="rs-vs">Your current rotation: {pct(current.fit)}</span>
          )}
        </div>
        <p>{winner.why}</p>

        <ul className="rs-points">
          {winnerIsCurrent && (
            <li>
              With your current priorities, no alternative scores higher than what you grow now. The other options
              below are still worth a look if your priorities change.
            </li>
          )}
          {strengths.map((r) => (
            <li key={r.g}>
              It does best on <strong>{lower(PRIORITY_LABELS[r.g])}</strong>: {pct(r.ws)} compared with {pct(r.cs)} for
              your current rotation.
            </li>
          ))}
          {wStress && (
            <li>
              Replaying the last {wStress.years_total} years, it would have had water stress in{" "}
              <strong>{wStress.years_with_stress} years</strong>
              {cStress && !winnerIsCurrent ? `, compared with ${cStress.years_with_stress} for your current rotation` : ""}.
              {worst && worst.water_stress_pct > 0 ? ` The worst year was ${worst.year}, when water stress reached ${worst.water_stress_pct}%.` : ""}
            </li>
          )}
          {tradeoffs.map((r) => (
            <li key={r.g} className="rs-trade">
              Trade-off: it scores lower on <strong>{lower(PRIORITY_LABELS[r.g])}</strong> ({pct(r.ws)} compared with{" "}
              {pct(r.cs)} for your current rotation).
            </li>
          ))}
        </ul>
        {winner.risks_for_local_review?.length > 0 && (
          <p className="rs-check"><strong>Check with local experts:</strong> {winner.risks_for_local_review.join("; ")}.</p>
        )}
      </div>

      <div className="rs-how">
        <h3>What does the fit score mean?</h3>
        <p>
          The fit score is a <strong>relative suitability index from 0 to 100</strong>. It compares the options for
          your field and your priorities. It is <strong>not a probability of success and not a yield forecast</strong>.
          A higher number means a better match to what you said matters most.
        </p>
        <table className="rs-table">
          <thead>
            <tr><th>Priority</th><th>Share of your weighting</th><th>Score for this rotation</th><th>Points added</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.g}>
                <td>{PRIORITY_LABELS[r.g]}</td>
                <td>{pct(r.share)}%</td>
                <td>{pct(r.ws)}</td>
                <td>{r.points.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr><td colSpan="3">Fit score</td><td>{pct(winner.fit)}</td></tr>
          </tfoot>
        </table>
        <p className="hint">
          Each priority's score is the average of its sub-scores. Fit is the average of the priority scores, weighted by
          how much you care about each. <button className="fl-link no-print" onClick={() => go("goals")}>Change your priorities</button>
        </p>
      </div>

      <div className="rs-actions no-print">
        <button className="fl-btn ghost" onClick={() => setShowEvidence(!showEvidence)} aria-expanded={showEvidence}>
          {showEvidence ? "Hide evidence" : "Show evidence"}
        </button>
        <button className="fl-btn primary" onClick={() => window.print()}>Print or save as PDF</button>
      </div>

      {showEvidence && (
        <div className="rs-evidence">
          <h3>Evidence behind this recommendation</h3>
          <List title="Why it was suggested" items={[winner.why]} />
          <List title="Benefits" items={winner.benefits} />
          <List
            title="Evidence from the data"
            items={(winner.evidence || []).map((e) => `${e.claim}: ${e.value} ${e.unit} (source: ${e.source})`)}
          />
          <List title="What we don't know" items={winner.data_gaps} />
          <List title="Check with local experts" items={winner.risks_for_local_review} />
          <p className="hint">
            Confidence: {winner.confidence || "not rated"}. Soil moisture is modeled (MERRA-2), not measured by a
            satellite. This report supports, and does not replace, local agricultural expertise.
          </p>
        </div>
      )}
    </div>
  );
}

function List({ title, items }) {
  return (
    <div>
      <h4>{title}</h4>
      {items?.length ? <ul>{items.map((t, i) => <li key={i}>{t}</li>)}</ul> : <p className="empty">None listed yet.</p>}
    </div>
  );
}

export default { id: "report-summary", title: "", order: 1, screen: "report", Component: Report };
