// Arrays to store selected choices
const days = JSON.parse(sessionStorage.getItem("days") || "[]");
const sessions = JSON.parse(sessionStorage.getItem("sessions") || "[]");
let selectedDays = days;
let selectedSessions = sessions;

console.log("Days:", selectedDays);
console.log("Sessions:", selectedSessions);

// Get all day and session buttons
const dayButtons = document.querySelectorAll(".simulation-item.days .selectBtn");
const sessionButtons = document.querySelectorAll(".simulation-item.sessions .selectBtn");

// Helper: toggle selection
function toggleSelection(button, list) {
    const value = button.textContent.trim();

    if (list.includes(value)) {
        // If already selected -> unselect
        list.splice(list.indexOf(value), 1);
        button.classList.remove("selected");
    } else {
        // If not selected -> add
        list.push(value);
        button.classList.add("selected");
    }
}
function updateSimCount() {
    const total = selectedDays.length * selectedSessions.length;
    document.getElementById("simCount").textContent = 
        `${total} Simulation${total !== 1 ? "s" : ""} Selected`;
}

// Update count whenever selections change
dayButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        toggleSelection(btn, selectedDays);
        updateSimCount();
    });
});

sessionButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        toggleSelection(btn, selectedSessions);
        updateSimCount();
    });
});


// Example: when generating simulations
document.getElementById("generateSimBtn").addEventListener("click", () => {
    console.log("Selected Days:", selectedDays);
    console.log("Selected Sessions:", selectedSessions);

    // Generate combinations
    let simulations = [];
    selectedDays.forEach(day => {
        selectedSessions.forEach(session => {
            simulations.push({ day, session });
        });
    });

    console.log("Generated Simulations:", simulations);

    sessionStorage.setItem("days", JSON.stringify(selectedDays));
    sessionStorage.setItem("sessions", JSON.stringify(selectedSessions));

    window.location.href = 'http://localhost:5501/Code/frontend/html/landingPage.html';

});
function initializeSelections() {
    dayButtons.forEach(btn => {
        const value = btn.textContent.trim();
        if (selectedDays.includes(value)) {
            btn.classList.add("selected");
        }
    });

    sessionButtons.forEach(btn => {
        const value = btn.textContent.trim();
        if (selectedSessions.includes(value)) {
            btn.classList.add("selected");
        }
    });

    // Update sim count initially
    updateSimCount();
}

// Call this once on page load
initializeSelections();
