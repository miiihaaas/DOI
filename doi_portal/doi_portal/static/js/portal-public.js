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

  onReady(function () {
    initCursorBall();
    initCounters();
    initReveal();
    initLenis();
  });
})();
