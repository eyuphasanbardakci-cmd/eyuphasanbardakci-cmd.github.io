function revealLinkedSection() {
  if (!location.hash) return;
  const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (!target) return;
  for (let parent = target.parentElement; parent; parent = parent.parentElement) {
    if (parent instanceof HTMLDetailsElement) parent.open = true;
  }
  target.scrollIntoView();
}

revealLinkedSection();
window.addEventListener('hashchange', revealLinkedSection);

document.querySelectorAll('a[href="#tour"]').forEach(link => {
  link.addEventListener('click', () => {
    document.querySelector('.tour-player')?.play().catch(() => {
      // Native video controls remain available if playback needs another click.
    });
  });
});
