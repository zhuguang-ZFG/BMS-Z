/* Optional learning records. All links/titles come from the generated catalog. */
(function () {
  'use strict';
  var catalog = window.ANALOG_LEARNING_CATALOG;
  if (!catalog || !document.currentScript) return;
  var base = new URL('../', document.currentScript.src);
  var key = 'analog-learning:v1:' + base.pathname;
  var chapters = new Map(catalog.chapters.map(function (entry) { return [entry.id, entry]; }));
  var questions = new Map(catalog.questions.map(function (entry) { return [entry.id, entry]; }));
  var temporary = false;
  var current = null;
  var scheduled = false;
  var pending = new Map();

  function uniqueKnown(values, index) {
    return Array.isArray(values) ? Array.from(new Set(values.filter(function (id) { return index.has(id); }))) : [];
  }
  function parse(raw) {
    try { return JSON.parse(raw); } catch (_) { return null; }
  }
  function apply(record, change) {
    if (change.field === 'last') {
      record.last = change.value;
      return;
    }
    var list = record[change.field];
    var index = list.indexOf(change.id);
    if (change.value && index === -1) list.push(change.id);
    else if (!change.value && index !== -1) list.splice(index, 1);
  }
  function knownLast(value) {
    if (!value || !chapters.has(value.chapter)) return null;
    return { chapter: value.chapter,
      anchor: typeof value.anchor === 'string' ? value.anchor.slice(0,150) : value.chapter };
  }
  function read() {
    var empty = { version: 1, completed: [], bookmarks: [], last: null };
    try {
      // Read the original v1 snapshot as a baseline. Per-record overrides
      // preserve existing records without a bulk migration or shared writes.
      var raw = parse(localStorage.getItem(key));
      if (raw && raw.version === 1) {
        empty.completed = uniqueKnown(raw.completed, chapters);
        empty.bookmarks = uniqueKnown(raw.bookmarks, questions);
        empty.last = knownLast(raw.last);
      }
      [['completed', chapters], ['bookmarks', questions]].forEach(function (group) {
        group[1].forEach(function (_, id) {
          var value = parse(localStorage.getItem(key + group[0] + ':' + id));
          if (typeof value === 'boolean') apply(empty, { field: group[0], id: id, value: value });
        });
      });
      var last = knownLast(parse(localStorage.getItem(key + 'last')));
      if (last) empty.last = last;
    } catch (_) {
      temporary = true;
      if (state) empty = { version: 1, completed: state.completed.slice(),
        bookmarks: state.bookmarks.slice(), last: state.last };
    }
    pending.forEach(function (change) { apply(empty, change); });
    return empty;
  }
  var state = read();
  function save(change) {
    saveChanges([change]);
  }
  function saveChanges(changes) {
    changes.forEach(function (change) {
      var slot = key + change.field + (change.id ? ':' + change.id : '');
      pending.set(slot, change);
    });
    state = read();
    // One atomic, synchronous write per record: unrelated tab actions cannot
    // overwrite each other, and an immediate reload cannot cancel a save.
    // Keep false overrides so removing a legacy record stays removed.
    pending.forEach(function (entry, entryKey) {
      try {
        localStorage.setItem(entryKey, JSON.stringify(entry.value));
        pending.delete(entryKey);
      } catch (_) { /* Retry this page's unsaved actions on its next change. */ }
    });
    temporary = pending.size > 0;
    refresh();
  }
  function element(tag, text, className) {
    var el = document.createElement(tag);
    if (text) el.textContent = text;
    if (className) el.className = className;
    return el;
  }
  function link(entry, anchor) {
    var el = element('a', entry.title);
    var url = new URL(entry.href, base);
    if (anchor) url.hash = anchor;
    el.href = url.href;
    return el;
  }
  function toggle(field, value) {
    // Two tabs marking an unfinished chapter both intend "complete".
    var add = !state[field].includes(value);
    save({ field: field, id: value, value: add });
  }
  function button(label, handler, className) {
    var el = element('button', label, className);
    el.type = 'button';
    el.addEventListener('click', handler);
    return el;
  }
  function backupMessage(message) {
    var note = document.querySelector('.learning-backup-message');
    if (note) note.textContent = message;
  }
  function exportRecords() {
    state = read();
    var data = { format: 'analog-circuit-learning', version: 1,
      exportedAt: new Date().toISOString(), completed: state.completed,
      bookmarks: state.bookmarks, last: state.last };
    var blob = new Blob([JSON.stringify(data, null, 2) + '\n'], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var download = element('a');
    download.href = url;
    download.download = 'analog-learning-' + data.exportedAt.slice(0, 10) + '.json';
    document.body.appendChild(download);
    download.click();
    download.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    backupMessage('已导出当前学习记录，可在另一浏览器导入。');
  }
  function importRecords(file) {
    if (!file) return;
    if (file.size > 256 * 1024) {
      backupMessage('文件过大，请选择本站导出的学习记录（不超过 256KB）。');
      return;
    }
    file.text().then(function (text) {
      var raw = JSON.parse(text);
      function validList(list) {
        return Array.isArray(list) && list.length <= 1000 && list.every(function (id) {
          return typeof id === 'string' && id.length <= 150;
        });
      }
      if (!raw || raw.format !== 'analog-circuit-learning' || raw.version !== 1 ||
          !validList(raw.completed) || !validList(raw.bookmarks) ||
          !(raw.last === null || (raw.last && typeof raw.last.chapter === 'string' &&
            typeof raw.last.anchor === 'string' && raw.last.anchor.length <= 150 &&
            !/[\u0000-\u001f]/.test(raw.last.anchor)))) {
        throw new Error('Unsupported learning record');
      }
      // Validate the entire file before applying anything; titles and URLs are
      // never imported. Unknown IDs from other editions are simply ignored.
      state = read();
      var completed = uniqueKnown(raw.completed, chapters);
      var bookmarks = uniqueKnown(raw.bookmarks, questions);
      var changes = [];
      [['completed', completed], ['bookmarks', bookmarks]].forEach(function (group) {
        group[1].forEach(function (id) {
          if (!state[group[0]].includes(id)) changes.push({ field: group[0], id: id, value: true });
        });
      });
      var last = knownLast(raw.last);
      if (!state.last && last) changes.push({ field: 'last', value: last });
      saveChanges(changes);
      var ignored = raw.completed.length + raw.bookmarks.length - completed.length - bookmarks.length;
      backupMessage('记录已合并，已有进度保留。' + (ignored ? '已忽略重复或未知编号。' : '') +
        (temporary ? '浏览器未能保存，当前记录可先导出备份。' : ''));
    }).catch(function () {
      backupMessage('无法导入：请使用本站导出的有效版本 1 JSON 文件。已有记录未更改。');
    });
  }
  function dashboard() {
    var root = document.querySelector('.learning-dashboard');
    if (!root) return;
    if (!root.querySelector('h2')) {
      root.appendChild(element('h2', '我的学习记录'));
      root.appendChild(element('a', '', 'learning-resume'));
      root.appendChild(element('p', '', 'learning-count'));
      var progress = element('progress');
      progress.max = catalog.chapters.length;
      progress.setAttribute('aria-label', '章节完成进度');
      root.appendChild(progress);
      var chapterDetails = element('details', '', 'learning-chapters');
      chapterDetails.appendChild(element('summary', '章节进度'));
      var chapterList = element('ul');
      catalog.chapters.forEach(function (entry) {
        var item = element('li');
        item.appendChild(link(entry, entry.id));
        var status = element('span', '', 'learning-chapter-status');
        status.dataset.chapter = entry.id;
        item.appendChild(status);
        chapterList.appendChild(item);
      });
      chapterDetails.appendChild(chapterList);
      root.appendChild(chapterDetails);
      var bookmarks = element('details', '', 'learning-bookmarks');
      bookmarks.appendChild(element('summary'));
      bookmarks.appendChild(element('p', '在自测题旁点击“收藏为错题”，下次从这里复习。'));
      bookmarks.appendChild(element('ul'));
      root.appendChild(bookmarks);
      var controls = element('div', '', 'learning-backup');
      var picker = element('input');
      picker.type = 'file';
      picker.accept = '.json,application/json';
      picker.hidden = true;
      picker.setAttribute('aria-label', '选择学习记录文件');
      picker.addEventListener('change', function () {
        var file = picker.files[0];
        picker.value = '';
        importRecords(file);
      });
      controls.appendChild(button('导出学习记录', exportRecords));
      controls.appendChild(button('导入学习记录', function () { picker.click(); }));
      controls.appendChild(picker);
      root.appendChild(controls);
      var backupNote = element('p', '导入会合并完成章节与错题，保留当前阅读位置；文件仅在本机处理。', 'learning-backup-message');
      backupNote.setAttribute('role', 'status');
      root.appendChild(backupNote);
      var note = element('p', '', 'learning-storage-note');
      note.setAttribute('role', 'status');
      root.appendChild(note);
    }
    var resume = root.querySelector('.learning-resume');
    resume.hidden = !state.last;
    if (state.last) {
      var target = link(chapters.get(state.last.chapter), state.last.anchor);
      resume.href = target.href;
      resume.textContent = '继续上次阅读：' + target.textContent;
    } else {
      resume.removeAttribute('href');
    }
    root.querySelector('.learning-count').textContent =
      '已完成 ' + state.completed.length + ' / ' + catalog.chapters.length + ' 章';
    root.querySelector('progress').value = state.completed.length;
    root.querySelectorAll('.learning-chapter-status').forEach(function (status) {
      var done = state.completed.includes(status.dataset.chapter);
      status.textContent = done ? '已完成' : '未完成';
      status.dataset.done = String(done);
    });
    var details = root.querySelector('.learning-bookmarks');
    details.querySelector('summary').textContent = '错题收藏（' + state.bookmarks.length + '）';
    details.querySelector('p').hidden = Boolean(state.bookmarks.length);
    var list = details.querySelector('ul');
    var signature = JSON.stringify(state.bookmarks);
    if (list.dataset.bookmarks !== signature) {
      var active = list.contains(document.activeElement) ? document.activeElement : null;
      var focusedId = active && active.dataset.question;
      list.replaceChildren();
      state.bookmarks.forEach(function (id) {
        var item = element('li');
        var review = link(questions.get(id));
        review.dataset.question = id;
        item.appendChild(review);
        list.appendChild(item);
      });
      list.dataset.bookmarks = signature;
      if (active) {
        var replacement = Array.from(list.querySelectorAll('a')).find(function (a) {
          return a.dataset.question === focusedId;
        });
        (replacement || details.querySelector('summary')).focus({ preventScroll: true });
      }
    }
  }
  function refresh() {
    document.querySelectorAll('.chapter-done-button').forEach(function (el) {
      var done = state.completed.includes(el.dataset.chapter);
      el.setAttribute('aria-pressed', String(done));
      el.textContent = done ? '本章已完成 · 点击撤销' : '标记本章已完成';
    });
    document.querySelectorAll('.question-bookmark').forEach(function (el) {
      var saved = state.bookmarks.includes(el.dataset.question);
      el.setAttribute('aria-pressed', String(saved));
      el.textContent = saved ? '已收藏 · 移出错题' : '收藏为错题';
    });
    dashboard();
    document.querySelectorAll('.learning-storage-note').forEach(function (note) {
      note.textContent = temporary ? '浏览器无法保存，本次操作仅临时保留。' :
        '记录仅保存在当前浏览器，清除站点数据后会丢失。';
    });
  }
  function remember(anchor) {
    if (!current || (state.last && state.last.chapter === current.id && state.last.anchor === anchor)) return;
    var chapterId = current.id;
    save({ field: 'last', value: { chapter: chapterId, anchor: anchor } });
  }
  function init() {
    current = catalog.chapters.find(function (entry) {
      return new URL(entry.href, base).pathname === location.pathname;
    }) || null;
    if (current) {
      var anchor;
      try { anchor = decodeURIComponent(location.hash.slice(1)); } catch (_) { anchor = ''; }
      var target = document.getElementById(anchor);
      if (!target || !target.classList.contains('legacy-anchor')) remember(target ? anchor : current.id);
      var checkpoint = document.querySelector('.reading-checkpoint');
      if (checkpoint && !checkpoint.querySelector('.chapter-done-button')) {
        var chapterId = current.id;
        var done = button('标记本章已完成', function () { toggle('completed', chapterId); }, 'chapter-done-button');
        done.dataset.chapter = chapterId;
        checkpoint.appendChild(done);
        var note = element('p', '', 'learning-storage-note');
        note.setAttribute('role', 'status');
        checkpoint.appendChild(note);
      }
    }
    document.querySelectorAll('a[data-quiz-question]').forEach(function (anchor) {
      if (!questions.has(anchor.id)) return;
      var parent = anchor.closest('li') || anchor.parentElement;
      if (parent.querySelector('.question-bookmark')) return;
      var tools = element('div', '', 'question-tools');
      var mark = button('收藏为错题', function () { toggle('bookmarks', anchor.id); }, 'question-bookmark');
      mark.dataset.question = anchor.id;
      mark.setAttribute('aria-label', '错题收藏：' + questions.get(anchor.id).title);
      tools.appendChild(mark);
      parent.appendChild(tools);
    });
    var quizTitle = document.querySelector('.md-content h1');
    if (quizTitle && document.querySelector('.question-bookmark') && !document.querySelector('.quiz-storage-note')) {
      var quizNote = element('p', '', 'learning-storage-note quiz-storage-note');
      quizNote.setAttribute('role', 'status');
      quizTitle.after(quizNote);
    }
    var hero = document.querySelector('.learning-hero');
    if (hero && !document.querySelector('.learning-dashboard')) {
      hero.after(element('section', '', 'learning-dashboard'));
    }
    refresh();
  }
  window.addEventListener('scroll', function () {
    if (!current || scheduled) return;
    scheduled = true;
    requestAnimationFrame(function () {
      scheduled = false;
      if (!current) return;
      var anchor = current.id;
      document.querySelectorAll('.md-content h2[id], .md-content h3[id], .md-content h4[id]').forEach(function (heading) {
        if (heading.getBoundingClientRect().top <= 110) anchor = heading.id;
      });
      remember(anchor);
    });
  }, { passive: true });
  window.addEventListener('storage', function (event) {
    if (event.key === null || event.key.startsWith(key)) {
      state = read();
      refresh();
    }
  });
  if (typeof document$ !== 'undefined') document$.subscribe(init);
  else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
