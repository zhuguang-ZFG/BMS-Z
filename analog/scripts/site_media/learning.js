/* Progressive enhancement: the source images and video links also work without JS. */
(function () {
  'use strict';
  var lessons = {
    rc: { duration: 5, stages: [[0.5, '① 刚合闸：电流最大'], [2.3, '② 充电中：越来越慢'], [4, '③ 对照时间常数与曲线']] },
    mosfet: { duration: 10, stages: [[1, '① 栅极充电，尚未开通'], [4, '② 电流上升'], [7, '③ 米勒平台，漏压下降'], [9, '④ 完全增强']] },
    lm358: { duration: 11, stages: [[1, '① 一个封装，两路运放'], [4, '② 输入共模范围'], [7, '③ 输出摆幅限制'], [10, '④ 选型与应用']] }
  };
  var players = [];
  function button(label, action) {
    var el = document.createElement('button');
    el.type = 'button'; el.textContent = label;
    el.addEventListener('click', action);
    return el;
  }
  function animation(img) {
    var config = lessons[img.dataset.study];
    if (!config || img.dataset.enhanced) { return; }
    img.dataset.enhanced = 'true';
    var figure = document.createElement('figure'); figure.className = 'study-player';
    var viewport = document.createElement('div'); viewport.className = 'study-viewport';
    var controls = document.createElement('div'); controls.className = 'study-controls';
    var caption = document.createElement('figcaption'); caption.textContent = '点击启用控制，可暂停、重播或按阶段观察。动画时间为教学慢放。';
    var source = document.createElement('a'); source.href = img.src; source.textContent = '打开原图';
    var parent = img.parentElement;
    (parent.tagName === 'P' && parent.children.length === 1 ? parent : img).replaceWith(figure);
    viewport.appendChild(img); figure.append(viewport, controls, caption, source);
    var svg, object, timer, cancelLoad;
    var toggle, slider, stageButtons = [];
    function clearStage() {
      stageButtons.forEach(function (el) { el.setAttribute('aria-pressed', 'false'); });
    }
    function stopTimer() { if (timer) { clearInterval(timer); timer = null; } }
    function sync() {
      if (!figure.isConnected) { stopTimer(); return; }
      slider.value = (svg.getCurrentTime() % config.duration).toFixed(2);
      slider.setAttribute('aria-valuetext', Number(slider.value).toFixed(2) + ' 教学秒');
      toggle.textContent = svg.animationsPaused() ? '播放' : '暂停';
    }
    var start = button('启用动画控制', function () {
      start.disabled = true;
      var active = true;
      var restoreFocus = document.activeElement === start;
      object = document.createElement('object'); object.type = 'image/svg+xml';
      object.setAttribute('aria-label', img.alt); object.setAttribute('tabindex', '-1');
      object.style.aspectRatio = (img.getAttribute('width') || 800) + ' / ' + (img.getAttribute('height') || 460);
      var timeout;
      cancelLoad = function () { active = false; clearTimeout(timeout); };
      function fallback() {
        if (!active) { return; }
        cancelLoad(); stopTimer(); svg = null; object.replaceWith(img);
        controls.replaceChildren(start); start.disabled = false;
        caption.textContent = '动画控制暂不可用，可以重试或打开原图观看。';
        if (restoreFocus && figure.isConnected) { start.focus(); }
      }
      object.addEventListener('error', fallback, {once: true});
      object.addEventListener('load', function () {
        if (!active || !figure.isConnected) { return; }
        clearTimeout(timeout);
        try {
          svg = object.contentDocument.documentElement;
          if (!svg || typeof svg.pauseAnimations !== 'function') { fallback(); return; }
          svg.pauseAnimations(); svg.setCurrentTime(0);
          toggle = button('播放', function () {
            if (svg.animationsPaused()) { svg.unpauseAnimations(); } else { svg.pauseAnimations(); }
            clearStage(); caption.textContent = svg.animationsPaused() ? '已暂停。可拖动进度或选择阶段。' : '正在播放，动画时间为教学慢放。';
            sync();
          });
          var replay = button('从头重播', function () {
            svg.setCurrentTime(0); svg.unpauseAnimations(); clearStage();
            caption.textContent = '从头播放，动画时间为教学慢放。'; sync();
          });
          var zoom = button('放大细节', function () {
            var enlarged = viewport.classList.toggle('is-enlarged');
            zoom.setAttribute('aria-pressed', String(enlarged));
            zoom.textContent = enlarged ? '适应宽度' : '放大细节';
          });
          zoom.setAttribute('aria-pressed', 'false');
          slider = document.createElement('input'); slider.type = 'range';
          slider.min = '0'; slider.max = String(config.duration - 0.01); slider.step = '0.01'; slider.value = '0';
          slider.setAttribute('aria-label', '动画时间（教学慢放秒数）');
          slider.addEventListener('input', function () {
            svg.pauseAnimations(); svg.setCurrentTime(Number(slider.value)); clearStage();
            caption.textContent = '已暂停在选定位置，可对照图中的波形与说明。'; sync();
          });
          controls.replaceChildren(toggle, replay, zoom, slider);
          stageButtons = [];
          config.stages.forEach(function (stage) {
            var stageButton = button(stage[1], function () {
              svg.pauseAnimations(); svg.setCurrentTime(stage[0]); sync();
              clearStage(); stageButton.setAttribute('aria-pressed', 'true');
              caption.textContent = stage[1] + '。已暂停，可对照下方说明。';
            });
            stageButton.setAttribute('aria-pressed', 'false');
            stageButtons.push(stageButton); controls.appendChild(stageButton);
          });
          caption.textContent = '已暂停在起点。选择阶段或播放；拖动进度条可逐帧观察。';
          timer = setInterval(sync, 150); sync();
          if (restoreFocus) { toggle.focus(); }
        } catch (error) { fallback(); }
      }, {once: true});
      timeout = setTimeout(fallback, 12000);
      object.data = img.src; img.replaceWith(object);
    });
    controls.appendChild(start);
    function visibility() {
      if (document.hidden && svg && figure.isConnected) { svg.pauseAnimations(); sync(); }
    }
    document.addEventListener('visibilitychange', visibility);
    players.push({ element: figure, dispose: function () {
      if (cancelLoad) { cancelLoad(); }
      stopTimer();
      document.removeEventListener('visibilitychange', visibility);
    } });
  }
  function video(link) {
    if (link.dataset.enhanced) { return; }
    var url = new URL(link.href, location.href);
    var id = url.hostname === 'www.youtube.com' && url.pathname === '/watch' ? url.searchParams.get('v') : null;
    if (!id || !/^[\w-]{11}$/.test(id)) { return; }
    link.dataset.enhanced = 'true';
    var card = document.createElement('div'); card.className = 'study-video';
    var slot = document.createElement('div'); slot.className = 'study-video-slot';
    var note = document.createElement('p'); note.textContent = '点击后加载 YouTube 播放器；若无法播放，请使用原站链接。';
    var parent = link.parentElement;
    // Markdown may wrap a standalone link in <p>; a player must live outside it.
    if (parent.tagName === 'P' && parent.childNodes.length === 1) { parent.replaceWith(card); }
    else { link.parentNode.insertBefore(card, link); }
    card.appendChild(link);
    var load = button('在本页观看', function () {
      var frame = document.createElement('iframe');
      frame.src = 'https://www.youtube-nocookie.com/embed/' + id + '?playsinline=1&autoplay=0';
      frame.title = link.textContent.trim() || '配套教学视频';
      frame.allow = 'fullscreen; picture-in-picture; encrypted-media'; frame.allowFullscreen = true;
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      slot.replaceChildren(frame); load.hidden = true; close.hidden = false;
      note.textContent = '播放器已加载。如遇网络或嵌入限制，请在原站观看。';
      close.focus();
    });
    var close = button('关闭播放器', function () {
      slot.replaceChildren(); load.hidden = false; close.hidden = true; load.focus();
      note.textContent = '播放器已关闭。可重新加载或在原站观看。';
    });
    close.hidden = true; card.append(load, close, slot, note);
  }
  function init() {
    players = players.filter(function (player) {
      if (player.element.isConnected) { return true; }
      player.dispose(); return false;
    });
    document.querySelectorAll('img[data-study]').forEach(function (img) {
      if (!img.closest('[data-visual-player]')) { animation(img); }
    });
    document.querySelectorAll('a[data-study-video]').forEach(video);
  }
  if (typeof document$ !== 'undefined') { document$.subscribe(init); }
  else if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
}());
