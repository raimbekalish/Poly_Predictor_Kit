// --- Your Feature Functions ---
// Put your logic for each feature here.
// They receive the URL and should return a string to display.

function doFeature1(url) {
  console.log("Feature 1 processing URL:", url);
  // Example: Just return a success message
  return "Feature 1: Success!";
}

function doFeature2(url) {
  console.log("Feature 2 processing URL:", url);
  return "Feature 2: Done!";
}

function doFeature3(url) {
  console.log("Feature 3 processing URL:", url);
  return "Feature 3: Complete!";
}

// --- Main Setup ---
// This runs as soon as the popup is opened.

document.addEventListener("DOMContentLoaded", () => {
  // Get the HTML element where we will show the outcome
  const outcomeDisplay = document.getElementById("outcome");

  // Query Chrome for the active tab
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const currentTab = tabs[0];
    
    // Check if we got a tab and it's a Polymarket event
    if (currentTab && currentTab.url && currentTab.url.includes("polymarket.com/event/")) {
      
      const eventUrl = currentTab.url;
      
      // Log the URL to the *extension's* console
      // (See note below on how to open this)
      console.log("Polymarket Event URL:", eventUrl);
      
      // --- Wire up the buttons ---
      
      document.getElementById("feature1Btn").addEventListener("click", () => {
        // Call your feature function and pass it the URL
        const result = doFeature1(eventUrl);
        // Display the outcome in the HTML
        outcomeDisplay.textContent = result;
      });
      
      document.getElementById("feature2Btn").addEventListener("click", () => {
        const result = doFeature2(eventUrl);
        outcomeDisplay.textContent = result;
      });
      
      document.getElementById("feature3Btn").addEventListener("click", () => {
        const result = doFeature3(eventUrl);
        outcomeDisplay.textContent = result;
      });
      
    } else {
      // Not on the right page
      document.body.innerHTML = `<p style="padding: 10px; font-family: sans-serif;">This extension only works on a polymarket.com event page.</p>`;
    }
  });
});