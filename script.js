// Header turns solid once you scroll past the hero
const header = document.querySelector('.site-header');
const onScroll = () => header.classList.toggle('solid', window.scrollY > 40);
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

// Mobile menu: a small dropdown that slides down on hover (or tap)
const toggle = document.querySelector('.nav-toggle');
const mnav = document.getElementById('mobile-nav');
let closeTimer;
const setOpen = (open) => {
  clearTimeout(closeTimer);
  mnav.classList.toggle('open', open);
  toggle.setAttribute('aria-expanded', open);
};
const closeSoon = () => { closeTimer = setTimeout(() => setOpen(false), 180); };
// Hover opens it for a mouse; on phones, a tap does
[toggle, mnav].forEach(el => {
  el.addEventListener('pointerenter', (e) => { if (e.pointerType === 'mouse') setOpen(true); });
  el.addEventListener('pointerleave', (e) => { if (e.pointerType === 'mouse') closeSoon(); });
});
toggle.addEventListener('click', (e) => {
  // a mouse already opened it on hover, so a click keeps it open; a tap toggles it
  if (e.pointerType === 'mouse' || (e.detail && matchMedia('(hover: hover)').matches)) { setOpen(true); return; }
  setOpen(!mnav.classList.contains('open'));
});
mnav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setOpen(false)));
document.addEventListener('click', (e) => {
  if (!mnav.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });

document.getElementById('year').textContent = new Date().getFullYear();
