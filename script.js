// Header turns solid once you scroll past the hero
const header = document.querySelector('.site-header');
const onScroll = () => header.classList.toggle('solid', window.scrollY > 40);
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

// Mobile menu: tap "Menu" to open or close (hover is handled in CSS for mouse users)
const toggle = document.querySelector('.nav-toggle');
const mnav = document.getElementById('mobile-nav');
const setOpen = (open) => {
  mnav.classList.toggle('open', open);
  toggle.setAttribute('aria-expanded', String(open));
};
toggle.addEventListener('click', (e) => {
  e.stopPropagation();
  setOpen(!mnav.classList.contains('open'));
});
mnav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setOpen(false)));
// close when tapping anywhere else (pointerdown works on iPhone, where plain taps on the page may not fire "click")
document.addEventListener('pointerdown', (e) => {
  if (mnav.classList.contains('open') && !mnav.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });

document.getElementById('year').textContent = new Date().getFullYear();
