// Single place that talks to the backend.
// Flip USE_MOCK to false once the FastAPI backend serves POST /api/analyze.
const USE_MOCK = true;

export async function analyze(body) {
  if (USE_MOCK) {
    const res = await fetch("/sample.json");
    const json = await res.json();
    return json.response; // contract: { _meta, request_example, response }
  }
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
