/**
 * Chat full-screen page — independent của widget.
 */
(function () {
  const API = "/api/chat";
  const els = {
    messages: document.getElementById("chatp-messages"),
    input:    document.getElementById("chatp-input"),
    form:     document.getElementById("chatp-form"),
    quick:    document.getElementById("chatp-quick"),
  };
  if (!els.messages) return;

  let history = [];
  let sending = false;

  greet();
  els.form.addEventListener("submit", e => { e.preventDefault(); send(els.input.value.trim()); });
  els.input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(els.input.value.trim()); }
  });
  els.input.addEventListener("input", () => {
    els.input.style.height = "auto";
    els.input.style.height = Math.min(els.input.scrollHeight, 160) + "px";
  });
  document.querySelectorAll(".cp-q").forEach(b =>
    b.addEventListener("click", () => send(b.dataset.q)));

  function greet() {
    addBot(
      "Chào bạn! Mình là **UniBot** 🤖 — trợ lý AI dùng **RAG + Ollama (Qwen)**.\n\n" +
      "Mình tra cứu trong cơ sở tri thức của UniReg (môn học, lịch, tài liệu, thông báo) " +
      "rồi tổng hợp câu trả lời. Hãy hỏi bằng tiếng Việt nhé!"
    );
  }

  async function send(text) {
    if (!text || sending) return;
    sending = true;
    els.input.value = "";
    els.input.style.height = "auto";
    if (els.quick && history.length === 0) els.quick.style.display = "none";
    addUser(text);
    history.push({ role: "user", text });
    const tid = typing();

    try {
      const r = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: history.slice(-12) }),
      });
      removeTyping(tid);
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.error || "Lỗi máy chủ");
      }
      const d = await r.json();
      addBot(d.reply, d.sources);
      history.push({ role: "model", text: d.reply });
    } catch (e) {
      removeTyping(tid);
      addBot("⚠️ " + (e.message || "Không kết nối được."));
    }
    sending = false;
  }

  function addUser(t) {
    const el = document.createElement("div");
    el.className = "flex justify-end animate-fadeIn";
    el.innerHTML = `<div class="max-w-[75%] bg-forum-base text-white px-4 py-3 rounded-2xl rounded-br-md shadow-sm">${esc(t)}</div>`;
    els.messages.appendChild(el); scroll();
  }

  function addBot(t, sources) {
    const el = document.createElement("div");
    el.className = "flex justify-start animate-fadeIn";
    let src = "";
    if (sources && sources.length) {
      src = `<div class="mt-3 pt-2 border-t border-gray-100 text-xs text-gray-500">
        <i class="fas fa-link mr-1"></i> Nguồn (${sources.length}):
        ${sources.map(s => `<span class="inline-block bg-gray-100 px-2 py-0.5 rounded mr-1 mt-1" title="${esc(s.snippet||"")}">${esc(s.title||s.type)}</span>`).join("")}
      </div>`;
    }
    el.innerHTML = `
      <div class="flex items-start gap-2 max-w-[80%]">
        <div class="w-8 h-8 bg-gradient-to-br from-forum-base to-forum-dark rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
          <i class="fas fa-robot text-white text-xs"></i>
        </div>
        <div class="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm text-gray-800 unibot-bot-text">
          ${md(t)}${src}
        </div>
      </div>`;
    els.messages.appendChild(el); scroll();
  }

  function typing() {
    const id = "tp-" + Date.now();
    const el = document.createElement("div");
    el.id = id; el.className = "flex justify-start";
    el.innerHTML = `<div class="flex items-start gap-2">
      <div class="w-8 h-8 bg-gradient-to-br from-forum-base to-forum-dark rounded-full flex items-center justify-center"><i class="fas fa-robot text-white text-xs"></i></div>
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

  function esc(s) {
    return (s||"").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
  }

  function md(t) {
    let h = esc(t);
    h = h.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    h = h.replace(/\*(.+?)\*/g, "<em>$1</em>");
    h = h.replace(/`(.+?)`/g, "<code class='bg-gray-100 px-1 rounded text-xs'>$1</code>");
    h = h.replace(/\[([^\]]+)\]\(((\/|https?:\/\/)[^\)]+)\)/g, '<a href="$2" target="_blank" class="text-forum-base underline">$1</a>');
    h = h.replace(/^- (.+)$/gm, "<li>$1</li>");
    h = h.replace(/(<li>.*<\/li>\n?)+/g, "<ul class='list-disc ml-5 my-1'>$&</ul>");
    h = h.split(/\n{2,}/).map(p => p.trim().startsWith("<ul")?p:`<p class='mb-1.5 last:mb-0'>${p.replace(/\n/g,"<br>")}</p>`).join("");
    return h;
  }
})();
