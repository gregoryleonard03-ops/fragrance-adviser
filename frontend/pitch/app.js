// ===== Theme =====
document.documentElement.setAttribute('data-theme', localStorage.getItem('parfindo-theme') || 'dark');

function toggleTheme() {
  const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('parfindo-theme', next);
  updateThemeButton();
}

function updateThemeButton() {
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀' : '☽';
}

updateThemeButton();
window.toggleTheme = toggleTheme;

// ===== Slide navigation =====
const slides = Array.from(document.querySelectorAll('.slide'));
const nav = document.getElementById('slide-nav');

slides.forEach((slide, i) => {
  const btn = document.createElement('button');
  btn.setAttribute('aria-label', slide.dataset.title || `Слайд ${i + 1}`);
  btn.title = slide.dataset.title || `Слайд ${i + 1}`;
  btn.addEventListener('click', () => {
    slide.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  nav.appendChild(btn);
});

const navButtons = Array.from(nav.querySelectorAll('button'));

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const idx = slides.indexOf(entry.target);
        navButtons.forEach((b, i) => b.classList.toggle('active', i === idx));
      }
    });
  },
  { threshold: 0.55 }
);

slides.forEach((s) => observer.observe(s));

// ===== Keyboard navigation =====
document.addEventListener('keydown', (e) => {
  if (!['ArrowDown', 'ArrowUp', 'PageDown', 'PageUp', 'Home', 'End'].includes(e.key)) return;
  e.preventDefault();
  const activeIdx = navButtons.findIndex((b) => b.classList.contains('active'));
  let target = activeIdx;
  if (e.key === 'ArrowDown' || e.key === 'PageDown') target = Math.min(slides.length - 1, activeIdx + 1);
  if (e.key === 'ArrowUp' || e.key === 'PageUp') target = Math.max(0, activeIdx - 1);
  if (e.key === 'Home') target = 0;
  if (e.key === 'End') target = slides.length - 1;
  if (target !== activeIdx && target >= 0) slides[target].scrollIntoView({ behavior: 'smooth' });
});
