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
        if (!response.ok) {
            console.error('EcoPilot backend returned non-OK status', response.status);
            return { status: 'error', message: `Backend error ${response.status}` };
        }
        return await response.json();
    } catch (error) {
        console.error("EcoPilot Backend offline:", error);
        return { status: 'error', message: String(error) };
    }
}

// Function to inject the UI into the DOM
function injectWidget(data) {
    if (!data) return;
    if (data.status === "error") {
        console.error('EcoPilot error:', data.message || data);
        return;
    }

    const widget = document.createElement("div");
    widget.id = "ecopilot-widget";

    widget.innerHTML = `
        <h3 class="ecopilot-header">🌱 EcoPilot Suggestion</h3>
        <p class="ecopilot-nudge">${data.nudge || ''}</p>
        <div class="ecopilot-stats">
            <span>🌍 -${data.co2_saved ?? 0}kg CO₂</span>
            <span>⏱️ ${data.time_impact ?? 0} mins</span>
            <span>⭐ Score: ${data.eco_score ?? 'N/A'}</span>
        </div>
        <button class="ecopilot-btn">Switch to: ${data.alternative || 'Alternative'}</button>
    `;

    document.body.appendChild(widget);

    // Attach event listener to button (avoid inline onclick handlers)
    const btn = widget.querySelector('.ecopilot-btn');
    if (btn) {
        btn.addEventListener('click', () => {
            widget.remove();
        });
    }
}

// Main execution flow
// Start after DOM is ready
console.log('EcoPilot content script loaded for', window.location.href);
window.addEventListener('load', () => {
    setTimeout(async () => {
        try {
            const context = getPageContext();
            console.log('EcoPilot context:', context);
            const recommendation = await fetchEcoNudge(context);
            console.log('EcoPilot recommendation:', recommendation);
            injectWidget(recommendation);
        } catch (err) {
            console.error('EcoPilot unexpected error:', err);
        }
    }, 1200);
});