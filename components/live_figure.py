"""
Kidashi ABM -- FIG 01 Live Figure (golden-standard rebuild)
=============================================================

Standalone animated hero visualization for the KidashiSim landing
page: farm clusters, Kidashi trust-circle liquidity, the Kano
farmgate market, downstream aggregation/export, and live agent-state
dynamics (stable / fintech-supported / vulnerable / distress-sale) on
an HTML canvas embedded via st.iframe.

Visual bridge to GROCERYsim's shelf metaphor:
    reactive shelves    -> reactive market crates       (crates[])
    shopper archetypes  -> farmer agent states           (stateColor)
    restock pulses      -> Kidashi credit pulses into
                            trust-circles                 (pulses[])

Usage
-----
    from components.live_figure import render_kidashi_live_figure

    render_kidashi_live_figure(
        farmers=54, fintech_rate=0.41, shock_regime="baseline",
        maize_price=310_000, tomato_price=420_000, height=470,
    )
"""

from __future__ import annotations

import json

import streamlit as st

HTML_TEMPLATE = r"""<div class="kf-figure">
  <canvas id="kfCanvas"></canvas>
</div>
<div class="kf-footer">
  <span class="kf-tag">FIG 01</span>
  <p class="kf-caption">Smallholder agents move between farm clusters, Kidashi trust-circles and the Kano market, liquidity pulses ease distress-sale pressure as climate and trade shocks pass through the chain.</p>
</div>

<style>
  * {
    box-sizing: border-box;
  }

  html,
  body {
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: transparent;
  }

  .kf-figure {
    position: relative;
    width: 100%;
    height: __HEIGHT__px;
    border-radius: 10px;
    border: 1px solid rgba(126, 223, 224, 0.30);
    background:
      radial-gradient(circle at 20% 15%, rgba(0, 212, 255, 0.09), transparent 32%),
      linear-gradient(180deg, #0b3a40 0%, #082a30 100%);
    box-shadow:
      0 24px 60px rgba(0, 0, 0, 0.35),
      inset 0 0 34px rgba(0, 212, 255, 0.04);
    overflow: hidden;
  }

  #kfCanvas {
    width: 100%;
    height: 100%;
    display: block;
  }

  .kf-footer {
    min-height: 58px;
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.72rem 0.85rem 0.65rem;
    margin-top: 0;
    border-top: 1px solid rgba(126, 223, 224, 0.16);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    overflow: visible;
  }

  .kf-tag {
    color: #7edfe0;
    font: 900 0.72rem ui-monospace, "Cascadia Code", Consolas, monospace;
    letter-spacing: 0.20em;
    flex-shrink: 0;
    padding-top: 0.08rem;
  }

  .kf-caption {
    margin: 0;
    color: rgba(220, 236, 235, 0.72);
    font-size: 0.80rem;
    line-height: 1.42;
    white-space: normal;
    overflow: visible;
    text-overflow: clip;
    max-width: 100%;
  }
</style>

<script>
(() => {
  const cfg = __CONFIG__;
  const canvas = document.getElementById("kfCanvas");
  const ctx = canvas.getContext("2d");

  let W = 0, H = 0, DPR = 1;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const C = {
    cyan: "#7edfe0",
    cyanStrong: "#00d4ff",
    cream: "#f3efe4",
    orange: "#eba654",
    gold: "#f2b84b",
    green: "#3fbd7a",
    red: "#ef4444",
    redSoft: "#ef6b55",
    purple: "#a78bfa",
    teal: "#2fa7ba",
    muted: "#8fb0b3"
  };

  function resize() {
    DPR = window.devicePixelRatio || 1;
    W = canvas.clientWidth;
    H = canvas.clientHeight;
    canvas.width = Math.floor(W * DPR);
    canvas.height = Math.floor(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  window.addEventListener("resize", resize);
  resize();

  function rand(a, b) { return a + Math.random() * (b - a); }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

  function roundRect(x, y, w, h, r, fill, stroke) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
    if (fill) ctx.fill();
    if (stroke) ctx.stroke();
  }

  function layout() {
    return {
      farm:       { x: W * 0.14, y: H * 0.58, r: clamp(H * 0.065, 20, 26) },
      credit:     { x: W * 0.32, y: H * 0.20, r: clamp(H * 0.048, 15, 19) },
      market:     { x: W * 0.55, y: H * 0.44, r: clamp(H * 0.062, 19, 25) },
      lagos:      { x: W * 0.76, y: H * 0.62, r: clamp(H * 0.050, 16, 20) },
      exportNode: { x: W * 0.91, y: H * 0.24, r: clamp(H * 0.040, 12, 15) }
    };
  }

  function curvePoint(a, b, bend, t) {
    const cx = (a.x + b.x) / 2;
    const cy = (a.y + b.y) / 2 + bend;
    return {
      x: (1 - t) * (1 - t) * a.x + 2 * (1 - t) * t * cx + t * t * b.x,
      y: (1 - t) * (1 - t) * a.y + 2 * (1 - t) * t * cy + t * t * b.y
    };
  }

  function drawCurve(a, b, bend, color, width, dash) {
    const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2 + bend;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.setLineDash(dash || []);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.quadraticCurveTo(cx, cy, b.x, b.y);
    ctx.stroke();
    ctx.restore();
  }

  // ---- shock regimes (mirrors KidashiModel's --shock flag) ----
  const REGIME = {
    BASELINE:         { weather: "LOW",  trade: "LOW",  climate: false, tradeShock: false },
    CLIMATE_STRESS:    { weather: "HIGH", trade: "LOW",  climate: true,  tradeShock: false },
    TRADE_DISRUPTION:  { weather: "LOW",  trade: "HIGH", climate: false, tradeShock: true },
    COMPOUND:           { weather: "HIGH", trade: "HIGH", climate: true,  tradeShock: true }
  };
  const regime = REGIME[cfg.shockRegime] || REGIME.BASELINE;

  // ---- trust circles: static ring near the farm node, positions recomputed live ----
  const CIRCLE_COUNT = 6;
  const circleState = Array.from({ length: CIRCLE_COUNT }, () => ({ flash: 0 }));

  function circlePos(i, farm) {
    const ang = (i / CIRCLE_COUNT) * Math.PI * 2 + 0.35;
    const rad = clamp(H * 0.16, 46, 72);
    return { x: farm.x + Math.cos(ang) * rad, y: farm.y + Math.sin(ang) * rad * 0.66, ang };
  }

  // ---- reactive market crates (GROCERYsim shelf metaphor, reinterpreted) ----
  const crates = [
    { crop: "MAIZE",    color: C.gold,    fill: rand(0.55, 0.9), flash: 0 },
    { crop: "SORGHUM",  color: "#c88a4a", fill: rand(0.55, 0.9), flash: 0 },
    { crop: "TOMATO",   color: C.redSoft, fill: rand(0.55, 0.9), flash: 0 }
  ];

  function triggerCrateFlash() {
    const c = crates[Math.floor(Math.random() * crates.length)];
    c.flash = 1;
    c.fill = clamp(c.fill - rand(0.03, 0.09), 0.12, 1);
    if (c.fill < 0.16) c.fill = rand(0.65, 0.95);
  }

  // ---- agents ----
  function pickState() {
    const p = Math.random();
    if (p < cfg.fintechRate) return "credit";
    if (p < cfg.fintechRate + 0.32) return "stable";
    if (p < 0.90) return "vulnerable";
    return "distress";
  }
  function stateColor(s) {
    if (s === "credit") return C.cyanStrong;
    if (s === "stable") return C.green;
    if (s === "vulnerable") return C.gold;
    return C.red;
  }

  const visibleFarmers = clamp(cfg.farmers, 26, 64);
  const farmers = Array.from({ length: visibleFarmers }, (_, i) => {
    const state = pickState();
    return {
      id: i,
      state,
      t: Math.random(),
      speed: state === "distress" ? rand(0.0034, 0.0050) : rand(0.0018, 0.0032),
      size: state === "distress" ? rand(4.0, 4.8) : rand(3.0, 4.0),
      wobble: rand(0, Math.PI * 2),
      glow: 0,
      trail: [],
      circleIdx: i % CIRCLE_COUNT
    };
  });

  const produce = Array.from({ length: 20 }, (_, i) => ({
    t: Math.random(),
    speed: rand(0.0020, 0.0040),
    leg: Math.random() < 0.7 ? "toLagos" : "toExport",
    color: i % 3 === 0 ? C.gold : i % 3 === 1 ? "#c88a4a" : C.redSoft
  }));

  const traders = Array.from({ length: 7 }, (_, i) => ({
    hub: i < 4 ? "market" : "lagos",
    ang: (i / 7) * Math.PI * 2,
    phase: rand(0, Math.PI * 2)
  }));

  const pulses = Array.from({ length: 9 }, () => ({
    t: Math.random(),
    speed: rand(0.0055, 0.0090),
    target: Math.floor(Math.random() * CIRCLE_COUNT),
    size: rand(2.2, 3.4)
  }));

  // ---- draw functions ----
  function drawBackground() {
    ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.strokeStyle = "rgba(126,223,224,0.045)";
    ctx.lineWidth = 1;
    const gap = 24;
    for (let x = 0; x <= W; x += gap) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    for (let y = 0; y <= H; y += gap) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    ctx.restore();

    const g = ctx.createRadialGradient(W * 0.22, H * 0.16, 0, W * 0.22, H * 0.16, Math.max(W, H) * 0.6);
    g.addColorStop(0, "rgba(0,212,255,0.06)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
  }

  function drawShock(now, L) {
    if (regime.climate) {
      ctx.save();
      ctx.strokeStyle = "rgba(242,184,75,0.09)";
      ctx.lineWidth = 1;
      const off = (now * 0.03) % 40;
      for (let x = -H; x < W + H; x += 26) {
        ctx.beginPath();
        ctx.moveTo(x + off, 0);
        ctx.lineTo(x + off - H * 0.35, H);
        ctx.stroke();
      }
      ctx.restore();
    }
    if (regime.tradeShock) {
      const cycle = (now * 0.00007) % 1;
      ctx.save();
      for (let i = 0; i < 3; i++) {
        ctx.strokeStyle = `rgba(239,107,85,${Math.max(0, 0.16 - i * 0.045 - cycle * 0.02)})`;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.arc(L.exportNode.x, L.exportNode.y, 26 + cycle * 140 + i * 22, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  function drawRoutes(now, L) {
    drawCurve(L.farm, L.market, -34, "rgba(163,184,204,0.22)", 1.3, [7, 9]);
    drawCurve(L.market, L.lagos, 30, "rgba(163,184,204,0.18)", 1.2, [7, 9]);
    drawCurve(L.lagos, L.exportNode, -30, "rgba(163,184,204,0.18)", 1.2, [7, 9]);
    const glow = 0.26 + Math.sin(now * 0.002) * 0.08;
    drawCurve(L.credit, L.farm, -8, `rgba(0,212,255,${glow})`, 1.7, null);
  }

  function drawCropPatches(farm) {
    const patches = [
      { dx: -8,  dy: -56, w: 50, h: 18, color: "rgba(242,184,75,0.24)", label: "MAIZE" },
      { dx: 40,  dy: -42, w: 56, h: 18, color: "rgba(200,138,74,0.24)", label: "SORGHUM" },
      { dx: -52, dy: -34, w: 50, h: 18, color: "rgba(239,107,85,0.22)", label: "TOMATO" }
    ];
    ctx.save();
    patches.forEach(p => {
      const x = farm.x + p.dx, y = farm.y + p.dy;
      ctx.fillStyle = p.color;
      ctx.strokeStyle = "rgba(255,255,255,0.10)";
      ctx.lineWidth = 1;
      roundRect(x, y, p.w, p.h, 5, true, true);
      ctx.fillStyle = "rgba(255,255,255,0.62)";
      ctx.font = "700 6.5px ui-monospace, Consolas, monospace";
      ctx.textAlign = "center";
      ctx.fillText(p.label, x + p.w / 2, y + p.h / 2 + 2.5);
    });
    ctx.restore();
  }

  function drawTrustCircles(now, farm) {
    circleState.forEach((c, i) => {
      c.flash *= 0.92;
      const pos = circlePos(i, farm);
      ctx.save();
      if (c.flash > 0.04) {
        const glowR = 14 + c.flash * 22;
        const g = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, glowR);
        g.addColorStop(0, `rgba(0,212,255,${0.32 * c.flash})`);
        g.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(pos.x, pos.y, glowR, 0, Math.PI * 2); ctx.fill();
      }
      ctx.strokeStyle = c.flash > 0.04 ? `rgba(0,212,255,${0.55 + c.flash * 0.4})` : "rgba(126,223,224,0.30)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(pos.x, pos.y, 12, 0, Math.PI * 2); ctx.stroke();
      for (let m = 0; m < 3; m++) {
        const a = (m / 3) * Math.PI * 2 + now * 0.00018;
        const mx = pos.x + Math.cos(a) * 7.5;
        const my = pos.y + Math.sin(a) * 7.5;
        ctx.fillStyle = c.flash > 0.04 ? C.cyanStrong : "rgba(220,236,235,0.55)";
        ctx.beginPath(); ctx.arc(mx, my, 1.5, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    });
  }

  function drawNode(node, color, label, sub, now, phase) {
    const breathe = 1 + Math.sin(now * 0.0022 + phase) * 0.045;
    const glowR = node.r * 2.5;
    ctx.save();
    const g = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, glowR);
    g.addColorStop(0, color + "55");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(node.x, node.y, glowR, 0, Math.PI * 2); ctx.fill();

    ctx.strokeStyle = color + "aa";
    ctx.lineWidth = 1.3;
    ctx.beginPath(); ctx.arc(node.x, node.y, node.r * breathe, 0, Math.PI * 2); ctx.stroke();

    ctx.fillStyle = "rgba(6,26,31,0.88)";
    ctx.beginPath(); ctx.arc(node.x, node.y, node.r * 0.66, 0, Math.PI * 2); ctx.fill();

    ctx.fillStyle = color;
    ctx.shadowBlur = 14; ctx.shadowColor = color;
    ctx.beginPath(); ctx.arc(node.x, node.y, 3.4, 0, Math.PI * 2); ctx.fill();
    ctx.shadowBlur = 0;

    ctx.textAlign = "center";
    ctx.fillStyle = "rgba(243,239,228,0.92)";
    ctx.font = "800 9px Inter, Arial";
    ctx.fillText(label, node.x, node.y + node.r + 18);
    ctx.fillStyle = "rgba(143,176,179,0.85)";
    ctx.font = "700 7.5px Inter, Arial";
    ctx.fillText(sub, node.x, node.y + node.r + 30);
    ctx.restore();
  }

  function drawMarketCrates(market) {
    const w = 38, h = 10, gap = 5;
    const totalH = crates.length * (h + gap) - gap;
    const startY = market.y - totalH / 2;
    crates.forEach((c, i) => {
      c.flash *= 0.90;
      const x = market.x + market.r + 14;
      const y = startY + i * (h + gap);
      ctx.save();
      ctx.fillStyle = "#0e3038";
      ctx.strokeStyle = c.flash > 0.05 ? `rgba(255,192,100,${0.5 + c.flash * 0.45})` : "rgba(126,223,224,0.22)";
      ctx.lineWidth = 1;
      roundRect(x, y, w, h, 2, true, true);
      ctx.fillStyle = c.flash > 0.05 ? "rgba(255,192,100,0.85)" : c.color;
      roundRect(x + 2, y + 2, (w - 4) * clamp(c.fill, 0, 1), h - 4, 1, true, false);
      ctx.restore();
    });
  }

  function drawTraders(now, L) {
    traders.forEach(t => {
      const hub = t.hub === "market" ? L.market : L.lagos;
      const r = hub.r * 1.55;
      const a = t.ang + Math.sin(now * 0.0005 + t.phase) * 0.15;
      const x = hub.x + Math.cos(a) * r, y = hub.y + Math.sin(a) * r;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(a * 0.25);
      ctx.fillStyle = "rgba(47,167,186,0.30)";
      ctx.strokeStyle = "rgba(0,212,255,0.55)";
      ctx.lineWidth = 1;
      roundRect(-4, -4, 8, 8, 2, true, true);
      ctx.restore();
    });
  }

  function drawProduce(L) {
    produce.forEach(p => {
      if (!reduced) p.t += p.speed;
      if (p.t > 1) { p.t = 0; p.leg = Math.random() < 0.7 ? "toLagos" : "toExport"; }
      const pt = p.leg === "toLagos"
        ? curvePoint(L.market, L.lagos, 30, p.t)
        : curvePoint(L.lagos, L.exportNode, -30, p.t);
      ctx.save();
      ctx.globalAlpha = 0.55;
      ctx.fillStyle = p.color;
      ctx.shadowBlur = 6; ctx.shadowColor = p.color;
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 2, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    });
  }

  function drawCreditPulses(now, L) {
    pulses.forEach(p => {
      if (!reduced) p.t += p.speed;
      if (p.t > 1) {
        p.t = 0;
        p.target = Math.floor(Math.random() * CIRCLE_COUNT);
        circleState[p.target].flash = 1;
        const pool = farmers.filter(f => f.circleIdx === p.target);
        const f = pool[Math.floor(Math.random() * pool.length)];
        if (f) {
          if (f.state === "distress" && Math.random() < 0.40) f.state = "vulnerable";
          else if (f.state === "vulnerable" && Math.random() < 0.32) f.state = "credit";
          f.glow = 1;
        }
      }
      const targetPos = circlePos(p.target, L.farm);
      const pt = curvePoint(L.credit, targetPos, 8, p.t);
      ctx.save();
      ctx.globalAlpha = 0.75;
      ctx.fillStyle = C.cyanStrong;
      ctx.shadowBlur = 16; ctx.shadowColor = C.cyanStrong;
      ctx.beginPath(); ctx.arc(pt.x, pt.y, p.size, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    });
  }

  function drawFarmers(now, L) {
    farmers.forEach(a => {
      if (!reduced) {
        const prevT = a.t;
        a.t += a.speed;
        if (a.t >= 1) a.t -= 1;
        if (prevT < 0.5 && a.t >= 0.5) {
          triggerCrateFlash();
          if (a.state === "distress") triggerCrateFlash();
          if ((regime.climate || regime.tradeShock) && Math.random() < 0.12) {
            a.state = Math.random() < 0.55 ? "vulnerable" : "distress";
          }
        }
        a.glow *= 0.93;
      }

      const localT = a.t < 0.5 ? a.t * 2 : (1 - a.t) * 2;
      const pt = curvePoint(L.farm, L.market, -34, localT);
      const y = pt.y + Math.sin(now * 0.003 + a.wobble) * 2;
      const color = stateColor(a.state);

      if (a.state === "distress") {
        a.trail.push({ x: pt.x, y });
        if (a.trail.length > 5) a.trail.shift();
      } else if (a.trail.length) {
        a.trail.length = 0;
      }

      if (a.trail.length) {
        ctx.save();
        a.trail.forEach((tp, idx) => {
          ctx.globalAlpha = ((idx + 1) / a.trail.length) * 0.16;
          ctx.fillStyle = C.red;
          ctx.beginPath(); ctx.arc(tp.x, tp.y, a.size * 0.65, 0, Math.PI * 2); ctx.fill();
        });
        ctx.restore();
      }

      ctx.save();
      if (a.glow > 0.03) {
        ctx.fillStyle = `rgba(0,212,255,${a.glow * 0.25})`;
        ctx.beginPath(); ctx.arc(pt.x, y, a.size + 11 * a.glow, 0, Math.PI * 2); ctx.fill();
      }
      if (a.state === "credit") {
        ctx.strokeStyle = "rgba(0,212,255,0.65)";
        ctx.lineWidth = 1;
        ctx.shadowBlur = 10; ctx.shadowColor = C.cyanStrong;
        ctx.beginPath(); ctx.arc(pt.x, y, a.size + 4, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.fillStyle = color;
      ctx.shadowBlur = a.state === "distress" ? 12 : 7;
      ctx.shadowColor = color;
      ctx.beginPath(); ctx.arc(pt.x, y, a.size, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    });
  }

  function drawHeaderText() {
    const distress = farmers.filter(f => f.state === "distress").length;
    const credit = farmers.filter(f => f.state === "credit").length;
    const uptake = Math.round((credit / farmers.length) * 100);

    ctx.save();
    ctx.font = "800 10px ui-monospace, Consolas, monospace";
    ctx.textAlign = "left";
    ctx.fillStyle = C.cyanStrong;
    ctx.fillText(`VALUE CHAIN LIVE \u00b7 ${farmers.length} FARMERS`, 14, 20);

    ctx.textAlign = "right";
    ctx.fillStyle = "rgba(224,244,244,0.75)";
    ctx.fillText(`DISTRESS \u00b7 ${String(distress).padStart(3, "0")}`, W - 14, 20);

    ctx.font = "700 9px ui-monospace, Consolas, monospace";
    ctx.textAlign = "left";
    ctx.fillStyle = "rgba(224,244,244,0.55)";
    ctx.fillText(`FINTECH UPTAKE \u00b7 ${uptake}%`, 14, 34);

    ctx.textAlign = "right";
    ctx.fillText(`${cfg.maizePrice} \u00b7 ${cfg.tomatoPrice}`, W - 14, 34);
    ctx.restore();
  }

  function drawLegend() {
    ctx.save();
    const items = [
      ["STABLE", C.green],
      ["CREDIT", C.cyanStrong],
      ["VULNERABLE", C.gold],
      ["DISTRESS", C.red]
    ];
    let x = 14;
    const y = H - 14;
    items.forEach(([label, color]) => {
      ctx.fillStyle = color;
      ctx.beginPath(); ctx.arc(x, y - 3, 3, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "rgba(224,244,244,0.72)";
      ctx.font = "800 7.5px ui-monospace, Consolas, monospace";
      ctx.textAlign = "left";
      ctx.fillText(label, x + 8, y);
      x += label.length * 6.4 + 26;
    });
    ctx.restore();
  }

  function drawRegimeBadge() {
    const label = cfg.shockRegime.replace(/_/g, " ");
    ctx.save();
    ctx.font = "800 7.5px ui-monospace, Consolas, monospace";
    const text = `${label} \u00b7 WX ${regime.weather} \u00b7 TRADE ${regime.trade}`;
    const tw = ctx.measureText(text).width;
    const pad = 8, bh = 18;
    const bw = tw + pad * 2;
    const bx = W - 14 - bw, by = H - 14 - bh;
    ctx.fillStyle = "rgba(5,20,25,0.55)";
    ctx.strokeStyle = (regime.climate || regime.tradeShock) ? "rgba(242,184,75,0.5)" : "rgba(63,189,122,0.5)";
    ctx.lineWidth = 1;
    roundRect(bx, by, bw, bh, 9, true, true);
    ctx.fillStyle = (regime.climate || regime.tradeShock) ? C.gold : C.green;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(text, bx + pad, by + bh / 2 + 1);
    ctx.textBaseline = "alphabetic";
    ctx.restore();
  }

  let frozenNow = null;
  function frame(now) {
    if (reduced) {
      if (frozenNow === null) frozenNow = now;
      now = frozenNow;
    }
    const L = layout();
    drawBackground();
    drawShock(now, L);
    drawRoutes(now, L);
    drawCropPatches(L.farm);
    drawTrustCircles(now, L.farm);
    drawNode(L.farm, C.green, "FARM CLUSTERS", "maize \u00b7 sorghum \u00b7 tomato", now, 0.2);
    drawNode(L.credit, C.cyanStrong, "KIDASHI CREDIT", "trust-circle liquidity", now, 1.6);
    drawNode(L.market, C.gold, "KANO MARKET", "farmgate price formation", now, 0.9);
    drawNode(L.lagos, C.teal, "LAGOS / PROCESSORS", "aggregation & clearing", now, 1.1);
    drawNode(L.exportNode, C.purple, "EXPORT LINK", "trade shock channel", now, 0.5);
    drawMarketCrates(L.market);
    drawTraders(now, L);
    drawProduce(L);
    drawCreditPulses(now, L);
    drawFarmers(now, L);
    drawHeaderText();
    drawLegend();
    drawRegimeBadge();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
</script>
"""

_VALID_REGIMES = {"BASELINE", "CLIMATE_STRESS", "TRADE_DISRUPTION", "COMPOUND"}


def render_kidashi_live_figure(
    *,
    farmers: int = 48,
    fintech_rate: float = 0.42,
    shock_regime: str = "baseline",
    maize_price: int = 310_000,
    tomato_price: int = 420_000,
    height: int = 470,
) -> None:
    """Render FIG 01 -- the Kidashi live value-chain figure.

    Parameters
    ----------
    farmers:
        Number of farmer agents represented (clamped to 26-64 on screen
        for legibility -- the header readout tracks that same clamped
        count, so it never over-claims what is actually on screen).
    fintech_rate:
        Share of farmers with active Kidashi credit (0-1). Drives the
        cyan-ringed "credit" agent state and trust-circle pulses.
    shock_regime:
        "baseline" | "climate_stress" | "trade_disruption" | "compound"
        -- matches KidashiModel's --shock flag directly.
    maize_price / tomato_price:
        Farmgate price in NGN/MT, formatted into the on-canvas ticker.
    height:
        Pixel height of the figure. Width is always 100% of container.
    """
    regime_key = shock_regime.strip().upper().replace("-", "_").replace(" ", "_")
    if regime_key not in _VALID_REGIMES:
        regime_key = "BASELINE"

    config = {
        "farmers": farmers,
        "fintechRate": fintech_rate,
        "shockRegime": regime_key,
        "maizePrice": f"\u20a6{maize_price/1000:.0f}k/MT",
        "tomatoPrice": f"\u20a6{tomato_price/1000:.0f}k/MT",
    }

    html = HTML_TEMPLATE.replace("__CONFIG__", json.dumps(config)).replace(
        "__HEIGHT__", str(height)
    )
    # NOTE: streamlit.components.v1.html was deprecated in 1.56.0 (removal
    # date 2026-06-01 has passed) -- st.iframe(html_string, ...) is the
    # direct replacement and renders identically (srcdoc-based iframe).
    st.iframe(html, height=height + 74, width="stretch")
