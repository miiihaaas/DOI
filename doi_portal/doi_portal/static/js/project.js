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
