// A small badge in the corner of each demo page: a light for the local server and the page's version.
// Green: tools/demo_server.py answered in the last few seconds. Red: it did not. Grey: the page was opened as a file.
(function () {
  const page = location.pathname.split("/").pop() || "index.html";
  const b = document.createElement("div");
  b.id = "status-badge";
  b.style.cssText = "position:fixed;bottom:8px;right:10px;z-index:50;font:12.5px/1.3 'Helvetica Neue',Helvetica,Arial,sans-serif;background:#000;color:#fff;padding:6px 10px;border-radius:4px;display:flex;gap:8px;align-items:center;box-shadow:0 1px 4px rgba(0,0,0,.3)";
  b.innerHTML = '<span id="status-light" style="width:11px;height:11px;border-radius:50%;background:#888;display:inline-block"></span><span id="status-text">checking the server…</span>';
  document.body.appendChild(b);
  const light = b.querySelector("#status-light"), text = b.querySelector("#status-text");
  async function check() {
    if (location.protocol === "file:") { light.style.background = "#888"; text.textContent = "opened as a file, no server · " + page; return; }
    try {
      const c = new AbortController(), t = setTimeout(() => c.abort(), 3000);
      const r = await fetch("/api/status?page=" + encodeURIComponent(page), { signal: c.signal, cache: "no-store" }).then(r => r.json());
      clearTimeout(t);
      light.style.background = "#22c55e";
      text.textContent = "server up · page version " + (r.page_changed || "?") + (r.commit ? " · commit " + r.commit : "") + " · checked " + r.now.slice(11);
    } catch (e) { light.style.background = "#ff3b30"; text.textContent = "server down · start tools/demo_server.py"; }
  }
  check(); setInterval(check, 5000);
})();
