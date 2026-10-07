/* Project specific Javascript goes here. */

/**
 * Double-space warning for title/subtitle fields.
 * Targets inputs/textareas with data-check-spaces="true" attribute.
 */
document.addEventListener('DOMContentLoaded', function () {
  var fields = document.querySelectorAll('input[data-check-spaces="true"], textarea[data-check-spaces="true"]');

  fields.forEach(function (field) {
    field.addEventListener('input', function () {
      checkDoubleSpaces(field);
    });
    // Check on initial load in case of pre-filled values
    checkDoubleSpaces(field);
  });

  function checkDoubleSpaces(field) {
    var hasDoubleSpaces = /  +/.test(field.value);
    var warning = field.nextElementSibling;
    var isWarning = warning && warning.classList.contains('double-space-warning');

    if (hasDoubleSpaces) {
      if (!isWarning) {
        var warningEl = document.createElement('div');
        warningEl.className = 'double-space-warning';
        warningEl.innerHTML =
          '<i class="bi bi-exclamation-triangle"></i>' +
          '<span>Naslov sadrži duple razmake</span>' +
          '<button type="button" class="fix-spaces-btn">Ispravi</button>';
        field.insertAdjacentElement('afterend', warningEl);

        warningEl.querySelector('.fix-spaces-btn').addEventListener('click', function () {
          field.value = field.value.replace(/ {2,}/g, ' ');
          // Trigger input event so other listeners (e.g. Alpine.js) react
          field.dispatchEvent(new Event('input', { bubbles: true }));
        });
      }
    } else {
      if (isWarning) {
        warning.remove();
      }
    }
  }
});

/**
 * Searchable selects (Tom Select).
 *
 * One central initialiser for the dashboard and the public pages:
 *
 *   initSearchableSelects(root)
 *
 * enhances every `select.form-select` at or below `root` (default: document) that
 *   - is not enhanced yet,
 *   - is single-value (no `multiple`, no `size` > 1),
 *   - is not opted out with `data-no-search` (on the select or any ancestor), and
 *   - has at least 6 real options (an option with an empty value is a placeholder
 *     and is not counted) OR carries `data-search="true"`.
 * Everything else stays a native `.form-select`.
 *
 * It runs on DOMContentLoaded and on every HTMX swap (`htmx:load`), always by
 * element, never by id, so partials with duplicate ids are fine. Widgets whose
 * select was swapped out are destroyed (`htmx:beforeCleanupElement`).
 *
 * The original <select> stays in the DOM and in the form: it is submitted as
 * before, and Tom Select dispatches bubbling `input` + `change` events on it,
 * so `hx-trigger="change"`, `onchange="..."`, `addEventListener('change')` and
 * `form[data-autosubmit]` keep working unchanged.
 *
 * If a script changes an enhanced select behind the widget's back, call
 * `syncSearchableSelect(select)` (a `change` event on the select does it too).
 *
 * If the library did not load (CDN down) nothing happens: selects stay native.
 */
(function () {
  'use strict';

  var MIN_OPTIONS = 6;
  var SELECTOR = 'select.form-select';
  var live = [];        // enhanced <select> elements, for leak sweeping
  var openInstance = null;

  function hasLibrary() {
    return typeof window.TomSelect === 'function';
  }

  function realOptionCount(select) {
    var n = 0;
    for (var i = 0; i < select.options.length; i++) {
      if (select.options[i].value !== '') { n++; }
    }
    return n;
  }

  function shouldEnhance(select) {
    if (select.tomselect) { return false; }
    if (select.multiple || select.size > 1) { return false; }
    if (select.closest('[data-no-search]')) { return false; }
    if (select.getAttribute('data-search') === 'true') { return true; }
    return realOptionCount(select) >= MIN_OPTIONS;
  }

  /* Markup restored from the HTMX history cache (or copied as HTML) can contain
     the widget's DOM without a live instance. Strip it so the select can be
     enhanced again instead of ending up with two controls. */
  function removeStaleMarkup(root) {
    var scope = root.querySelectorAll ? root : document;
    var i;
    var stale = scope.querySelectorAll('select.tomselected, select.ts-hidden-accessible');
    for (i = 0; i < stale.length; i++) {
      var select = stale[i];
      if (select.tomselect) { continue; }
      var next = select.nextElementSibling;
      if (next && next.classList.contains('ts-wrapper')) { next.remove(); }
      select.classList.remove('tomselected', 'ts-hidden-accessible');
      if (select.getAttribute('tabindex') === '-1') { select.removeAttribute('tabindex'); }
      if (select.id) {
        var labels = document.querySelectorAll('label[for="' + cssEscape(select.id + '-ts-control') + '"]');
        for (var j = 0; j < labels.length; j++) {
          if (!document.getElementById(select.id + '-ts-control')) {
            labels[j].setAttribute('for', select.id);
          }
        }
      }
    }
    var dropdowns = document.querySelectorAll('body > .ts-dropdown');
    for (i = 0; i < dropdowns.length; i++) {
      if (!dropdowns[i].__searchableSelect) { dropdowns[i].remove(); }
    }
  }

  function cssEscape(value) {
    return window.CSS && window.CSS.escape ? window.CSS.escape(value) : value.replace(/["\\]/g, '\\$&');
  }

  /* Mirror state that other scripts (Alpine, HTMX settling, validation code)
     change on the original select after the widget was built. */
  function mirrorState(select) {
    var ts = select.tomselect;
    if (!ts) { return; }
    if (!select.classList.contains('ts-hidden-accessible')) {
      // HTMX attribute settling can rewrite the class attribute
      select.classList.add('tomselected', 'ts-hidden-accessible');
    }
    ['is-invalid', 'is-valid'].forEach(function (cls) {
      ts.wrapper.classList.toggle(cls, select.classList.contains(cls));
    });
    if (select.disabled !== ts.isDisabled) {
      if (select.disabled) { ts.disable(); } else { ts.enable(); }
    }
  }

  /* Several HTMX partials can be open at once with the same field id
     (id_contributor_role, id_relationship_type, per-chapter forms). Tom Select
     names its text input "<id>-ts-control" and points the label at it, so
     duplicates would send every label click to the first widget. Give later
     duplicates their own control id and re-point the label of their own form. */
  var controlSeq = 0;
  function uniquifyControlId(select, ts) {
    var input = ts.control_input;
    if (!input || !input.id) { return; }
    var baseId = input.id;
    var first = document.getElementById(baseId);
    if (!first || first === input) { return; }
    var newId = baseId + '-' + (++controlSeq);
    input.id = newId;
    var form = select.form;
    if (!form || !select.id) { return; }
    var selectors = ['label[for="' + cssEscape(baseId) + '"]', 'label[for="' + cssEscape(select.id) + '"]'];
    var labels = form.querySelectorAll(selectors.join(','));
    for (var i = 0; i < labels.length; i++) {
      labels[i].setAttribute('for', newId);
      if (labels[i].id) { input.setAttribute('aria-labelledby', labels[i].id); }
    }
  }

  function enhance(select) {
    var ts;
    try {
      ts = new window.TomSelect(select, {
        maxOptions: null,            // list everything (the default cuts at 50)
        allowEmptyOption: true,      // "---------" / "Svi ..." stays a normal, selectable option
        dropdownParent: 'body',      // not clipped by .table-responsive, cards or modals
        selectOnTab: false,
        closeAfterSelect: true,
        render: {
          no_results: function () {
            return '<div class="no-results">Nema rezultata</div>';
          }
        }
      });
    } catch (err) {
      if (window.console && console.warn) { console.warn('Searchable select not initialised', err); }
      return null;
    }

    /* Backspace/Delete must not remove the chosen value: a native select can
       never be emptied that way, and required selects without an empty option
       would otherwise submit nothing. */
    ts.hook('instead', 'deleteSelection', function () { return false; });

    /* Enter on a closed control opens the list instead of submitting the form
       (a native select never submits on Enter). Capture phase: Tom Select's own
       handler closes the list on Enter, so the state must be read before it. */
    ts.wrapper.addEventListener('keydown', function (event) {
      if ((event.key === 'Enter' || event.keyCode === 13) && !ts.isOpen && !ts.isLocked) {
        event.preventDefault();
        event.stopPropagation();
        ts.open();
      }
    }, true);

    uniquifyControlId(select, ts);
    ts.dropdown.__searchableSelect = true;
    ts.dropdown.classList.add('searchable-select-dropdown');

    /* While the user types, hide the current value so only the query shows. */
    ts.on('type', function (query) {
      ts.wrapper.classList.toggle('is-typing', !!query);
    });
    ['blur', 'item_add', 'dropdown_close'].forEach(function (name) {
      ts.on(name, function () { ts.wrapper.classList.remove('is-typing'); });
    });
    ts.on('dropdown_open', function () {
      openInstance = ts;
      // The dropdown is outside the form: give it the control's text size (.form-select-sm, public pages)
      var size = window.getComputedStyle ? window.getComputedStyle(ts.control).fontSize : '';
      if (size) { ts.dropdown.style.fontSize = size; }
    });
    ts.on('dropdown_close', function () { if (openInstance === ts) { openInstance = null; } });

    if (typeof MutationObserver === 'function') {
      var observer = new MutationObserver(function () { mirrorState(select); });
      observer.observe(select, { attributes: true, attributeFilter: ['class', 'disabled'] });
      ts.on('destroy', function () { observer.disconnect(); });
    }
    ts.on('destroy', function () {
      if (openInstance === ts) { openInstance = null; }
    });

    live.push(select);
    return ts;
  }

  function destroy(select) {
    var ts = select.tomselect;
    if (ts) {
      try { ts.destroy(); } catch (err) { /* already gone */ }
    }
    var i = live.indexOf(select);
    if (i !== -1) { live.splice(i, 1); }
  }

  /* Destroy widgets whose select left the document without HTMX telling us. */
  function sweep() {
    for (var i = live.length - 1; i >= 0; i--) {
      if (!live[i].isConnected || !live[i].tomselect) { destroy(live[i]); }
    }
  }

  function initSearchableSelects(root) {
    if (!hasLibrary()) { return; }
    root = root || document;
    if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) { return; }
    sweep();
    removeStaleMarkup(root);
    var selects = [];
    if (root.matches && root.matches(SELECTOR)) { selects.push(root); }
    if (root.querySelectorAll) {
      Array.prototype.push.apply(selects, root.querySelectorAll(SELECTOR));
    }
    selects.forEach(function (select) {
      if (shouldEnhance(select)) { enhance(select); }
    });
  }

  function syncSearchableSelect(select) {
    var ts = select && select.tomselect;
    if (!ts) { return; }
    ts.sync();
    mirrorState(select);
  }

  window.initSearchableSelects = initSearchableSelects;
  window.syncSearchableSelect = syncSearchableSelect;

  function guarded(fn) {
    return function (event) {
      try { fn(event); } catch (err) {
        if (window.console && console.warn) { console.warn('Searchable select', err); }
      }
    };
  }

  /* project.js is loaded with `defer`, i.e. before DOMContentLoaded. Waiting for
     the event lets HTMX (loaded earlier) process the page first. */
  if (document.readyState === 'complete') {
    guarded(function () { initSearchableSelects(document); })();
  } else {
    document.addEventListener('DOMContentLoaded', guarded(function () { initSearchableSelects(document); }));
  }

  /* HTMX: `htmx:load` fires on every newly inserted element (after attribute
     settling), for innerHTML, outerHTML and out-of-band swaps alike. */
  document.addEventListener('htmx:load', guarded(function (event) {
    initSearchableSelects(event.target);
  }));
  document.addEventListener('htmx:historyRestore', guarded(function () {
    initSearchableSelects(document);
  }));

  /* HTMX is about to drop an element. The event also fires for elements that
     stay in the page (hx-disable), so only destroy once the select is gone. */
  document.addEventListener('htmx:beforeCleanupElement', function (event) {
    var el = event.target;
    if (!el || !el.tomselect) { return; }
    window.setTimeout(function () {
      if (!el.isConnected) { destroy(el); }
    }, 0);
  });

  /* A script changed the select and announced it with `change`: follow it. */
  document.addEventListener('change', guarded(function (event) {
    var el = event.target;
    var ts = el && el.tomselect;
    if (ts && el.tagName === 'SELECT' && el.value !== ts.getValue()) {
      ts.setValue(el.value, true);
    }
  }), true);

  /* <button type="reset">: the browser resets the select after this event. */
  document.addEventListener('reset', function (event) {
    var form = event.target;
    window.setTimeout(guarded(function () {
      if (!form || !form.querySelectorAll) { return; }
      Array.prototype.forEach.call(form.querySelectorAll('select'), syncSearchableSelect);
    }), 0);
  });

  /* The dropdown lives in <body>; keep it glued to its control when a scroll
     container other than the window moves (modal body, .table-responsive). */
  document.addEventListener('scroll', function (event) {
    if (!openInstance) { return; }
    if (event.target && event.target.nodeType === 1 && openInstance.dropdown.contains(event.target)) { return; }
    openInstance.positionDropdown();
  }, true);
})();
