/**
 * UniBot widget — gọi /api/chat (RAG + Ollama).
 */
(function () {
  const API_URL = "/api/chat";
  const STORAGE_KEY = "unibot_history";
  const els = {};
  let isOpen = false, isSending = false, history = [];

  document.addEventListener("DOMContentLoaded", init);

  function $(id) { return document.getElementById(id); }

  function init() {
    Object.assign(els, {
      toggle: $("unibot-toggle"), window: $("unibot-window"),
      messages: $("unibot-messages"), input: $("unibot-input"),
      sendBtn: $("unibot-send"), iconChat: $("unibot-icon-chat"),
      iconClose: $("unibot-icon-close"), dot: $("unibot-dot"),
      quick: $("unibot-quick"), form: $("unibot-form"),
      clearBtn: $("unibot-clear"), minBtn: $("unibot-min"),
    });
    if (!els.toggle) return;

    els.toggle.addEventListener("click", toggle);
    els.minBtn?.addEventListener("click", toggle);
    els.clearBtn?.addEventListener("click", clearChat);
    els.form?.addEventListener("submit", e => {
      e.preventDefault();
      const text = els.input.value.trim();
      if (text && !isSending) send(text);
    });
    els.input?.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const text = els.input.value.trim();
        if (text && !isSending) send(text);
      }
    });
    els.input?.addEventListener("input", () => {
      els.input.style.height = "auto";
      els.input.style.height = Math.min(els.input.scrollHeight, 96) + "px";
    });
    document.querySelectorAll(".ub-quick").forEach(b =>
      b.addEventListener("click", () => send(b.dataset.q)));

    addBot(
      "Xin chào! Mình là **UniBot** 🤖 — trợ lý ảo dùng RAG + Ollama (Qwen).\n\n" +
      "Mình có thể giúp bạn:\n" +
      "- [**Đăng ký tín chỉ**](/student/registration)\n" +
      "- [**Xem lịch học**](/student/schedule)\n" +
      "- [**Tài liệu học tập**](/student/materials)\n" +
      "- [**Điểm & GPA**](/student/grades)\n\n" +
      "Hỏi mình bằng tiếng Việt nhé! 😊"
    );
    loadHistory();
  }

  function toggle() {
    isOpen = !isOpen;
    els.window.classList.toggle("hidden", !isOpen);
    els.iconChat.classList.toggle("hidden", isOpen);
    els.iconClose.classList.toggle("hidden", !isOpen);
    els.dot?.classList.add("hidden");
    if (isOpen) { scroll(); setTimeout(() => els.input.focus(), 100); }
  }

  async function send(text) {
    isSending = true;
    els.sendBtn.disabled = true;
    els.input.value = "";
    els.input.style.height = "auto";
    if (history.length === 0 && els.quick) els.quick.style.display = "none";

    addUser(text);
    history.push({ role: "user", text });
    const tid = typing();

    try {
      const r = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: history.slice(-12) }),
      });
      removeTyping(tid);
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.error || "Lỗi kết nối server.");
      }
      const d = await r.json();
      const reply = d.reply || "Xin lỗi, mình chưa hiểu. Bạn thử hỏi lại nhé!";
      addBot(reply, d.sources);
      history.push({ role: "model", text: reply });
      saveHistory();
    } catch (e) {
      removeTyping(tid);
      addBot("⚠️ " + (e.message || "Không kết nối được."));
    }
    isSending = false;
    els.sendBtn.disabled = false;
    els.input.focus();
  }

  function addUser(text) {
    const el = document.createElement("div");
    el.className = "flex justify-end animate-fadeIn";
    el.innerHTML =
      `<div class="max-w-[80%] bg-forum-base text-white px-4 py-2.5 rounded-2xl rounded-br-md text-sm leading-relaxed shadow-sm">${esc(text)}</div>`;
    els.messages.appendChild(el); scroll();
  }

  function addBot(text, sources) {
    const el = document.createElement("div");
    el.className = "flex justify-start animate-fadeIn";
    let src = "";
    if (sources && sources.length) {
      src = `<div class="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500">
        <i class="fas fa-link mr-1"></i> Nguồn:
        ${sources.slice(0, 3).map(s =>
          `<span class="inline-block bg-gray-100 px-2 py-0.5 rounded mr-1 mt-1" title="${esc(s.snippet||"")}">${esc(s.title||s.type)}</span>`
        ).join("")}</div>`;
    }
    el.innerHTML = `
      <div class="flex items-start gap-2 max-w-[88%]">
        <div class="w-7 h-7 bg-gradient-to-br from-forum-base to-forum-dark rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
          <i class="fas fa-robot text-white text-xs"></i>
        </div>
        <div class="bg-white border border-gray-200 px-4 py-2.5 rounded-2xl rounded-bl-md text-sm leading-relaxed shadow-sm text-gray-800 unibot-bot-text">
          ${md(text)}${src}
        </div>
      </div>`;
    els.messages.appendChild(el); scroll();
  }

  function typing() {
    const id = "tp-" + Date.now();
    const el = document.createElement("div");
    el.id = id; el.className = "flex justify-start";
    el.innerHTML = `<div class="flex items-start gap-2">
      <div class="w-7 h-7 bg-gradient-to-br from-forum-base to-forum-dark rounded-full flex items-center justify-center"><i class="fas fa-robot text-white text-xs"></i></div>
      <div class="bg-white border border-gray-200 px-4 py-3 rounded-2xl shadow-sm flex gap-1.5">
        <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
        <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:.15s"></span>
        <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay:.3s"></span>
      </div></div>`;
    els.messages.appendChild(el); scroll();
    return id;
  }
  function removeTyping(id) { document.getElementById(id)?.remove(); }
  function scroll() { requestAnimationFrame(() => els.messages.scrollTop = els.messages.scrollHeight); }

  function clearChat() {
    if (!confirm("Xóa toàn bộ hội thoại?")) return;
    history = [];
    els.messages.innerHTML = "";
    if (els.quick) els.quick.style.display = "";
    localStorage.removeItem(STORAGE_KEY);
    addBot("Hội thoại đã được xóa. Hỏi mình câu mới nhé! 😊");
  }

  function saveHistory() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-20))); } catch (_) {}
  }

  function loadHistory() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (!saved) return;
      const arr = JSON.parse(saved);
      if (!Array.isArray(arr) || !arr.length) return;
      arr.forEach(m => m.role === "user" ? addUser(m.text) : addBot(m.text));
      history = arr;
      if (els.quick) els.quick.style.display = "none";
    } catch (_) {}
  }

  function esc(s) {
    const m = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return (s || "").replace(/[&<>"']/g, c => m[c]);
  }

  function md(text) {
    let h = esc(text);
    h = h.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    h = h.replace(/\*(.+?)\*/g, "<em>$1</em>");
    h = h.replace(/`(.+?)`/g, "<code class='bg-gray-100 px-1 rounded text-xs'>$1</code>");
    h = h.replace(/\[([^\]]+)\]\(((\/|https?:\/\/)[^\)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener" class="text-forum-base underline hover:text-forum-dark">$1</a>');
    h = h.replace(/^- (.+)$/gm, "<li>$1</li>");
    h = h.replace(/(<li>.*<\/li>\n?)+/g, "<ul class='list-disc ml-5 my-1'>$&</ul>");
    h = h.split(/\n{2,}/).map(p => p.trim().startsWith("<ul")
      ? p : `<p class='mb-1.5 last:mb-0'>${p.replace(/\n/g, "<br>")}</p>`).join("");
    return h;
  }
})();
