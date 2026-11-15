// Tiny localStorage helper. No login: answers stay in this browser.
// Every call is wrapped because storage can be blocked (private windows, some previews).
const KEY = "astraterra.v1";

export function loadSaved() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || {};
  } catch {
    return {};
  }
}

export function save(patch) {
  try {
    localStorage.setItem(KEY, JSON.stringify({ ...loadSaved(), ...patch }));
  } catch {
    /* ignore */
  }
}

export function clearSaved() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
