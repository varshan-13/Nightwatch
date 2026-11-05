// Small page animations. Everything here is optional: without JavaScript, or
// with "reduce motion" switched on, the page simply shows its final state.

const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- Scroll reveals (landing page) ----------
// Headings and cards start slightly lower and transparent (see .reveal in
// style.css). When one scrolls into view we add .is-visible and CSS fades it in.
const revealTargets = document.querySelectorAll(
  '.section .tag, .section h2, .section-lead, .section .badge, .section .btn,' +
  '.section .card, .cta h2, .cta p, .cta-buttons'
);

if (!calm && 'IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        el.classList.add('is-visible');
        observer.unobserve(el);  // animate once only
        // Drop the stagger delay afterwards, so hover effects respond instantly.
        setTimeout(() => { el.style.transitionDelay = ''; }, 1200);
      }
    });
  }, {threshold: 0.15, rootMargin: '0px 0px -40px 0px'});

  revealTargets.forEach(el => {
    // Cards in the same row come in one after another.
    if (el.classList.contains('card')) {
      const index = [...el.parentElement.children].indexOf(el);
      el.style.transitionDelay = (index * 90) + 'ms';
    }
    el.classList.add('reveal');
    observer.observe(el);
  });
}

// ---------- Counters count up (Watch page) ----------
// Reads the real number from the page, then counts from 0 to it in ~0.9 s.
if (!calm) {
  document.querySelectorAll('.counter-value').forEach(el => {
    const target = parseInt(el.textContent, 10);
    if (!target) return;
    const start = performance.now();
    const duration = 900;
    const step = now => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);  // fast at first, then slows down
      el.textContent = Math.round(target * eased);
      if (t < 1) requestAnimationFrame(step);
    };
    el.textContent = '0';
    requestAnimationFrame(step);
  });
}
