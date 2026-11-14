// Auto-discovers every feature in src/features/<name>/index.jsx.
// To add a feature: copy features/_template, edit it, done. No App.jsx changes.
import { disabled } from "../features.config.js";

const modules = import.meta.glob("../features/*/index.jsx", { eager: true });

export const features = Object.values(modules)
  .map((m) => m.default)
  .filter((f) => f && f.id && f.Component && !disabled.includes(f.id))
  .sort((a, b) => (a.order ?? 100) - (b.order ?? 100));
