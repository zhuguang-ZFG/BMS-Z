/* V2: a static conclusion first, then a user-controlled, single-play SVG timeline. */
(function () {
  'use strict';
  var instances = [];
  function button(text, action) {
    var el = document.createElement('button');
    el.type = 'button'; el.textContent = text; el.setAttribute('aria-label', text);
    el.addEventListener('click', action); return el;
  }
  function mount(host) {
    if (host.dataset.visualReady) { return; }
    var config;
    try { config = JSON.parse(host.dataset.timeline); } catch (error) { return; }
    if (!(config.duration > 0) || !Array.isArray(config.beats) || !config.beats.length) { return; }
    host.dataset.visualReady = 'true';
    var viewport = host.querySelector('.visual-player-viewport');
    var image = viewport.querySelector('img');
    var controls = host.querySelector('.visual-player-controls');
    var status = host.querySelector('.visual-player-status');
    var source = new URL(host.dataset.animationSrc, document.baseURI);
    if (source.origin !== location.origin) { return; }
    var media = window.matchMedia('(prefers-reduced-motion: reduce)');
    var svg = null, object = null, frame = 0, timeout = 0, loadVersion = 0;
    var playing = false, time = 0, rate = 1, last = 0, disposed = false;
    var toggle, slider, progressText, beatButtons = [], lastLabel = '';
    viewport.style.aspectRatio = image.getAttribute('width') + ' / ' + image.getAttribute('height');

    function message(text) { if (text !== lastLabel) { status.textContent = text; lastLabel = text; } }
    function sync() {
      if (!svg) { return; }
      svg.setCurrentTime(time);
      slider.value = String(time);
      slider.setAttribute('aria-valuetext', time.toFixed(1) + ' / ' + config.duration + ' 秒');
      progressText.textContent = time.toFixed(1) + ' / ' + config.duration + ' 秒';
      toggle.textContent = playing ? '暂停' : '播放';
      toggle.setAttribute('aria-label', toggle.textContent);
      var index = config.beats.findIndex(function (beat) { return time >= beat.start && time < beat.end; });
      if (index < 0) { index = config.beats.length - 1; }
      beatButtons.forEach(function (el, i) { el.setAttribute('aria-pressed', String(i === index)); });
      message((time >= config.duration ? '已到结论：' : (playing ? '播放：' : '暂停：')) + config.beats[index].name);
    }
    function stop() { playing = false; cancelAnimationFrame(frame); frame = 0; }
    function advance(now) {
      if (disposed || !host.isConnected || document.hidden) { stop(); if (host.isConnected) { sync(); } return; }
      time = Math.min(config.duration, time + Math.max(0, now - last) / 1000 * rate);
      last = now;
      if (time >= config.duration) { stop(); }
      sync();
      if (playing) { frame = requestAnimationFrame(advance); }
    }
    function play() {
      if (time >= config.duration) { time = 0; }
      playing = true; last = performance.now(); cancelAnimationFrame(frame);
      sync(); frame = requestAnimationFrame(advance);
    }
    function staticView(text) {
      stop(); loadVersion += 1; clearTimeout(timeout); svg = null;
      if (object) { object.remove(); object = null; }
      image.hidden = false; controls.replaceChildren(start); start.disabled = false;
      message(text);
    }
    function ready(focus) {
      toggle = button('暂停', function () { if (playing) { stop(); sync(); } else { play(); } });
      var replay = button('重播', function () { time = 0; play(); });
      var still = button('显示结论静帧', function () { staticView('结论静帧'); start.focus(); });
      var speedLabel = document.createElement('label'); speedLabel.textContent = '速度';
      var speed = document.createElement('select'); speed.setAttribute('aria-label', '播放速度');
      [0.5, 1, 1.5].forEach(function (value) {
        var option = document.createElement('option'); option.value = String(value);
        option.textContent = value + '×'; option.selected = value === rate; speed.appendChild(option);
      });
      speed.addEventListener('change', function () {
        if (playing) { time = Math.min(config.duration, time + (performance.now() - last) / 1000 * rate); }
        rate = Number(speed.value); last = performance.now(); sync();
      });
      speedLabel.appendChild(speed);
      slider = document.createElement('input'); slider.type = 'range'; slider.className = 'visual-player-progress';
      slider.min = '0'; slider.max = String(config.duration); slider.step = '0.01';
      slider.setAttribute('aria-label', '动画进度');
      progressText = document.createElement('span'); progressText.className = 'visual-player-time';
      progressText.setAttribute('role', 'timer');
      progressText.setAttribute('aria-label', '当前时间与总时长');
      slider.addEventListener('input', function () { stop(); time = Number(slider.value); sync(); });
      var beats = document.createElement('div'); beats.className = 'visual-player-beats';
      beatButtons = config.beats.map(function (beat, index) {
        var el = button((index + 1) + '. ' + beat.name, function () {
          stop(); time = Math.min(beat.end - 0.01, beat.start + 0.6); sync();
        });
        el.setAttribute('aria-pressed', 'false'); beats.appendChild(el); return el;
      });
      controls.replaceChildren(toggle, replay, still, speedLabel, slider, progressText, beats);
      if (media.matches) { time = config.duration; sync(); } else { time = 0; play(); }
      if (focus) { toggle.focus(); }
    }
    var start = button('播放动画', function () {
      start.disabled = true; var version = ++loadVersion;
      var focus = document.activeElement === start;
      object = document.createElement('object'); object.type = 'image/svg+xml';
      object.setAttribute('aria-label', image.alt); object.setAttribute('tabindex', '-1');
      object.style.visibility = 'hidden';
      function fail() {
        if (version !== loadVersion || disposed) { return; }
        staticView('动画加载失败，已保留结论静帧；可重试或查看原动画。');
        if (focus && host.isConnected) { start.focus(); }
      }
      object.addEventListener('error', fail, {once: true});
      object.addEventListener('load', function () {
        if (version !== loadVersion || disposed || !host.isConnected) { return; }
        clearTimeout(timeout);
        try {
          svg = object.contentDocument.documentElement;
          if (!svg || svg.localName !== 'svg' || typeof svg.pauseAnimations !== 'function') { fail(); return; }
          svg.pauseAnimations(); svg.setCurrentTime(0);
          image.hidden = true; object.style.visibility = ''; ready(focus);
        } catch (error) { fail(); }
      }, {once: true});
      timeout = setTimeout(fail, 12000);
      object.data = source.href; viewport.appendChild(object);
      message('正在载入动画…');
    });
    controls.appendChild(start);
    if (media.matches) { message('已启用减弱动效：显示结论静帧；可按需查看各节拍。'); }
    function visibility() { if (document.hidden) { stop(); sync(); } }
    function reduceMotion() {
      if (media.matches) { staticView('已启用减弱动效：显示结论静帧。'); }
    }
    document.addEventListener('visibilitychange', visibility);
    media.addEventListener('change', reduceMotion);
    instances.push({host: host, dispose: function () {
      disposed = true; stop(); loadVersion += 1; clearTimeout(timeout);
      document.removeEventListener('visibilitychange', visibility);
      media.removeEventListener('change', reduceMotion);
    }});
  }
  function init() {
    instances = instances.filter(function (instance) {
      if (instance.host.isConnected) { return true; }
      instance.dispose(); return false;
    });
    document.querySelectorAll('[data-visual-player]').forEach(mount);
  }
  if (typeof document$ !== 'undefined') { document$.subscribe(init); }
  else if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
}());
