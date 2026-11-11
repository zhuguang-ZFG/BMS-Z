(() => {
  "use strict";

  const top = document.getElementById("book-top");
  const progress = document.getElementById("book-progress");
  if (!top && !progress) return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  let pending = false;

  const render = () => {
    pending = false;
    if (top) top.hidden = window.scrollY < 600;
    if (progress) {
      const scrollable = document.documentElement.scrollHeight - window.innerHeight;
      const ratio = scrollable > 0
        ? Math.min(1, Math.max(0, window.scrollY / scrollable)) : 0;
      progress.style.transform = "scaleX(" + ratio.toFixed(4) + ")";
    }
  };

  const schedule = () => {
    if (pending) return;
    pending = true;
    window.requestAnimationFrame(render);
  };

  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  if (top) {
    top.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: reduced.matches ? "auto" : "smooth" });
    });
  }
  render();
})();
