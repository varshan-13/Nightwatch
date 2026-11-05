(() => {
  const {copy, watchUrl, page} = JSON.parse(document.getElementById('tour-config').textContent);
  const dialog = document.getElementById('tour');
  const card = dialog.querySelector('.tour-card');
  const highlight = document.getElementById('tour-highlight');
  const title = document.getElementById('tour-title');
  const description = document.getElementById('tour-description');
  const progress = document.getElementById('tour-progress');
  const next = document.getElementById('tour-next');
  const back = document.getElementById('tour-back');
  const skip = document.getElementById('tour-skip');
  const key = 'nightwatch-tour-v1';
  let index = -1;
  let opener;
  let target;
  // Browsers may block storage. The tour still works for the current visit.
  const remembered = () => { try { return localStorage.getItem(key); } catch { return null; } };
  const remember = () => { try { localStorage.setItem(key, 'seen'); } catch {} };

  function position() {
    if (!dialog.open) return;
    const margin = 16;
    card.style.left = `${Math.max(margin, (innerWidth - card.offsetWidth) / 2)}px`;
    card.style.top = `${Math.max(margin, (innerHeight - card.offsetHeight) / 2)}px`;
    highlight.hidden = !target;
    if (!target) return;
    const rect = target.getBoundingClientRect();
    Object.assign(highlight.style, {
      left: `${Math.max(4, rect.left - 5)}px`, top: `${Math.max(4, rect.top - 5)}px`,
      width: `${Math.min(innerWidth - 8, rect.width + 10)}px`,
      height: `${Math.min(innerHeight - 8, rect.height + 10)}px`,
    });
    const below = rect.bottom + 16;
    const above = rect.top - card.offsetHeight - 16;
    const top = below + card.offsetHeight <= innerHeight - margin ? below
      : above >= margin ? above : innerHeight - card.offsetHeight - margin;
    card.style.top = `${Math.max(margin, top)}px`;
  }

  function render() {
    const welcome = index < 0;
    const step = welcome ? null : copy.steps[index];
    target = step ? document.querySelector(step.target) : null;
    title.textContent = welcome ? copy.welcome_title : step.title;
    description.textContent = welcome ? copy.welcome_text : step.text;
    progress.textContent = welcome ? 'Nightwatch' : `${copy.step} ${index + 1} / ${copy.steps.length}`;
    skip.textContent = welcome ? copy.explore : copy.skip;
    back.textContent = copy.back;
    back.hidden = welcome;
    next.textContent = welcome ? copy.start : index === copy.steps.length - 1 ? copy.finish : copy.next;
    if (target) target.scrollIntoView({behavior: 'instant', block: 'center'});
    position();
    title.focus({preventScroll: true});
  }

  function open(start = -1) {
    opener = document.activeElement;
    index = start;
    dialog.showModal();
    render();
  }
  function close() {
    remember();
    dialog.close();
    if (opener instanceof HTMLElement) opener.focus({preventScroll: true});
  }
  next.addEventListener('click', () => {
    if (index < 0 && page !== 'watch') {
      remember();
      location.assign(`${watchUrl}?tour=1`);
    } else if (index === copy.steps.length - 1) close();
    else { index++; render(); }
  });
  back.addEventListener('click', () => { index--; render(); });
  skip.addEventListener('click', close);
  dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
  document.querySelectorAll('[data-tour-replay]').forEach(button => button.addEventListener('click', () => open()));
  window.addEventListener('resize', position);
  window.addEventListener('scroll', position, {passive: true});
  const url = new URL(location.href);
  if (page === 'watch' && url.searchParams.get('tour') === '1') {
    url.searchParams.delete('tour');
    history.replaceState(null, '', url);
    open(0);
  } else if ((page === 'landing' || page === 'watch') && !remembered()) open();
})();
