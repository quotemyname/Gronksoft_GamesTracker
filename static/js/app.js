/* Gronksoft GamesTracker – client-side JavaScript */

document.addEventListener("DOMContentLoaded", function () {
  // -----------------------------------------------------------
  // Mobile menu toggle
  // -----------------------------------------------------------
  var menuToggle = document.getElementById("menuToggle");
  var mobileMenu = document.getElementById("mobileMenu");
  var menuOverlay = document.getElementById("menuOverlay");

  if (menuToggle) {
    menuToggle.addEventListener("click", function () {
      mobileMenu.classList.toggle("open");
      menuOverlay.classList.toggle("open");
    });
  }
  if (menuOverlay) {
    menuOverlay.addEventListener("click", function () {
      mobileMenu.classList.remove("open");
      menuOverlay.classList.remove("open");
    });
  }

  // -----------------------------------------------------------
  // Filter panel toggle
  // -----------------------------------------------------------
  var toggleFilters = document.getElementById("toggleFilters");
  var filterPanel = document.getElementById("filterPanel");

  if (toggleFilters && filterPanel) {
    // Auto-open if any filter is active
    var params = new URLSearchParams(window.location.search);
    var hasFilter = ["result", "army", "opponent", "scenario", "event", "date_from", "date_to"].some(function (k) {
      return params.get(k);
    });
    if (hasFilter) {
      filterPanel.classList.add("open");
    }

    toggleFilters.addEventListener("click", function () {
      filterPanel.classList.toggle("open");
    });
  }

  // -----------------------------------------------------------
  // Collapsible "Additional" section on battle form
  // -----------------------------------------------------------
  var additionalToggle = document.getElementById("additionalToggle");
  var additionalBody = document.getElementById("additionalBody");

  if (additionalToggle && additionalBody) {
    additionalToggle.addEventListener("click", function () {
      additionalToggle.classList.toggle("collapsed");
      additionalBody.classList.toggle("collapsed");
    });
  }

  // -----------------------------------------------------------
  // Context menu (long-press / right-click) on battle cards
  // -----------------------------------------------------------
  var contextMenu = document.getElementById("contextMenu");
  var longPressTimer = null;

  // Close context menu on any outside click
  document.addEventListener("click", function () {
    if (contextMenu) contextMenu.classList.remove("open");
  });

  // Attach long-press for touch devices
  document.querySelectorAll(".battle-card").forEach(function (card) {
    card.addEventListener("touchstart", function (e) {
      var id = card.getAttribute("data-id");
      longPressTimer = setTimeout(function () {
        e.preventDefault();
        var touch = e.touches[0];
        openContextMenu(touch.clientX, touch.clientY, id);
      }, 500);
    });
    card.addEventListener("touchend", function () {
      clearTimeout(longPressTimer);
    });
    card.addEventListener("touchmove", function () {
      clearTimeout(longPressTimer);
    });
  });
});


/**
 * Show context menu at the given position for a battle.
 * Called from inline oncontextmenu handler on battle cards.
 */
function showContextMenu(event, battleId) {
  event.preventDefault();
  openContextMenu(event.clientX, event.clientY, battleId);
}

function openContextMenu(x, y, battleId) {
  var contextMenu = document.getElementById("contextMenu");
  if (!contextMenu) return;

  // Position
  contextMenu.style.left = x + "px";
  contextMenu.style.top = y + "px";
  contextMenu.classList.add("open");

  // Wire links
  var ctxView = document.getElementById("ctxView");
  var ctxEdit = document.getElementById("ctxEdit");
  var ctxDeleteForm = document.getElementById("ctxDeleteForm");

  if (ctxView) ctxView.href = "/battles/" + battleId;
  if (ctxEdit) ctxEdit.href = "/battles/" + battleId + "/edit";
  if (ctxDeleteForm) ctxDeleteForm.action = "/battles/" + battleId + "/delete";
}
