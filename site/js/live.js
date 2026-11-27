// A polite live region for short status messages ("Answer shown", "Saved: Got it").
export function announce(msg) {
  const el = document.getElementById('live');
  if (!el) return;
  el.textContent = '';
  setTimeout(() => { el.textContent = msg; }, 60);
}
