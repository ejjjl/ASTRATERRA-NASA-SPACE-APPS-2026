// FEATURE TEMPLATE
// 1. Copy this folder to src/features/<your-feature>/
// 2. Rename index.template.jsx to index.jsx (the registry only loads index.jsx)
// 3. Set a unique id, a title, and an order (lower = higher on the page)
// 4. Read what you need from useApp(). Never import another feature.
// 5. If you need new fields from the backend, add them to docs/api-contract.sample.json in the same PR.
import { useApp } from "../../core/AppState.jsx";

function MyFeature() {
  const { data, field, priorities, constraints } = useApp();
  // Handle missing data gracefully: the backend may not return your slice yet.
  if (!data.my_slice) return <p className="empty">No data yet.</p>;
  return <div>{/* render data.my_slice */}</div>;
}

export default { id: "my-feature", title: "My feature", order: 50, Component: MyFeature };
