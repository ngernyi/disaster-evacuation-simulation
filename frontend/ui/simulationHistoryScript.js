// declare global variables
let listOfSimulations = [];
let listToShow = [];
let currentSort = "date";
let currentKeyword = "";

// Fetch and render simulations on page load
window.onload = function() {
    fetch('http://localhost:5000/get_user_simulations', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        listOfSimulations = data.simulations.map(sim => ({
            id: sim.Simulation_Id,
            name: sim.Simulation_Name || 'Unnamed Simulation',
            date: sim.Created_At,
            duration: sim.Computational_Time ? parseFloat(sim.Computational_Time) : 0
        }));

        updateListToShow();
        renderSimulations();
    })
    .catch(error => console.error('Error:', error));
};

// to sort the list to show
function sortSimulations(list) {
    let sorted = [...list];
    if (currentSort === 'date') {
        sorted.sort((a, b) => new Date(b.date) - new Date(a.date));
    } else if (currentSort === 'name') {
        sorted.sort((a, b) => a.name.localeCompare(b.name));
    } else if (currentSort === 'duration') {
        sorted.sort((a, b) => b.duration - a.duration);
    }
    return sorted;
}

// to update the list to show
function updateListToShow() {

    // filter by keywords
    if (currentKeyword) {
        listToShow = listOfSimulations.filter(sim =>
            sim.name.toLowerCase().includes(currentKeyword.toLowerCase()) ||
            new Date(sim.date).toLocaleDateString().toLowerCase().includes(currentKeyword.toLowerCase()) ||
            sim.duration.toString().includes(currentKeyword)
        );
    } 
    else {
        listToShow = [...listOfSimulations];
    }

    // sort
    listToShow = sortSimulations(listToShow);

}

function renderSimulations() {
    const simulationsList = document.querySelector('.simulation-list');
    simulationsList.innerHTML = '';

    if (listToShow.length === 0) {
        const noResult = document.createElement('div');
        noResult.style.paddingLeft = '20px';
        noResult.style.paddingTop = '20px';
        noResult.classList.add('no-result');
        noResult.textContent = 'No result found';
        simulationsList.appendChild(noResult);
        return;
    }

    if (currentSort === 'date') {
        // Grouped by Date (old way)
        const groupedByDate = {};
        listToShow.forEach(sim => {
            const date = new Date(sim.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
            if (!groupedByDate[date]) groupedByDate[date] = [];
            groupedByDate[date].push(sim);
        });

        for (const date in groupedByDate) {
            const dateGroup = document.createElement('div');
            dateGroup.classList.add('date-group');

            const dateHeader = document.createElement('div');
            dateHeader.classList.add('date-header');
            dateHeader.textContent = date;
            dateGroup.appendChild(dateHeader);

            groupedByDate[date].forEach(sim => {
                const simItem = createSimulationItem(sim);
                dateGroup.appendChild(simItem);
            });

            simulationsList.appendChild(dateGroup);
        }
    } else {
        // Flat list (no grouping) but show Date per item
        listToShow.forEach(sim => {
            
                const dateGroup = document.createElement('div');
                dateGroup.classList.add('date-group');

                const dateHeader = document.createElement('div');
                dateHeader.classList.add('date-header');
                dateHeader.textContent = new Date(sim.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
                const simItem = createSimulationItem(sim);

                dateGroup.appendChild(dateHeader);
                dateGroup.appendChild(simItem);

                simulationsList.appendChild(dateGroup);
            
        });
    }
}


// Helper function to create simulation item (reusable)
function createSimulationItem(sim) {
    const simItem = document.createElement('div');
    simItem.classList.add('simulation-item');

    const simInfo = document.createElement('div');
    simInfo.classList.add('simulation-info');

    const simTitle = document.createElement('div');
    simTitle.classList.add('simulation-title');
    simTitle.textContent = sim.name;

    const duration = document.createElement('div');
    duration.classList.add('duration');
    duration.textContent = `Duration: ${Math.floor(sim.duration / 60)}m ${Math.floor(sim.duration % 60)}s`;

    simInfo.appendChild(simTitle);
    simInfo.appendChild(duration);

    const simActions = document.createElement('div');
    simActions.classList.add('simulation-actions');

    const replayBtn = document.createElement('button');
    replayBtn.classList.add('replay-btn');
    replayBtn.innerHTML = '<span class="play-icon"></span>Replay';
    replayBtn.addEventListener('click', () => {
        console.log(`Replay Simulation ID: ${sim.id}`);
        window.location.href = "http://localhost:5501/Code/frontend/html/simulationPlaying.html?simulationId=" + sim.id;

    });

    const menuContainer = document.createElement('div');
    menuContainer.classList.add('menu-container');

    const menuBtn = document.createElement('button');
    menuBtn.classList.add('menu-btn');
    menuBtn.textContent = '⋮';

    const menuOptions = document.createElement('div');
    menuOptions.classList.add('menu-options');
    menuOptions.style.display = 'none';

    const renameOption = document.createElement('div');
    renameOption.classList.add('menu-option', 'rename');
    renameOption.textContent = 'Rename';

    const deleteOption = document.createElement('div');
    deleteOption.classList.add('menu-option', 'delete');
    deleteOption.textContent = 'Delete';

    renameOption.addEventListener('click', () => {
        renameSimulation(simItem, sim.id, sim.name);
    });

    deleteOption.addEventListener('click', () => {
        deleteSimulation(simItem, sim.id, sim.name);
    });

    simTitle.addEventListener('click', () => {
        showEvaluation(simItem, sim.id, sim.name);
    });

    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.menu-options').forEach(menu => {
            if (menu !== menuOptions) menu.style.display = 'none';
        });
        menuOptions.style.display = (menuOptions.style.display === 'block') ? 'none' : 'block';
    });

    menuOptions.appendChild(renameOption);
    menuOptions.appendChild(deleteOption);
    menuContainer.appendChild(menuBtn);
    menuContainer.appendChild(menuOptions);

    simActions.appendChild(replayBtn);
    simActions.appendChild(menuContainer);

    simItem.appendChild(simInfo);
    simItem.appendChild(simActions);

    return simItem;
}


function showEvaluation(simItem, simId, simName) {
    console.log(`Evaluation Simulation ID: ${simId}`);
    const modal = document.getElementById('evaluationBoard');
    modal.style.display = 'block';

    const evaluationSimulationName = document.getElementById('evaluationSimulationName');
    const evaluatioDurationValue = document.getElementById('evaluationDurationValue');
    const evaluationEvacueesValue = document.getElementById('evaluationEvacueesValue');
    const evaluationHazardsValue = document.getElementById('evaluationHazardsValue');
    const evaluationComputationalTimeValue = document.getElementById('evaluationComputationalTimeValue');
    const closeEvaluationBtn = document.getElementById('closeEvaluationBtn');

    // fetch the data
    fetch('http://localhost:5000/get_simulation_data?simulation_id='+simId, {
        credentials: 'include',
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json()).then(data => {
        console.log(data);
        let maxLength = 0;
        for (const evacuation of data.evacuees_routes) {
            if (evacuation.route.length > maxLength) {
                maxLength = evacuation.route.length;
            }   
        }
        const duration = maxLength * 100 / 1000; 
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        let durationText = `${minutes}m ${seconds}s`;
        if(minutes === 0) durationText = `${seconds}s`;

        evaluationSimulationName.textContent = simName;
        evaluatioDurationValue.textContent = durationText;
        evaluationEvacueesValue.textContent = data.evacuees.length;
        evaluationHazardsValue.textContent = data.hazards.length;
        evaluationComputationalTimeValue.textContent = data.simulation_metadata.Computational_Time;
    })
    

    // handle close
    const closeEvaluation = () => {
        modal.style.display = 'none';
    }
    closeEvaluationBtn.addEventListener('click', closeEvaluation);

    // display data
    evaluationSimulationName.textContent = simName;
    evaluatioDurationValue.textContent = simItem.Computational_Time;
    evaluationEvacueesValue.textContent = simItem.Evacuees;
    evaluationHazardsValue.textContent = simItem.Hazards;
    evaluationComputationalTimeValue.textContent = simItem.Computational_Time;
}

// rename a simulation
function renameSimulation(simItem, simId, simName){
    const modal = document.getElementById('renameModal');
    const confirmBtn = document.getElementById('confirmRenameBtn');
    const cancelBtn = document.getElementById('cancelRenameBtn');
    const renameInput = document.getElementById('renameInput');
    modal.style.display = 'block';

    renameInput.value = simName;

    const confirmHandler = () => {
        const newName = renameInput.value;
        fetch('http://localhost:5000/rename_simulation', {
            credentials: 'include',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ simulation_id: simId, new_name: newName })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                simItem.name = newName; // Update the name in the DOM; 
                console.log(`Renamed Simulation ID ${simId}`);

                // update the list of simulations
                const simObj = listOfSimulations.find(item => item.id === simId);
                if (simObj) simObj.name = newName;

                // update the list to show
                updateListToShow();
                renderSimulations();
            } else {
                alert('Failed to delete simulation: ' + result.message);
            }
        })
        .catch(err => {
            console.error('Error deleting simulation:', err);
            alert('Error occurred while deleting.');
        });

        modal.style.display = 'none';
        confirmBtn.removeEventListener('click', confirmHandler);
        cancelBtn.removeEventListener('click', cancelHandler);
    };

    const cancelHandler = () => {
        modal.style.display = 'none';
        confirmBtn.removeEventListener('click', confirmHandler);
        cancelBtn.removeEventListener('click', cancelHandler);
    };

    confirmBtn.addEventListener('click', confirmHandler);
    cancelBtn.addEventListener('click', cancelHandler);


}

// delete a simulation
function deleteSimulation(simItem,simId, simName) {
    const modal = document.getElementById('deleteModal');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const cancelBtn = document.getElementById('cancelDeleteBtn');
    const simNameDisplay = document.getElementById('deleteSimulationName');
    modal.style.display = 'block';
    simNameDisplay.textContent = simName;


    const confirmHandler = () => {
        simItem.remove();
        console.log(`Deleted Simulation ID: ${simId}`);
        // update in database
        fetch('http://localhost:5000/delete_simulation', {
            credentials: 'include',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ simulation_id: simId })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // remove the simulation from the list of simulations
                listOfSimulations = listOfSimulations.filter(item => item.id !== simId);
                
                // update the list to show
                updateListToShow();
                renderSimulations();
            } else {
                alert('Failed to delete simulation: ' + result.message);
            }
        })
        .catch(err => {
            console.error('Error deleting simulation:', err);
            alert('Error occurred while deleting.');
        });
        
        modal.style.display = 'none';

        // Clean up event listeners
        confirmBtn.removeEventListener('click', confirmHandler);
        cancelBtn.removeEventListener('click', cancelHandler);
    };

    const cancelHandler = () => {
        modal.style.display = 'none';
        confirmBtn.removeEventListener('click', confirmHandler);
        cancelBtn.removeEventListener('click', cancelHandler);
    };

    confirmBtn.addEventListener('click', confirmHandler);
    cancelBtn.addEventListener('click', cancelHandler);
}


// Close menus when clicking outside
window.addEventListener('click', () => {
    document.querySelectorAll('.menu-options').forEach(menu => {
        menu.style.display = 'none';
    });
});

// Dropdown sorting functionality
const sortBtn = document.getElementById('sortBtn');
const sortDropdown = document.getElementById('sortDropdown');

sortBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    sortDropdown.style.display = (sortDropdown.style.display === 'block') ? 'none' : 'block';
    const rect = sortBtn.getBoundingClientRect();
    sortDropdown.style.position = 'absolute';
    sortDropdown.style.left = `${rect.left}px`;
    sortDropdown.style.top = `${rect.bottom}px`;
});

window.addEventListener('click', (e) => {
    if (!sortBtn.contains(e.target)) sortDropdown.style.display = 'none';
});


// Sort input
document.querySelectorAll('#sortDropdown li').forEach(item => {
    item.addEventListener('click', function() {
        const sortBy = this.getAttribute('data-sort');
        currentSort = sortBy;
        sortBtn.innerHTML = `Sort By: ${sortBy.charAt(0).toUpperCase() + sortBy.slice(1)} <span class="dropdown-arrow"></span>`;
        sortDropdown.style.display = 'none';

        updateListToShow();
        renderSimulations();
    });
});

// Search bar input
const searchInput = document.querySelector('.search-input');
searchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase();
    currentKeyword = query;
    updateListToShow();
    renderSimulations();
});

// Logout
const logoutBtn = document.querySelector('.btn-secondary');
logoutBtn.addEventListener('click', function() {
    window.location.href = 'http://localhost:5000/logout';
});

// Generate Simulation
const generateSimulationBtn = document.querySelector('.btn-primary');
generateSimulationBtn.addEventListener('click', function() {
    window.location.href = 'http://localhost:5501/Code/frontend/html/landingPage.html';
});



// export pdf
const exportPdfBtn = document.getElementById('exportPdfBtn');
exportPdfBtn.addEventListener('click', function() {
    fetch('http://localhost:5000/export_pdf', { method: 'GET' })
    .then(response => response.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "analytic report.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
    })
    .catch(err => console.error("PDF export failed:", err));
})

const exportCSVBtn = document.getElementById('exportCsvBtn');
exportCSVBtn.addEventListener('click', function() {
    fetch('http://localhost:5000/export_csv', { method: 'GET' })
    .then(response => response.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "analytic report.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
    })
    .catch(err => console.error("CSV export failed:", err));
})