/* Subtle cursor response; no tracking on touch or reduced-motion devices. */
(() => {
  const marks = [...document.querySelectorAll('.brand-logo')];
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const fine = matchMedia('(pointer: fine)');
  let frame = 0, pointer = null;
  const reset = () => {
    if (frame) cancelAnimationFrame(frame);
    frame = 0; pointer = null;
    marks.forEach(mark => mark.style.removeProperty('transform'));
  };
  const draw = () => {
    frame = 0;
    if (!pointer || motion.matches || !fine.matches) return;
    marks.forEach(mark => {
      const box = mark.parentElement.getBoundingClientRect();
      const x = Math.max(-1, Math.min(1, (pointer.x - box.left - box.width / 2) / 220));
      const y = Math.max(-1, Math.min(1, (pointer.y - box.top - box.height / 2) / 220));
      mark.style.transform = `translate(${x * 2}px, ${y * 2}px) rotateX(${-y * 7}deg) rotateY(${x * 9}deg)`;
    });
  };
  document.addEventListener('pointermove', event => {
    if (motion.matches || !fine.matches || event.pointerType === 'touch') return;
    pointer = {x: event.clientX, y: event.clientY};
    if (!frame) frame = requestAnimationFrame(draw);
  }, {passive: true});
  document.documentElement.addEventListener('pointerleave', reset);
  window.addEventListener('blur', reset);
  motion.addEventListener('change', reset);
  fine.addEventListener('change', reset);
})();
