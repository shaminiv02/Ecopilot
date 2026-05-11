// Function to extract context from the current page
function getPageContext() {
    let platform = window.location.hostname;
    let action_details = document.title; // In a real app, you'd scrape specific div elements (e.g., cart totals, destination inputs)
    
    // Hardcoding a test scenario if we are developing locally
    if (platform.includes("localhost") || platform.includes("127.0.0.1")) {
        platform = "RideSharingApp";
        action_details = "Looking for a ride from T-Nagar to Adyar during rush hour";
    }

    return { platform, action_details };
}

// Function to call our local FastAPI backend
async function fetchEcoNudge(context) {
    try {
        const response = await fetch("http://127.0.0.1:8000/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(context)
        });
        return await response.json();
    } catch (error) {
        console.error("EcoPilot Backend offline:", error);
        return null;
    }
}

// Function to inject the UI into the DOM
function injectWidget(data) {
    if (!data || data.status === "error") return;

    const widget = document.createElement("div");
    widget.id = "ecopilot-widget";

    widget.innerHTML = `
        <h3 class="ecopilot-header">🌱 EcoPilot Suggestion</h3>
        <p class="ecopilot-nudge">${data.nudge}</p>
        <div class="ecopilot-stats">
            <span>🌍 -${data.co2_saved}kg CO₂</span>
            <span>⏱️ +${data.time_impact} mins</span>
            <span>⭐ Score: ${data.eco_score}</span>
        </div>
        <button class="ecopilot-btn" onclick="document.getElementById('ecopilot-widget').remove()">
            Switch to: ${data.alternative}
        </button>
    `;

    document.body.appendChild(widget);
}

// Main execution flow
setTimeout(async () => {
    const context = getPageContext();
    const recommendation = await fetchEcoNudge(context);
    injectWidget(recommendation);
}, 2000); // Wait 2 seconds after page load to simulate context gathering