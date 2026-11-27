// MathJax is self-hosted in vendor/mathjax (no third-party requests).
// It renders each equation with an accessible speech label (MathSpeak) for screen readers.
// Absolute URLs are required: the speech worker and the fonts do not resolve relative paths.
(function () {
  var base = new URL('vendor/mathjax/', document.baseURI).href;
  window.__mjReady = new Promise(function (resolve) { window.__mjResolve = resolve; });
  window.MathJax = {
    tex: { inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']], processEscapes: false },
    loader: { paths: { fonts: base + 'fonts' } },
    output: { fontPath: base + 'fonts/%%FONT%%-font' },
    options: {
      sre: { domain: 'mathspeak', style: 'default' },
      worker: { path: base + 'sre', maps: base + 'sre/mathmaps' },
      a11y: { inTabOrder: false }
    },
    startup: {
      typeset: false,
      ready: function () {
        MathJax.startup.defaultReady();
        MathJax.startup.promise.then(function () { window.__mjResolve(true); });
      }
    }
  };
})();
