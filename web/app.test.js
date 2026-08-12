// Lightweight contract checks for the browser state adapter.
// Run in a browser test runner later; kept dependency-free for V1.

if (typeof window !== 'undefined' && window.AURELIX_UI) {
  const before = window.AURELIX_UI.snapshot();
  window.AURELIX_UI.apply({ governor: 'OPERATIONAL', system: 'HEALTHY' });
  const after = window.AURELIX_UI.snapshot();
  console.assert(after.governor === 'OPERATIONAL');
  console.assert(after.system === 'HEALTHY');
  console.assert(before.policy === after.policy);
}
