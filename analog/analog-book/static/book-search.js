(() => {
  "use strict";

  const search = document.getElementById("book-search");
  const input = document.getElementById("book-search-input");
  const panel = document.getElementById("book-search-panel");
  const list = document.getElementById("book-search-results");
  const status = document.getElementById("book-search-status");
  if (!search || !input || !panel || !list || !status) return;

  const MAX_RESULTS = 18;
  let entries = null;
  let results = [];
  let active = -1;

  const normalize = (text) => (text || "").replace(/\s+/g, " ").trim().toLowerCase();

  function buildIndex() {
    if (entries) return entries;
    entries = [];
    document.querySelectorAll("section.book-page").forEach((page) => {
      const root = page.querySelector(".md-typeset") || page;
      const pageTitle = page.dataset.title || "";
      const partTitle = page.dataset.partTitle || "";
      let current = null;
      const flush = () => {
        if (!current) return;
        current.bodyKey = normalize(current.body);
        entries.push(current);
        current = null;
      };
      const visit = (node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          if (current) current.body += " " + node.nodeValue;
          return;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        const tag = node.tagName.toLowerCase();
        if (tag === "script" || tag === "style" || tag === "svg" || tag === "mjx-container") return;
        if (/^h[1-4]$/.test(tag)) {
          flush();
          const heading = (node.textContent || "").replace(/\s+/g, " ").trim();
          if (!heading) return;
          current = {
            anchor: node.id || page.id,
            heading,
            headingKey: heading.toLowerCase(),
            level: Number(tag[1]),
            pageTitle,
            partTitle,
            body: "",
          };
          return;
        }
        for (const child of node.childNodes) visit(child);
      };
      visit(root);
      flush();
    });
    return entries;
  }

  function snippetFor(entry, tokens) {
    let index = -1;
    for (const token of tokens) {
      index = entry.bodyKey.indexOf(token);
      if (index >= 0) break;
    }
    if (index < 0) return "";
    const start = Math.max(0, index - 32);
    const text = entry.bodyKey.slice(start, start + 120).trim();
    return (start > 0 ? "…" : "") + text + (start + 120 < entry.bodyKey.length ? "…" : "");
  }

  function appendHighlighted(parent, text, tokens) {
    const pattern = tokens
      .slice()
      .sort((a, b) => b.length - a.length)
      .map((token) => token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("|");
    if (!pattern) {
      parent.append(text);
      return;
    }
    const re = new RegExp("(" + pattern + ")", "gi");
    let last = 0;
    let match;
    while ((match = re.exec(text)) !== null) {
      if (match.index > last) parent.append(text.slice(last, match.index));
      const mark = document.createElement("mark");
      mark.textContent = match[0];
      parent.append(mark);
      last = match.index + match[0].length;
    }
    if (last < text.length) parent.append(text.slice(last));
  }

  function find(raw) {
    const query = normalize(raw);
    if (!query) return [];
    const tokens = query.split(" ").filter(Boolean);
    const found = [];
    for (const entry of buildIndex()) {
      let score = 0;
      let matched = true;
      for (const token of tokens) {
        const inHeading = entry.headingKey.includes(token);
        if (!inHeading && !entry.bodyKey.includes(token)) {
          matched = false;
          break;
        }
        score += inHeading ? 100 : 10;
      }
      if (!matched) continue;
      score += (5 - Math.min(entry.level, 5)) * 2;
      found.push({ entry, score, snippet: snippetFor(entry, tokens) });
    }
    found.sort((a, b) => b.score - a.score
      || a.entry.anchor.localeCompare(b.entry.anchor));
    return found;
  }

  function setActive(index) {
    const options = Array.from(list.children);
    if (!options.length) return;
    active = (index + options.length) % options.length;
    options.forEach((option, optionIndex) => {
      option.setAttribute("aria-selected", optionIndex === active ? "true" : "false");
    });
    input.setAttribute("aria-activedescendant", options[active].id);
    options[active].scrollIntoView({ block: "nearest" });
  }

  function close() {
    panel.hidden = true;
    list.replaceChildren();
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    status.textContent = "";
    results = [];
    active = -1;
  }

  function choose(index) {
    const item = results[index];
    if (!item) return;
    const anchor = item.entry.anchor;
    close();
    input.blur();
    if (!anchor) return;
    const target = document.getElementById(anchor);
    if (!target) return;
    if (window.location.hash === "#" + anchor) {
      target.scrollIntoView({ block: "start" });
    } else {
      window.location.hash = anchor;
    }
  }

  function render() {
    const found = find(input.value);
    const tokens = normalize(input.value).split(" ").filter(Boolean);
    const visible = found.slice(0, MAX_RESULTS);
    list.replaceChildren();
    results = visible;
    active = -1;
    input.removeAttribute("aria-activedescendant");
    if (!found.length) {
      status.textContent = "没有找到匹配的章节";
    } else {
      status.textContent = found.length > MAX_RESULTS
        ? "找到 " + found.length + " 条结果，显示前 " + MAX_RESULTS + " 条"
        : "找到 " + found.length + " 条结果";
      visible.forEach(({ entry, snippet }, index) => {
        const option = document.createElement("li");
        option.id = "book-search-option-" + index;
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", "false");
        const title = document.createElement("span");
        title.className = "book-search-hit";
        appendHighlighted(title, entry.heading, tokens);
        const crumb = document.createElement("span");
        crumb.className = "book-search-crumb";
        crumb.textContent = [entry.partTitle, entry.pageTitle].filter(Boolean).join(" · ");
        option.append(title, crumb);
        if (snippet) {
          const text = document.createElement("span");
          text.className = "book-search-snippet";
          appendHighlighted(text, snippet, tokens);
          option.append(text);
        }
        option.addEventListener("mousedown", (event) => {
          event.preventDefault();
          choose(index);
        });
        list.append(option);
      });
    }
    panel.hidden = false;
    input.setAttribute("aria-expanded", "true");
  }

  input.addEventListener("input", () => {
    if (normalize(input.value)) render();
    else close();
  });

  input.addEventListener("focus", () => {
    if (normalize(input.value)) render();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      if (panel.hidden) render();
      if (panel.hidden) return;
      event.preventDefault();
      setActive(active + (event.key === "ArrowDown" ? 1 : -1));
      return;
    }
    if (event.key === "Enter") {
      if (panel.hidden) return;
      event.preventDefault();
      choose(active >= 0 ? active : 0);
      return;
    }
    if (event.key === "Escape") {
      close();
      input.blur();
    }
  });

  search.addEventListener("focusout", (event) => {
    if (!search.contains(event.relatedTarget)) close();
  });

  document.addEventListener("pointerdown", (event) => {
    if (!search.contains(event.target)) close();
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    const tag = (target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea" || tag === "select"
      || target.isContentEditable;
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      input.focus();
      input.select();
      return;
    }
    if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      input.focus();
    }
  });
})();
