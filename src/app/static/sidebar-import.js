// Sidebar drop zone: drag/drop wiring for the import form in base.html.
// The <label for="sidebar-export-file"> wrapper handles click-to-browse
// natively, so this file only needs to handle drag/drop state and to
// reveal the submit button once a file has been chosen.
(function () {
  var zone = document.getElementById('sidebar-drop-zone');
  var input = document.getElementById('sidebar-export-file');
  var prompt = document.getElementById('sidebar-drop-zone-prompt');
  var filename = document.getElementById('sidebar-drop-zone-filename');
  var submit = document.getElementById('sidebar-import-submit');
  if (!zone || !input) return;

  zone.addEventListener('dragover', function (e) {
    e.preventDefault();
    zone.classList.add('drop-zone--active');
  });

  zone.addEventListener('dragleave', function () {
    zone.classList.remove('drop-zone--active');
  });

  zone.addEventListener('drop', function (e) {
    e.preventDefault();
    zone.classList.remove('drop-zone--active');
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      showFile(e.dataTransfer.files[0].name);
    }
  });

  input.addEventListener('change', function () {
    if (input.files && input.files.length) {
      showFile(input.files[0].name);
    }
  });

  function showFile(name) {
    if (prompt) prompt.style.display = 'none';
    if (filename) {
      filename.textContent = name;
      filename.style.display = 'block';
    }
    zone.classList.add('drop-zone--has-file');
    if (submit) submit.hidden = false;
  }
})();
