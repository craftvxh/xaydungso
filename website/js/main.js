// Gắn liên kết tải xuống / bản phát hành từ js/config.js.
(function () {
  var cfg = window.XDS_CONFIG;
  if (!cfg || !cfg.REPO) return;
  var repoUrl = 'https://github.com/' + cfg.REPO;
  var urls = {
    download: repoUrl + '/releases/latest/download/' + encodeURIComponent(cfg.RELEASE_ASSET),
    releases: repoUrl + '/releases',
    repo: repoUrl,
    readme: repoUrl + '#readme',
  };
  document.querySelectorAll('[data-link]').forEach(function (el) {
    var url = urls[el.getAttribute('data-link')];
    if (url) el.setAttribute('href', url);
  });
  if (cfg.VERSION_LABEL) {
    document.querySelectorAll('[data-version]').forEach(function (el) {
      el.textContent = cfg.VERSION_LABEL;
    });
  }
})();
