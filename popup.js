(function () {
  const url = window.location.href;
  if (!url.includes("polymarket.com")) {
    return;
  }

  if (document.getElementById("polymarket-copilot-panel")) {
    return;
  }

  const panel = document.createElement("div");
  panel.id = "polymarket-copilot-panel";
  panel.style.position = "fixed";
  panel.style.right = "16px";
  panel.style.bottom = "16px";
  panel.style.zIndex = "999999";
  panel.style.width = "320px";
  panel.style.maxHeight = "260px";
  panel.style.overflowY = "auto";
  panel.style.padding = "12px";
  panel.style.borderRadius = "10px";
  panel.style.background = "rgba(15,23,42,0.96)";
  panel.style.color = "#e2e8f0";
  panel.style.fontFamily = "system-ui, -apple-system, BlinkMacSystemFont, sans-serif";
  panel.style.fontSize = "13px";
  panel.style.boxShadow = "0 10px 30px rgba(0,0,0,0.4)";
  panel.style.backdropFilter = "blur(8px)";

  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
      <strong style="font-size:14px;">Polymarket Copilot</strong>
      <button id="copilot-close-btn" style="
        background:none;
        border:none;
        color:#94a3b8;
        cursor:pointer;
        font-size:14px;
      ">✕</button>
    </div>
    <div id="copilot-status" style="font-size:12px;opacity:0.8;margin-bottom:4px;">
      Analyzing this market...
    </div>
    <div id="copilot-score" style="font-size:13px;margin-bottom:4px;"></div>
    <pre id="copilot-explanation" style="
      white-space:pre-wrap;
      font-size:12px;
      background:#020617;
      padding:8px;
      border-radius:8px;
      margin:0;
    "></pre>
  `;

  document.body.appendChild(panel);

  document.getElementById("copilot-close-btn").addEventListener("click", () => {
    panel.remove();
  });

  const statusEl = document.getElementById("copilot-status");
  const scoreEl = document.getElementById("copilot-score");
  const explEl = document.getElementById("copilot-explanation");

  (async () => {
    try {
      const resp = await fetch("https://YOUR_BACKEND_URL/copilot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ market_url: url })
      });

      if (!resp.ok) {
        throw new Error("Backend error: " + resp.status);
      }

      const data = await resp.json();


      const score = data.score ?? "N/A";
      const label = data.label ?? "Unknown";
      const explanation = data.explanation ?? JSON.stringify(data, null, 2);

      statusEl.textContent = `Score: ${score} (${label})`;
      scoreEl.textContent = "";
      explEl.textContent = explanation;
    } catch (err) {
      statusEl.textContent = "Copilot error.";
      scoreEl.textContent = "";
      explEl.textContent = String(err);
      console.error("Copilot error:", err);
    }
  })();
})();