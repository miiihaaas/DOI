/* =====================================================================
   DOI Portal — public site interactions
   - Custom cursor ball (desktop only, doi.rs style)
   - Animated stat counters (count-up on scroll into view)
   - Scroll reveal for [data-reveal] elements
   - Lenis smooth scroll (+ GSAP ScrollTrigger sync when available)
   All features degrade gracefully if a CDN library is unavailable.
   ===================================================================== */
(function () {
  "use strict";

  var prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var isDesktop = window.matchMedia("(min-width: 1025px) and (hover: hover) and (pointer: fine)").matches;

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  /* ---------------------------------------------------------------
     1. Custom cursor ball
  --------------------------------------------------------------- */
  function initCursorBall() {
    if (!isDesktop || prefersReduced) return;

    var ball = document.createElement("div");
    ball.id = "cursor-ball";
    ball.setAttribute("aria-hidden", "true");
    document.body.appendChild(ball);
    document.body.classList.add("has-cursor-ball");

    var mouseX = window.innerWidth / 2;
    var mouseY = window.innerHeight / 2;
    var ballX = mouseX;
    var ballY = mouseY;
    var visible = false;

    document.addEventListener("mousemove", function (e) {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (!visible) {
        visible = true;
        ball.style.opacity = "1";
      }
    });

    document.addEventListener("mouseleave", function () {
      ball.style.opacity = "0";
      visible = false;
    });

    var interactiveSel = 'a, button, input, textarea, select, label, [role="button"], .stat-card, .publication-card, .quick-link-card, .publisher-card';
    document.addEventListener("mouseover", function (e) {
      if (e.target.closest(interactiveSel)) ball.classList.add("is-active");
    });
    document.addEventListener("mouseout", function (e) {
      if (e.target.closest(interactiveSel)) ball.classList.remove("is-active");
    });

    (function raf() {
      // Smooth trailing (lerp)
      ballX += (mouseX - ballX) * 0.18;
      ballY += (mouseY - ballY) * 0.18;
      ball.style.transform = "translate(" + ballX + "px, " + ballY + "px) translate(-50%, -50%)";
      window.requestAnimationFrame(raf);
    })();
  }

  /* ---------------------------------------------------------------
     2. Animated counters
  --------------------------------------------------------------- */
  function animateCounter(el) {
    var raw = (el.getAttribute("data-count-to") || el.textContent || "").trim();
    var target = parseInt(raw.replace(/[^\d]/g, ""), 10);
    if (isNaN(target)) return;

    if (prefersReduced) {
      el.textContent = target.toLocaleString("sr-RS");
      return;
    }

    var duration = 1400;
    var startTime = null;

    function easeOutCubic(t) {
      return 1 - Math.pow(1 - t, 3);
    }

    function step(ts) {
      if (startTime === null) startTime = ts;
      var progress = Math.min((ts - startTime) / duration, 1);
      var value = Math.floor(easeOutCubic(progress) * target);
      el.textContent = value.toLocaleString("sr-RS");
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        el.textContent = target.toLocaleString("sr-RS");
      }
    }
    window.requestAnimationFrame(step);
  }

  function initCounters() {
    var counters = document.querySelectorAll(".stat-number, [data-counter]");
    if (!counters.length) return;

    if (!("IntersectionObserver" in window)) {
      counters.forEach(animateCounter);
      return;
    }

    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });

    counters.forEach(function (c) { io.observe(c); });
  }

  /* ---------------------------------------------------------------
     3. Scroll reveal
  --------------------------------------------------------------- */
  function initReveal() {
    var items = document.querySelectorAll("[data-reveal]");
    if (!items.length) return;

    if (prefersReduced || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }

    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });

    items.forEach(function (el) { io.observe(el); });
  }

  /* ---------------------------------------------------------------
     4. Lenis smooth scroll (+ GSAP ScrollTrigger sync)
  --------------------------------------------------------------- */
  function initLenis() {
    if (prefersReduced || typeof window.Lenis === "undefined") return;

    var lenis = new window.Lenis({
      duration: 1.1,
      easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
      smoothWheel: true
    });

    var hasGsap = typeof window.gsap !== "undefined" && typeof window.ScrollTrigger !== "undefined";
    if (hasGsap) {
      lenis.on("scroll", window.ScrollTrigger.update);
      window.gsap.ticker.add(function (time) { lenis.raf(time * 1000); });
      window.gsap.ticker.lagSmoothing(0);
    } else {
      (function raf(time) {
        lenis.raf(time);
        window.requestAnimationFrame(raf);
      })();
    }

    // Anchor links use Lenis
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(function (link) {
      link.addEventListener("click", function (e) {
        var id = link.getAttribute("href");
        var target = document.querySelector(id);
        if (target) {
          e.preventDefault();
          lenis.scrollTo(target, { offset: -90 });
        }
      });
    });
  }

  /* ---------------------------------------------------------------
     5. Split word reveal for headings (doi.rs SplitText-style)
  --------------------------------------------------------------- */
  function initSplitReveal() {
    if (prefersReduced) return;
    var gsap = window.gsap;
    var ScrollTrigger = window.ScrollTrigger;
    if (!gsap || !ScrollTrigger) return;
    gsap.registerPlugin(ScrollTrigger);

    var selector = ".hero-content h1, .portal-page-header .page-title";
    var els = document.querySelectorAll(selector);

    els.forEach(function (el) {
      // Only split plain-text headings (no child elements) and only once.
      if (el.dataset.splitDone || el.children.length) return;

      var tokens = el.textContent.split(/(\s+)/);
      el.textContent = "";
      var words = [];
      tokens.forEach(function (tok) {
        if (tok.trim() === "") {
          el.appendChild(document.createTextNode(tok));
          return;
        }
        var span = document.createElement("span");
        span.className = "reveal-word";
        span.textContent = tok;
        el.appendChild(span);
        words.push(span);
      });
      el.dataset.splitDone = "1";

      gsap.set(words, { yPercent: 45, opacity: 0 });
      gsap.to(words, {
        yPercent: 0,
        opacity: 1,
        duration: 0.6,
        ease: "power3.out",
        stagger: 0.035,
        scrollTrigger: { trigger: el, start: "top 90%", once: true }
      });
    });
  }

  /* ---------------------------------------------------------------
     6. Animated connected-dots background (site-wide, subtle)
  --------------------------------------------------------------- */
  function makeConstellation(canvas, opts) {
    if (!canvas || prefersReduced) return;
    var ctx = canvas.getContext("2d");
    if (!ctx) return;
    opts = opts || {};
    var dot = opts.dot || "92, 180, 106";
    var line = opts.line || "3, 51, 51";
    var mouseLine = opts.mouseLine || "92, 180, 106";
    var sizeEl = opts.sizeEl || null;   // element to size to; null = viewport
    var w = 0, h = 0, dpr = 1, particles = [], raf = null;
    var mouse = { x: null, y: null };

    function vw() { return sizeEl ? sizeEl.clientWidth : window.innerWidth; }
    function vh() { return sizeEl ? sizeEl.clientHeight : window.innerHeight; }
    function small() { return window.matchMedia("(max-width: 768px)").matches; }
    function count() {
      var cap = sizeEl ? 55 : 90;
      return small() ? Math.min(sizeEl ? 22 : 30, Math.round(vw() / 16)) : Math.min(cap, Math.round(vw() / 20));
    }
    function maxDist() { return (small() ? 120 : 160) * dpr; }

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      var pw = vw() || 1, ph = vh() || 1;
      w = canvas.width = Math.floor(pw * dpr);
      h = canvas.height = Math.floor(ph * dpr);
      canvas.style.width = pw + "px";
      canvas.style.height = ph + "px";
    }

    function seed() {
      particles = [];
      var n = count();
      for (var i = 0; i < n; i++) {
        particles.push({
          x: Math.random() * w, y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.32 * dpr,
          vy: (Math.random() - 0.5) * 0.32 * dpr,
          r: (Math.random() * 1.5 + 0.8) * dpr
        });
      }
    }

    function frame() {
      var md = maxDist();
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(" + dot + ", 0.75)";
        ctx.fill();
        for (var j = i + 1; j < particles.length; j++) {
          var q = particles[j];
          var dx = p.x - q.x, dy = p.y - q.y, d = Math.sqrt(dx * dx + dy * dy);
          if (d < md) {
            ctx.strokeStyle = "rgba(" + line + ", " + ((1 - d / md) * 0.34) + ")";
            ctx.lineWidth = dpr;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
          }
        }
        if (mouse.x !== null) {
          var mx = mouse.x * dpr, my = mouse.y * dpr;
          var dmx = p.x - mx, dmy = p.y - my, dm = Math.sqrt(dmx * dmx + dmy * dmy);
          var reach = md * 1.5;
          if (dm < reach) {
            ctx.strokeStyle = "rgba(" + mouseLine + ", " + ((1 - dm / reach) * 0.55) + ")";
            ctx.lineWidth = dpr;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y); ctx.lineTo(mx, my); ctx.stroke();
          }
        }
      }
      raf = window.requestAnimationFrame(frame);
    }

    resize(); seed();
    var rt;
    window.addEventListener("resize", function () {
      window.clearTimeout(rt);
      rt = window.setTimeout(function () { resize(); seed(); }, 200);
    });
    if (!small()) {
      window.addEventListener("mousemove", function (e) {
        if (sizeEl) {
          var r = sizeEl.getBoundingClientRect();
          if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
            mouse.x = null; mouse.y = null; return;
          }
          mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
        } else {
          mouse.x = e.clientX; mouse.y = e.clientY;
        }
      });
      window.addEventListener("mouseout", function () { mouse.x = null; mouse.y = null; });
    }
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { if (raf) { window.cancelAnimationFrame(raf); raf = null; } }
      else if (!raf) { raf = window.requestAnimationFrame(frame); }
    });
    frame();
  }

  function initConstellation() {
    // Site-wide subtle background on the light page
    makeConstellation(document.getElementById("bg-constellation"), {
      dot: "92, 180, 106", line: "3, 51, 51", mouseLine: "92, 180, 106"
    });
    // Hero-local network on the dark hero (light colors for contrast)
    makeConstellation(document.getElementById("hero-constellation"), {
      dot: "255, 255, 255", line: "104, 204, 108", mouseLine: "255, 255, 255",
      sizeEl: document.querySelector(".hero-section")
    });
  }

  onReady(function () {
    initCursorBall();
    initCounters();
    initReveal();
    initLenis();
    initSplitReveal();
  });
})();
