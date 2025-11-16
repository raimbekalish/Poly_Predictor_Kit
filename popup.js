document.addEventListener('DOMContentLoaded', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs || tabs.length === 0) {
      showError("Could not get active tab.");
      return;
    }

    const urlString = tabs[0].url;
    const slug = getSlugFromUrl(urlString);

    if (slug) {
      fetchSteamrollerData(slug);
    } else {
      showError("Not a valid Polymarket event page. Please navigate to a page like '/event/slug-name'.");
    }
  });
});

function getSlugFromUrl(urlString) {
  try {
    const url = new URL(urlString);
    if (!url.hostname.endsWith("polymarket.com")) {
      return null;
    }
    const pathParts = url.pathname.split('/');
    const eventIndex = pathParts.indexOf('event');
    if (eventIndex !== -1 && pathParts.length > eventIndex + 1) {
      return pathParts[eventIndex + 1] || null;
    }
    return null;
  } catch (e) {
    return null;
  }
}

async function fetchSteamrollerData(slug) {
  const serverUrl = `http://localhost:5001/api/steamroller?slug=${slug}`;

  try {
    const response = await fetch(serverUrl);

    if (!response.ok) {
      const errorText = await response.text();
      showError(`Server error (${response.status}): ${errorText}`);
      return;
    }

    const data = await response.json();
    displayAnalysis(data);

  } catch (e) {
    console.error("Fetch error:", e);
    showError("Failed to connect to the server. Make sure your Python server is running on 'http://localhost:5001'.");
  }
}

function showError(message) {
  document.getElementById('loading').style.display = 'none';
  const errorContainer = document.getElementById('error-container');
  errorContainer.innerHTML = `<p class="error">${message}</p>`;
}

function displayAnalysis(data) {
  // Hide loading and show results
  document.getElementById('loading').style.display = 'none';
  document.getElementById('results-container').style.display = 'block';

  // 1. Set Market Title
  document.getElementById('title').textContent = data.market_title || 'Market Analysis';

  // 2. Build Summary Box
  const summary = data.steamroller_summary;
  const summaryBox = document.getElementById('summary');
  const summaryMessage = document.getElementById('summary-message');

  if (summary) {
    summaryMessage.textContent = summary.human_message || "No steamroller risk detected.";

    // Add risk-based color
    const risk = summary.overall_risk || "unknown"; // high, medium, low
    summaryBox.classList.add(`risk-${risk}`);
  }

  // 3. Build Outcome Boxes
  const outcomesContainer = document.getElementById('outcomes');
  outcomesContainer.innerHTML = ''; // Clear any old content

  if (data.outcomes) {
    for (const outcomeName in data.outcomes) {
      const outcome = data.outcomes[outcomeName];

      // Format data for display
      const probability = (outcome.probability * 100).toFixed(1);
      const wipeout = outcome.wipeout_factor.toFixed(1);
      const gain = outcome.max_gain_per_1.toFixed(2);
      const loss = outcome.max_loss_per_1.toFixed(2);
      const days = outcome.days_left.toFixed(1);

      // Create the HTML for one outcome box
      const outcomeBox = document.createElement('div');
      outcomeBox.className = 'outcome';
      outcomeBox.innerHTML = `
        <div class="outcome-header">
          <span class="outcome-name">${outcomeName}</span>
          <span class="outcome-prob outcome-prob-${outcomeName}">${probability}%</span>
        </div>
        <div class="metrics">
          <p><strong>Wipeout Factor:</strong> ${wipeout}x</p>
          <p><strong>Max Gain (per $1):</strong> $${gain}</p>
          <p><strong>Max Loss (per $1):</strong> $${loss}</p>
          <p><strong>Days Left:</strong> ${days}</p>
          <p><strong>Risk Shape:</strong> ${outcome.risk_label} / <strong>Time Risk:</strong> ${outcome.time_risk}</p>
        </div>
      `;

      outcomesContainer.appendChild(outcomeBox);
    }
  }
}