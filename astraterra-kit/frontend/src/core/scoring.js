// Client-side re-weighting so sliders feel instant.
// NOTE: the backend is the source of truth for scores. This mirrors its weighting
// ONLY to re-rank when the farmer moves a slider. Keep the groups in sync with
// backend/rotations/scoring.py. Deterministic, no AI.

export const CRITERIA_GROUPS = {
  water: ["water"],
  soil_health: ["erosion", "bare_months", "nitrogen", "organic_matter", "pest_break"],
  profit: ["profit"],
  forage: ["forage"],
};

export const PRIORITY_LABELS = {
  water: "Saving water",
  soil_health: "Soil health",
  profit: "Profit",
  forage: "Forage value",
};

const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;

export function weightedFit(scores, priorities) {
  let num = 0;
  let den = 0;
  for (const [group, keys] of Object.entries(CRITERIA_GROUPS)) {
    const w = priorities[group] ?? 0;
    const vals = keys.map((k) => scores[k]).filter((v) => v != null);
    if (!w || !vals.length) continue;
    num += w * mean(vals);
    den += w;
  }
  return den ? num / den : 0;
}

// Returns rotations with fit + availability, sorted best first (unavailable last).
export function rankRotations(rotations, priorities, constraints) {
  return rotations
    .map((r) => {
      const missing = (r.requires || []).filter((req) => !constraints[req]);
      return { ...r, fit: weightedFit(r.scores, priorities), blockedBy: missing };
    })
    .sort((a, b) => {
      if (!!a.blockedBy.length !== !!b.blockedBy.length) return a.blockedBy.length ? 1 : -1;
      return b.fit - a.fit;
    });
}
