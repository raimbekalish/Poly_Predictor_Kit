// --- Main Setup ---
document.addEventListener("DOMContentLoaded", () => {
  const outcomeDisplay = document.getElementById("outcome");

  // Find active tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const currentTab = tabs[0];

    // Ensure it's a Polymarket event page
    if (currentTab && currentTab.url && currentTab.url.includes("polymarket.com/event/")) {
      const eventUrl = currentTab.url;
      console.log("Polymarket Event URL:", eventUrl);

      // Extract slug from Polymarket event URL
      function extractSlug(url) {
        try {
          const after = url.split("/event/")[1];
          if (!after) return null;
          return after.split("?")[0];
        } catch (err) {
          console.error("Slug extraction error:", err);
          return null;
        }
      }

      const slug = extractSlug(eventUrl);
      console.log("Extracted slug:", slug);

      // ===========================================================
      // FEATURE 1 — Gemini AI Trade Insight
      // ===========================================================
      document.getElementById("feature1Btn").addEventListener("click", () => {
        if (!slug) {
          outcomeDisplay.textContent = "Could not parse event slug.";
          return;
        }

        outcomeDisplay.textContent = "Generating AI Market Insight...";

        fetch("http://127.0.0.1:5002/ai-insight", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slug })
        })
          .then((res) => res.json())
          .then((data) => {
            console.log("Gemini Insight backend returned:", data);

            if (data.error) {
              outcomeDisplay.textContent = "AI Insight Error: " + data.error;
              return;
            }

            if (!data.insight) {
              outcomeDisplay.textContent = "No AI insight returned.";
              return;
            }

            outcomeDisplay.textContent = data.insight;
          })
          .catch((err) => {
            console.error("Error contacting Gemini backend:", err);
            outcomeDisplay.textContent = "❌ Error contacting AI backend.";
          });
      });

      // ===========================================================
      // FEATURE 2 — Emotional/Rational Classifier
      // ===========================================================
      document.getElementById("feature2Btn").addEventListener("click", () => {
        outcomeDisplay.textContent = "Analyzing emotional vs rational sentiment...";

        fetch("http://127.0.0.1:5000/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: eventUrl })
        })
          .then((res) => res.json())
          .then((data) => {
            console.log("Emotional backend:", data);
            if (data.message) {
              outcomeDisplay.textContent = data.message;
            } else {
              outcomeDisplay.textContent = "Analysis complete.";
            }
          })
          .catch((err) => {
            console.error("Error contacting emotional backend:", err);
            outcomeDisplay.textContent = "❌ Error contacting emotional backend.";
          });
      });

      // ===========================================================
      // FEATURE 3 — Steamroller Detector
      // ===========================================================
      document.getElementById("feature3Btn").addEventListener("click", () => {
        if (!slug) {
          outcomeDisplay.textContent = "Could not parse event slug.";
          return;
        }

        outcomeDisplay.textContent = "Checking steamroller risk...";

        const apiUrl = `http://127.0.0.1:5001/api/steamroller?slug=${encodeURIComponent(slug)}`;

        fetch(apiUrl)
          .then((res) => res.json())
          .then((data) => {
            console.log("Steamroller backend:", data);

            if (data.error) {
              outcomeDisplay.textContent = "Steamroller error: " + data.error;
              return;
            }

            const summary = data.steamroller_summary;
            if (summary && summary.human_message) {
              outcomeDisplay.textContent = summary.human_message;
            } else {
              outcomeDisplay.textContent = "No steamroller pattern detected.";
            }
          })
          .catch((err) => {
            console.error("Error contacting steamroller backend:", err);
            outcomeDisplay.textContent = "❌ Error contacting steamroller backend.";
          });
      });

    } else {
      document.body.innerHTML = `
        <p style="padding: 10px; font-family: sans-serif;">
          This extension only works on Polymarket event pages.
        </p>`;
    }
  });
});