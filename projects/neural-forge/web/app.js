/* Ground Truth front end. Reads data/ground_truth.json and data/districts.geojson (built by pipeline/build.py).
   No build step: MapLibre for the map, D3 for the opening dots and the scatter plots. */
(async function () {
  "use strict";

  const [GT, GEO] = await Promise.all([
    fetch("data/ground_truth.json").then((r) => r.json()),
    fetch("data/districts.geojson").then((r) => r.json()),
  ]);

  // ---------- constants ----------
  const VERDICT = {
    confirmed: { label: "Confirmed", color: "#1ba89a", blurb: "research and New York agree" },
    contested: { label: "Contested", color: "#e9604f", blurb: "they disagree" },
    bridged: { label: "Bridged", color: "#8f6fe8", blurb: "a link no single dataset holds" },
    inconclusive: { label: "Inconclusive", color: "#5d6878", blurb: "not enough to say yet" },
  };
  const ORDER = ["confirmed", "contested", "bridged", "inconclusive"];
  const NODATA = "#1d2430";
  const LAYERS = {
    need: { field: "need_score", label: "Research needed", unit: "", ramp: ["#17120a", "#7a5414", "#ffb020", "#fff0c4"],
      note: "Heat burden × vulnerability, weighted by the questions research can't yet answer here", fmt: (v) => v.toFixed(2) },
    heat: { field: "heat_ed_rate", label: "Heat ER visits", unit: "per 100k", ramp: ["#1a0b0b", "#7f1d1d", "#ef4444", "#ffd2c9"],
      note: "Heat-stress emergency visits per 100,000 residents (5-year, age-adjusted)", fmt: (v) => v.toFixed(1), extrude: true },
    temp: { field: "surface_temp_f", label: "Surface temperature", unit: "°F", ramp: ["#1a1007", "#7c3a0a", "#f97316", "#ffe2c4"],
      note: "Daytime summer surface temperature from satellite", fmt: (v) => v.toFixed(1) },
    trees: { field: "tree_density_per_km2", label: "Street trees", unit: "per km²", ramp: ["#08160d", "#14532d", "#22c55e", "#d4f7de"],
      note: "Living street trees per km² (2015 Street Tree Census)", fmt: (v) => Math.round(v).toLocaleString("en-US") },
    poverty: { field: "poverty_pct", label: "Poverty", unit: "%", ramp: ["#0b1222", "#1e3a8a", "#3b82f6", "#d6e6ff"],
      note: "Share of residents below the federal poverty line", fmt: (v) => v.toFixed(1) },
  };
  // a claim's city x-variable → the map layer that shows it
  const X_LAYER = { tree_density_per_km2: "trees", surface_temp_f: "temp", poverty_pct: "poverty", heat_ed_rate: "heat" };
  const UNIT = { "community district": ["district", "districts"], "UHF42 neighborhood": ["neighborhood", "neighborhoods"],
    year: ["summer", "summers"] };
  // what hand-checking changed beyond excluded findings (see meta.review.notes)
  const READER_FIX = { "bridge-no-heat-cold-ed": "Research agreement 75% → 100%: we had misread “poor mental health”" };
  const STYLE = "https://tiles.openfreemap.org/styles/dark";
  const BLANK = { version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": "#0b0f15" } }] };

  // ---------- helpers ----------
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const num = (n) => Number(n).toLocaleString("en-US");
  const signed = (v, d = 2) => (v == null ? "—" : (v < 0 ? "−" : "+") + Math.abs(v).toFixed(d));
  const shortHash = (h) => (h ? h.slice(0, 13) + "…" : "");
  const unitWord = (u, n) => (UNIT[u] || [u, u + "s"])[n === 1 ? 0 : 1];
  const chip = (v, big) => `<span class="chip v-${v}${big ? " big" : ""}">${VERDICT[v].label}</span>`;
  const D = new Map(GT.districts.map((d) => [d.id, d]));
  const CLAIM = new Map(GT.claims.map((c) => [c.id, c]));
  const changedIn11 = (c) => (c.research.n_excluded_after_review || 0) > 0 || READER_FIX[c.id] || c.verdict !== c.verdict_v1;

  const tip = $("#tip");
  function showTip(html, x, y) {
    tip.innerHTML = html;
    tip.style.opacity = 1;
    const r = tip.getBoundingClientRect();
    let left = x + 14, top = y + 14;
    if (left + r.width > innerWidth - 8) left = x - r.width - 14;
    if (top + r.height > innerHeight - 8) top = y - r.height - 14;
    tip.style.transform = `translate(${left}px, ${top}px)`;
  }
  const hideTip = () => (tip.style.opacity = 0);

  function dirSentence(d, a, b) {
    if (d === "+") return `more ${a} goes with more ${b}`;
    if (d === "-") return `more ${a} goes with less ${b}`;
    if (d === "mixed") return "studies disagree";
    return "no readable direction";
  }

  // ---------- district colors ----------
  for (const L of Object.values(LAYERS)) {
    const vals = GT.districts.map((d) => d[L.field]).filter((v) => v != null).sort(d3.ascending);
    L.min = vals[0];
    L.max = vals[vals.length - 1];
    L.interp = d3.interpolateRgbBasis(L.ramp);
    // rank-based so a few outliers don't wash out the map
    L.color = (v) => (v == null ? NODATA : L.interp(0.06 + 0.94 * (d3.bisectLeft(vals, v) / (vals.length - 1))));
  }
  for (const f of GEO.features) {
    const d = D.get(f.properties.id) || {};
    for (const [k, L] of Object.entries(LAYERS)) f.properties["c_" + k] = L.color(d[L.field]);
    f.properties.h_heat = d.heat_ed_rate == null ? 0 : 120 + 2300 * (d.heat_ed_rate / LAYERS.heat.max);
    f.properties.need = d.need_score ?? 0;
  }

  // ---------- state ----------
  let layer = "need", version = "v1.1.0", selId = null, hoverId = null, hlId = null, openClaim = null, mapReady = false;

  // ---------- map ----------
  const style = await fetch(STYLE).then((r) => (r.ok ? STYLE : BLANK)).catch(() => BLANK);
  const map = new maplibregl.Map({
    container: "map", style, center: [-73.94, 40.705], zoom: 9.7, pitch: 38, bearing: -14,
    attributionControl: { compact: true }, maxPitch: 70,
  });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");

  const setState = (id, s) => id && map.setFeatureState({ source: "cd", id }, s);

  map.on("load", () => {
    const firstSymbol = undefined; // our layers sit above roads; place names move back on top after
    map.addSource("cd", { type: "geojson", data: GEO, promoteId: "id" });
    map.addLayer({ id: "cd-fill", type: "fill", source: "cd",
      paint: { "fill-color": ["get", "c_need"], "fill-opacity": 0.85, "fill-opacity-transition": { duration: 500 } } }, firstSymbol);
    map.addLayer({ id: "cd-extrude", type: "fill-extrusion", source: "cd", layout: { visibility: "none" },
      paint: { "fill-extrusion-color": ["get", "c_heat"], "fill-extrusion-height": ["get", "h_heat"],
        "fill-extrusion-opacity": 0.92, "fill-extrusion-vertical-gradient": true } }, firstSymbol);
    map.addLayer({ id: "cd-glow", type: "line", source: "cd", filter: [">=", ["get", "need"], 0.7],
      paint: { "line-color": "#ffc34d", "line-width": 9, "line-blur": 9,
        "line-opacity": ["interpolate", ["linear"], ["get", "need"], 0.7, 0.2, 1, 0.85] } }, firstSymbol);
    const st = (k) => ["boolean", ["feature-state", k], false];
    map.addLayer({ id: "cd-line", type: "line", source: "cd",
      paint: { "line-color": ["case", st("sel"), "#ffffff", st("hl"), "#ffffff", st("hover"), "rgba(255,255,255,.8)", "rgba(8,11,16,.85)"],
        "line-width": ["case", st("sel"), 2.6, st("hl"), 2.6, st("hover"), 1.6, 0.7] } });
    map.getStyle().layers.filter((l) => l.type === "symbol" && /place|city|town|suburb|neighbo/i.test(l.id))
      .forEach((l) => map.moveLayer(l.id));
    mapReady = true;
    setLayer(layer, true);
  });

  const hitLayers = () => [LAYERS[layer].extrude ? "cd-extrude" : "cd-fill"];
  map.on("mousemove", (e) => {
    if (!mapReady) return;
    const f = map.queryRenderedFeatures(e.point, { layers: hitLayers() })[0];
    const id = f ? f.properties.id : null;
    if (id !== hoverId) { setState(hoverId, { hover: false }); hoverId = id; setState(hoverId, { hover: true }); }
    map.getCanvas().style.cursor = id ? "pointer" : "";
    if (!id) return hideTip();
    const d = D.get(id), L = LAYERS[layer], v = d[L.field];
    showTip(`<b>${esc(d.name)}</b><span>${esc(d.borough)}</span><em>${L.label}: ${v == null ? "no data" : L.fmt(v) + " " + L.unit}</em>`,
      e.originalEvent.clientX, e.originalEvent.clientY);
  });
  map.on("mouseout", () => { setState(hoverId, { hover: false }); hoverId = null; hideTip(); });
  map.on("click", (e) => {
    const f = map.queryRenderedFeatures(e.point, { layers: hitLayers() })[0];
    f ? openDistrict(f.properties.id) : closeDistrict();
  });

  function setLayer(key, instant) {
    layer = key;
    const L = LAYERS[key];
    document.querySelectorAll(".layerbar button").forEach((b) => b.classList.toggle("on", b.dataset.k === key));
    $("#legend").innerHTML = `<h4>${L.label}${L.unit ? ` <span class="stat">(${L.unit})</span>` : ""}</h4><p>${L.note}</p>
      <div class="ramp" style="background:linear-gradient(90deg,${d3.range(0, 1.01, 0.1).map((t) => L.interp(0.06 + 0.94 * t)).join(",")})"></div>
      <div class="ends"><span>${L.fmt(L.min)}</span><span>${key === "need" ? "most needed" : L.fmt(L.max)}</span></div>`;
    if (!mapReady) return;
    map.setPaintProperty("cd-fill", "fill-color", ["get", "c_" + key]);
    map.setPaintProperty("cd-fill", "fill-opacity", L.extrude ? 0.04 : 0.85);
    map.setLayoutProperty("cd-extrude", "visibility", L.extrude ? "visible" : "none");
    map.setLayoutProperty("cd-glow", "visibility", key === "need" ? "visible" : "none");
    if (!instant) map.easeTo({ pitch: L.extrude ? 55 : 38, duration: 900 });
  }
  $("#layerbar").innerHTML = Object.entries(LAYERS).map(([k, L]) => `<button data-k="${k}">${L.label}</button>`).join("");
  $("#layerbar").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) setLayer(b.dataset.k); });
  setLayer("need", true);

  // ---------- district card ----------
  function openDistrict(id) {
    const d = D.get(id);
    if (!d) return;
    setState(selId, { sel: false }); selId = id; setState(selId, { sel: true });
    const c = CLAIM.get(d.top_need_claim);
    const row = (k, v, f, u) => `<span>${k}</span><em>${v == null ? "no data" : f(v) + (u ? " " + u : "")}</em>`;
    const missing = (d.missing_study || "").split(/(?<=\.)\s+/);
    const el = $("#district");
    el.hidden = false;
    el.innerHTML = `<button class="close" aria-label="Close">×</button>
      <h3>${esc(d.name)}</h3><div class="sub">${esc(d.borough)} · community district</div>
      <div class="rank">Research needed <b>#${d.need_rank}</b> of ${GT.districts.length}</div>
      <div class="kv">
        ${row("Heat ER visits / 100k", d.heat_ed_rate, (v) => v.toFixed(1))}
        ${row("Summer surface temp", d.surface_temp_f, (v) => v.toFixed(1), "°F")}
        ${row("Street trees / km²", d.tree_density_per_km2, (v) => Math.round(v).toLocaleString("en-US"))}
        ${row("Poverty", d.poverty_pct, (v) => v.toFixed(1), "%")}
        ${row("Older adults living alone", d.older_alone_pct, (v) => v.toFixed(1), "%")}
      </div>
      ${c ? `<h5>Most open question here</h5><p><button class="linkbtn" data-claim="${c.id}">${esc(c.title)}</button> ${chip(c.verdict)}</p>` : ""}
      <h5>The missing study</h5><p>${esc(missing.slice(0, 2).join(" "))}</p>
      ${missing.length > 2 ? `<p style="margin-top:6px"><b>What would settle it:</b> ${esc(missing.slice(2).join(" "))}</p>` : ""}`;
    el.querySelector(".close").onclick = closeDistrict;
    const lb = el.querySelector("[data-claim]");
    if (lb) lb.onclick = () => openDrawer(lb.dataset.claim);
  }
  function closeDistrict() { setState(selId, { sel: false }); selId = null; $("#district").hidden = true; }

  // ---------- ledger ----------
  function renderLedger() {
    const counts = d3.rollup(GT.claims, (v) => v.length, (c) => (version === "v1.0.0" ? c.verdict_v1 : c.verdict));
    const rv = GT.meta.review || {};
    const nChanged = GT.claims.filter((c) => c.verdict !== c.verdict_v1).length;
    const cc = GT.meta.claims_collection;
    const banner = version === "v1.1.0"
      ? `<b>Hand-checked:</b> ${rv.checked} findings read against their papers · ${rv.ok} held up · ${rv.wrong} wrong in the graph (excluded) ·
         <b>${nChanged} verdict${nChanged === 1 ? "" : "s"} changed</b>
         <details><summary>What hand-checking changed</summary><ul>${(rv.notes || []).map((n) => `<li>${esc(n)}</li>`).join("")}</ul></details>
         <a href="${cc.compare_url}" target="_blank" rel="noopener">See exactly which records changed on Underlay ↗</a>`
      : `<b>Automated run.</b> Every finding as the graph extracted it, before we checked any by hand.
         Switch to <b>v1.1.0</b> to see what hand-checking changed.`;
    const sorted = [...GT.claims].sort((a, b) => ORDER.indexOf(a.verdict) - ORDER.indexOf(b.verdict) || Math.abs(b.city.rho) - Math.abs(a.city.rho));
    $("#ledger").innerHTML = `
      <h2>The ledger</h2>
      <p class="lead">${GT.claims.length} things the research says about heat, each tested against New York's own data.</p>
      <div class="tiles">${ORDER.map((v) => `<div class="tile"><b>${counts.get(v) || 0}</b><span><i class="dot v-${v}"></i>${VERDICT[v].label}</span></div>`).join("")}</div>
      <div class="banner">${banner}</div>
      <div class="cards">${sorted.map(card).join("")}</div>`;
  }
  function card(c) {
    const v = version === "v1.0.0" ? c.verdict_v1 : c.verdict;
    const r = c.research, ct = c.city;
    let chg = "";
    if (version === "v1.1.0" && changedIn11(c)) {
      chg = READER_FIX[c.id] || `${r.n_excluded_after_review} finding excluded after hand-check`;
    }
    return `<button class="card${openClaim === c.id ? " active" : ""}" data-id="${c.id}">
      <div class="row">${chip(v)}${c.kind === "bridge" ? `<span class="kind">bridge</span>` : ""}</div>
      <h3>${esc(c.title)}</h3>
      <p class="meta">NYC ρ ${signed(ct.rho)} · ${ct.n} ${unitWord(ct.unit, ct.n)} · ${r.n_studies} studies, ${r.population?.nyc ?? 0} in NYC</p>
      ${chg ? `<p class="chg">● ${esc(chg)}</p>` : ""}</button>`;
  }
  $("#ledger").addEventListener("click", (e) => { const b = e.target.closest(".card"); if (b) openDrawer(b.dataset.id); });

  // ---------- version toggle ----------
  document.querySelectorAll(".version button").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.v === version) return;
    version = b.dataset.v;
    document.querySelectorAll(".version button").forEach((x) => x.classList.toggle("on", x === b));
    renderLedger();
    if (openClaim) openDrawer(openClaim, true);
    if (version === "v1.1.0") {
      document.querySelectorAll(".card").forEach((el) => { if (changedIn11(CLAIM.get(el.dataset.id))) el.classList.add("pulse"); });
    }
  }));

  // ---------- claim drawer ----------
  const drawer = $("#drawer");
  function openDrawer(id, keepScroll) {
    const c = CLAIM.get(id);
    if (!c) return;
    openClaim = id;
    const v = version === "v1.0.0" ? c.verdict_v1 : c.verdict;
    const r = c.research, ct = c.city, pop = r.population || {};
    const first = c.chain[0].label, last = c.chain[c.chain.length - 1].label;
    const regions = Object.entries(pop.regions || {}).sort((a, b) => b[1] - a[1]);
    const total = d3.sum(regions, (d) => d[1]) || 1;
    const units = unitWord(ct.unit, ct.n);

    drawer.innerHTML = `<button class="close" aria-label="Close">×</button>
      <div class="row">${chip(v, true)}<span class="kind">${c.kind === "bridge" ? "bridge · " : ""}${VERDICT[v].blurb}</span></div>
      <h2>${esc(c.title)}</h2>
      <div class="chain" id="chain"></div>

      <div class="sec"><h5>The research says</h5>
        <p class="say">${r.direction ? `<b>${r.direction === "mixed" ? "±" : r.direction === "+" ? "↑" : "↓"}</b> ` : ""}${esc(dirSentence(r.direction, first, last))}</p>
        <p class="stat">${num(r.n_studies)} studies · ${num(r.n_findings)} findings${r.agree_share != null ? ` · ${Math.round(r.agree_share * 100)}% agree` : ""}</p>
        ${c.kind === "bridge" && r.links.length > 1 ? `<ul class="links3">${r.links.map((l) => `<li>${esc(l.from)} → ${esc(l.to)}: ${
          l.city_fill ? `studies split (${l.n_studies}), so NYC's own data supply this link (ρ ${signed(l.city_fill.rho)})`
                      : `${esc(dirSentence(l.direction, l.from, l.to))} (${l.n_studies} studies${l.agree_share != null ? `, ${Math.round(l.agree_share * 100)}% agree` : ""})`}</li>`).join("")}</ul>` : ""}
        <div class="regbar">${regions.map(([k, n]) => `<i class="${k === "NYC" ? "nyc" : ""}" style="flex:${n}" data-tip="${esc(k)}: ${n} studies"></i>`).join("")}</div>
        <p class="reglab"><b style="color:${pop.nyc ? "var(--accent)" : "var(--contested)"}">${pop.nyc || 0} in New York City.</b>
          Where they were done: ${regions.slice(0, 4).map(([k, n]) => `${esc(k)} ${n}`).join(" · ")}${regions.length > 4 ? " · …" : ""}</p>
      </div>

      <div class="sec"><h5>New York says</h5>
        <p class="say">Across ${ct.n} ${units}, ρ <b>${signed(ct.rho)}</b>${ct.ci ? ` <span class="stat">(95% CI ${signed(ct.ci[0])} to ${signed(ct.ci[1])})</span>` : ""}</p>
        <p class="stat">${ct.partial_rho_poverty != null ? `after accounting for poverty: ρ ${signed(ct.partial_rho_poverty)} · ` : ""}false-discovery q ${ct.q.toFixed(3)}</p>
        <div class="scatter" id="scatter"></div>
        ${ct.unit === "community district" ? `<p class="stat">Hover a dot to find the district on the map.</p>` : ""}
        ${ct.middle_links ? `<h5>Does each middle link hold in NYC?</h5><ul class="links3">${ct.middle_links.map((m) =>
          `<li>${esc(m.x_label)} → ${esc(m.y_label)}: ρ ${signed(m.rho)} ${m.p < 0.05 ? "✓ holds" : "· does not hold"}</li>`).join("")}</ul>` : ""}
        ${c.bridge_note ? `<p class="stat" style="margin-top:6px">${esc(c.bridge_note)}</p>` : ""}
        ${c.note ? `<p class="stat" style="margin-top:6px">${esc(c.note)}</p>` : ""}
      </div>

      <div class="sec"><h5>Verdict</h5>
        <div class="row">${chip(v, true)}</div>
        ${c.triage.length ? `<div class="tags">${c.triage.map((t) => `<span class="tag">${esc(t)}</span>`).join("")}</div>` : ""}
        ${c.resolution ? `<p>${esc(c.resolution)}</p>` : ""}
        ${c.settle ? `<div class="settle"><b>What would settle it</b><p>${esc(c.settle)}</p></div>` : ""}
        ${c.review && c.review.checked ? `<p class="stat" style="margin-top:8px">Hand-checked: ${c.review.checked} findings read against their papers ·
          ${c.review.ok} held up · ${c.review.wrong} wrong${version === "v1.1.0" && r.n_excluded_after_review ? " (excluded)" : ""}</p>` : ""}
      </div>

      <div class="sec"><h5>Rests on these exact records</h5><ul class="cites">
        ${ct.sources.map((s) => cite(s, s.record_ids && s.record_ids.length ? `${num(s.record_ids.length)} ${s.record_type} records` : s.query)).join("")}
        ${r.links.filter((l) => l.city_fill).flatMap((l) => l.city_fill.sources).map((s) => cite(s, `${num((s.record_ids || []).length)} ${s.record_type} records (bridge link)`)).join("")}
        ${cite(r.graph, `${num(r.association_ids.length)} Association records`, "Research findings")}
      </ul></div>`;
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
    if (!keepScroll) drawer.scrollTop = 0;
    drawer.querySelector(".close").onclick = closeDrawer;
    drawer.querySelectorAll("[data-tip]").forEach((n) => {
      n.onmousemove = (e) => showTip(`<b>${n.dataset.tip}</b>`, e.clientX, e.clientY);
      n.onmouseleave = hideTip;
    });
    drawChain(c);
    drawScatter(c, VERDICT[v].color);
    document.querySelectorAll(".card").forEach((el) => el.classList.toggle("active", el.dataset.id === id));
    if (ct.unit === "community district" && X_LAYER[ct.x] && X_LAYER[ct.x] !== layer) setLayer(X_LAYER[ct.x]);
  }
  function cite(s, what, label) {
    return `<li><a href="${s.url}" target="_blank" rel="noopener">${esc(s.collection)}@${esc(s.semver)}</a>
      <code>${esc(shortHash(s.hash))}</code><br>${esc(label || s.label || "")}${s.period ? ` · ${esc(s.period)}` : ""}${what ? ` · ${esc(what)}` : ""}</li>`;
  }
  function closeDrawer() {
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    openClaim = null;
    setState(hlId, { hl: false });
    document.querySelectorAll(".card").forEach((el) => el.classList.remove("active"));
  }
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closeDrawer(); closeDistrict(); } });

  function wrap(text, max) {
    const words = text.split(" "), lines = [""];
    for (const w of words) {
      const cur = lines[lines.length - 1];
      if ((cur + " " + w).trim().length > max && cur) lines.push(w); else lines[lines.length - 1] = (cur + " " + w).trim();
    }
    return lines.slice(0, 3);
  }
  function drawChain(c) {
    const W = 556, H = 112, n = c.chain.length, nodeW = n === 3 ? 140 : 170, nodeH = 54;
    const xs = d3.range(n).map((i) => (n === 1 ? W / 2 : nodeW / 2 + (i * (W - nodeW)) / (n - 1)));
    const svg = d3.select("#chain").append("svg").attr("viewBox", `0 0 ${W} ${H}`);
    svg.append("defs").append("marker").attr("id", "arr").attr("viewBox", "0 0 10 10").attr("refX", 9).attr("refY", 5)
      .attr("markerWidth", 7).attr("markerHeight", 7).attr("orient", "auto")
      .append("path").attr("d", "M0,0L10,5L0,10z").attr("fill", "#7d8a9b");
    const y = H - nodeH / 2 - 4;
    c.research.links.forEach((l, i) => {
      if (i >= n - 1) return;
      const x1 = xs[i] + nodeW / 2 + 4, x2 = xs[i + 1] - nodeW / 2 - 6;
      const fromCity = !!l.city_fill;
      svg.append("line").attr("x1", x1).attr("x2", x2).attr("y1", y).attr("y2", y)
        .attr("stroke", fromCity ? "#ffc34d" : "#7d8a9b").attr("stroke-width", 2).attr("stroke-dasharray", fromCity ? "5 4" : null)
        .attr("marker-end", "url(#arr)");
      const mid = (x1 + x2) / 2;
      const top = fromCity ? `NYC data · ρ ${signed(l.city_fill.rho)}` : `research · ${l.direction === "mixed" ? "split" : l.direction || "?"}`;
      const sub = fromCity ? `research split (${l.n_studies} studies)` : `${l.n_studies} studies`;
      svg.append("text").attr("x", mid).attr("y", 18).attr("text-anchor", "middle").attr("fill", fromCity ? "#ffc34d" : "#b4bfcc")
        .attr("font-size", 11.5).attr("font-weight", 600).text(top);
      svg.append("text").attr("x", mid).attr("y", 33).attr("text-anchor", "middle").attr("fill", "#7d8a9b").attr("font-size", 10.5).text(sub);
    });
    if (c.chain.length === 2 && c.research.links.length === 0) return;
    c.chain.forEach((node, i) => {
      const g = svg.append("g").attr("transform", `translate(${xs[i] - nodeW / 2},${y - nodeH / 2})`);
      g.append("rect").attr("width", nodeW).attr("height", nodeH).attr("rx", 10).attr("fill", "#161d28").attr("stroke", "rgba(148,163,184,.35)");
      const lines = wrap(node.label, n === 3 ? 18 : 22);
      lines.forEach((t, j) => g.append("text").attr("x", nodeW / 2).attr("y", nodeH / 2 + (j - (lines.length - 1) / 2) * 14 + 4)
        .attr("text-anchor", "middle").attr("fill", "#e8edf3").attr("font-size", 12).attr("font-weight", 500).text(t));
    });
  }

  function drawScatter(c, color) {
    const ct = c.city, pts = ct.scatter.filter((p) => p.x != null && p.y != null);
    const W = 556, H = 250, m = { t: 10, r: 12, b: 42, l: 48 };
    const svg = d3.select("#scatter").append("svg").attr("viewBox", `0 0 ${W} ${H}`);
    const x = d3.scaleLinear().domain(d3.extent(pts, (p) => p.x)).nice().range([m.l, W - m.r]);
    const yS = d3.scaleLinear().domain(d3.extent(pts, (p) => p.y)).nice().range([H - m.b, m.t]);
    svg.append("g").attr("class", "grid").attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(yS).ticks(4).tickSize(-(W - m.l - m.r)).tickFormat("")).call((g) => g.select(".domain").remove());
    svg.append("g").attr("class", "axis").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat(ct.unit === "year" ? d3.format("d") : d3.format("~s")));
    svg.append("g").attr("class", "axis").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(yS).ticks(4).tickFormat(d3.format("~s")));
    svg.append("text").attr("class", "axlab").attr("x", (m.l + W - m.r) / 2).attr("y", H - 6).attr("text-anchor", "middle").text(ct.x_label);
    svg.append("text").attr("class", "axlab").attr("transform", `translate(12,${(H - m.b + m.t) / 2}) rotate(-90)`)
      .attr("text-anchor", "middle").text(ct.y_label.length > 46 ? ct.y_label.slice(0, 44) + "…" : ct.y_label);
    const isCD = ct.unit === "community district";
    svg.append("g").selectAll("circle").data(pts).join("circle")
      .attr("cx", (p) => x(p.x)).attr("cy", (p) => yS(p.y)).attr("r", 0).attr("fill", color).attr("fill-opacity", 0.85)
      .attr("stroke", "#0d121a").attr("stroke-width", 1.5)
      .on("mousemove", function (e, p) {
        d3.select(this).attr("r", 7).attr("fill-opacity", 1);
        showTip(`<b>${esc(p.name || p.id)}</b><em>${esc(ct.x_label)}: ${(+p.x).toLocaleString("en-US", { maximumFractionDigits: 1 })}</em>
          <em>${esc(ct.y_label)}: ${(+p.y).toLocaleString("en-US", { maximumFractionDigits: 1 })}</em>`, e.clientX, e.clientY);
        if (isCD && p.id !== hlId) { setState(hlId, { hl: false }); hlId = p.id; setState(hlId, { hl: true }); }
      })
      .on("mouseleave", function () { d3.select(this).attr("r", 4.5).attr("fill-opacity", 0.85); hideTip(); setState(hlId, { hl: false }); hlId = null; })
      .on("click", (e, p) => isCD && openDistrict(p.id))
      .transition().duration(600).delay((_, i) => i * 8).attr("r", 4.5);
  }

  // ---------- footer ----------
  const cc = GT.meta.claims_collection;
  $("#underlay-link").href = cc.url;
  $("#foot").innerHTML = [
    `<span>Verdicts: <a href="${cc.url}" target="_blank" rel="noopener">${cc.owner}/${cc.slug}</a></span>`,
    ...GT.meta.inputs.map((i) => `<a href="${i.url}" target="_blank" rel="noopener" title="${i.hash}">${i.collection}@${i.semver} · ${shortHash(i.hash)}</a>`),
    `<span>${esc(GT.meta.graph_citation.split(". http")[0])} · CC BY-NC 4.0</span>`,
  ].join(`<span class="sep">|</span>`);

  renderLedger();

  // ---------- opening: whose evidence ----------
  const intro = $("#intro"), H = GT.headline;
  const REGIONS = ["NYC", "US", "Europe", "China", "East Asia other", "Australia", "Other place", "No place stated", "Animal studies"];
  const RNAME = { NYC: "New York City", "East Asia other": "Other East Asia", "Other place": "Elsewhere", "No place stated": "No place stated",
    "Animal studies": "Animals" };
  let timers = [];
  function playIntro() {
    timers.forEach(clearTimeout); timers = [];
    intro.classList.remove("gone");
    $("#intro-head").classList.remove("nyc");
    $("#intro-line").textContent = "studies on heat and health in the research graph";
    $("#intro-stats").innerHTML = [
      [H.studies_name_low_income, "name low-income people"],
      [H.studies_name_black_or_hispanic, "name Black or Hispanic people"],
      [H.studies_non_human, "are animal studies"],
      [H.studies_no_place, "don't say where"],
    ].map(([n, t]) => `<div><b>${num(n)}</b><span>${t}</span></div>`).join("");
    const outs = [...GT.outcomes].sort((a, b) => b.studies - a.studies).filter((o) =>
      ["Heart disease", "Asthma", "Hypertension", "Type 2 diabetes", "Depression", "Heat illness"].includes(o.outcome));
    const maxS = d3.max(outs, (o) => o.studies);
    $("#intro-out").innerHTML = `<h4>Beyond heat: studies in the graph vs studies about New York</h4>` + outs.map((o) =>
      `<div class="orow"><span>${esc(o.outcome)}</span><div class="bar" style="width:${Math.max(3, (100 * o.studies) / maxS)}%"><i></i></div>
       <em>${num(o.studies)} · <b>${o.nyc} NYC</b></em></div>`).join("");
    $("#intro-out").classList.remove("on"); $("#go").classList.remove("on");

    // dots: one per study, grouped in blocks by region
    const svg = d3.select("#dots"); svg.selectAll("*").remove();
    const rows = 9, pitch = 10, gap = 26, groups = d3.group(GT.evidence_dots, (d) => d.region);
    let x0 = 0;
    const placed = [];
    const blocks = REGIONS.filter((r) => groups.has(r)).map((r) => {
      const list = groups.get(r), cols = Math.ceil(list.length / rows), b = { r, x: x0, w: cols * pitch, n: list.length };
      list.forEach((d, i) => placed.push({ ...d, cx: x0 + Math.floor(i / rows) * pitch + pitch / 2, cy: 10 + (i % rows) * pitch + pitch / 2 }));
      x0 += cols * pitch + gap;
      return b;
    });
    const off = (1180 - (x0 - gap)) / 2;
    const g = svg.append("g").attr("transform", `translate(${off},0)`);
    const dots = g.selectAll("circle").data(placed).join("circle").attr("cx", (d) => d.cx).attr("cy", (d) => d.cy).attr("r", 3.1)
      .attr("fill", (d) => (d.region === "Animal studies" ? "#64748b" : "#cbd5e1")).attr("opacity", 0);
    blocks.forEach((b) => {
      g.append("text").attr("class", "lab" + (b.r === "NYC" ? " hot" : "")).attr("x", b.x + b.w / 2).attr("y", rows * pitch + 32).text(RNAME[b.r] || b.r);
      g.append("text").attr("class", "lab n" + (b.r === "NYC" ? " hot" : "")).attr("x", b.x + b.w / 2).attr("y", rows * pitch + 47).text(num(b.n));
    });
    dots.transition().duration(300).delay((_, i) => i * 1.6).attr("opacity", 1);
    d3.select("#intro-count").transition().duration(1300).tween("t", function () {
      const it = d3.interpolateRound(0, H.studies_total);
      return (t) => (this.textContent = num(it(t)));
    });
    timers.push(setTimeout(() => {
      dots.transition().duration(900).attr("opacity", (d) => (d.region === "NYC" ? 1 : 0.16))
        .attr("r", (d) => (d.region === "NYC" ? 5.2 : 3.1)).attr("fill", (d) => (d.region === "NYC" ? "#ffc34d" : "#64748b"))
        .style("filter", (d) => (d.region === "NYC" ? "drop-shadow(0 0 6px #ffc34d)" : null));
      $("#intro-head").classList.add("nyc");
      d3.select("#intro-count").interrupt();
      $("#intro-count").textContent = num(H.studies_nyc);
      $("#intro-line").textContent = `are about New York City.`;
    }, 2600));
    document.querySelectorAll("#intro-stats div").forEach((d, i) => timers.push(setTimeout(() => d.classList.add("on"), 4000 + i * 350)));
    timers.push(setTimeout(() => $("#intro-out").classList.add("on"), 5700));
    timers.push(setTimeout(() => $("#go").classList.add("on"), 6400));
  }
  function enterMap() {
    timers.forEach(clearTimeout);
    intro.classList.add("gone");
    if (mapReady) map.easeTo({ zoom: 9.9, bearing: -18, pitch: 42, duration: 2400 });
  }
  $("#go").onclick = enterMap;
  $("#skip").onclick = enterMap;
  $("#replay").onclick = playIntro;
  document.addEventListener("keydown", (e) => { if (e.key === "Enter" && !intro.classList.contains("gone")) enterMap(); });
  playIntro();
})();
