// require([
//     "esri/WebScene",
//     "esri/views/SceneView",
//     "esri/Graphic",
//     "esri/symbols/PointSymbol3D",
//     "esri/symbols/ObjectSymbol3DLayer",
//     "esri/geometry/Point"
// ], function (WebScene, SceneView, Graphic, PointSymbol3D, ObjectSymbol3DLayer, Point) {

//     // All your evacuee functions here...
//     window.lastClickedPoint = null;
//     let evacuees = {};
//     let isSimulationStarted = false;
//     let isPaused = false;
//     let currentStep = 0;
//     let simulationInterval = null;

//     const evacueeId = 1;
//     const lonStart = -117.19564100579537;
//     const latStart = 34.05609714289057;
//     const z = 15;

//     const lonEnd = lonStart + 0.0005;
//     const latEnd = latStart + 0.0005;
//     const totalSeconds = 15;
//     const intervalMs = 50;
//     const steps = (totalSeconds * 1000) / intervalMs;
//     const lonStep = (lonEnd - lonStart) / steps;
//     const latStep = (latEnd - latStart) / steps;

    
//     const webscene = new WebScene({ portalItem: { id: "7685f7ba6b47426ea20d6f640cf98596" } });
//     const view = new SceneView({ container: "map", map: webscene });

//     window.addEvacuee = (id, lon, lat, z) => {
//         const point = { type: "point", longitude: lon, latitude: lat, z: z, spatialReference: { wkid: 4326 } };
//         const symbol = {
//             type: "point-3d",
//             symbolLayers: [{
//                 type: "object", resource: { primitive: "sphere" },
//                 material: { color: "blue" }, height: 2, width: 2, depth: 2, anchor: "center"
//             }]
//         };
//         const graphic = new Graphic({ geometry: point, symbol: symbol });
//         view.graphics.add(graphic);
//         evacuees[id] = graphic;
//     };

//     window.moveEvacuee = (id, lon, lat, z, delayMs = 0) => {
//         const graphic = evacuees[id];
//         if (!graphic) return;
//         setTimeout(() => {
//             graphic.geometry = { type: "point", longitude: lon, latitude: lat, z: z, spatialReference: { wkid: 4326 } };
//         }, delayMs);
//     };

//     function runSimulationStep() {
//         if (currentStep > steps) {
//             clearInterval(simulationInterval);
//             console.log("Simulation complete.");
//             return;
//         }
//         const lonValue = lonStart + (lonStep * currentStep);
//         const latValue = latStart + (latStep * currentStep);
//         moveEvacuee(evacueeId, lonValue, latValue, z);
//         moveEvacuee(2, lonValue-0.0001, latValue-0.0001, z); 
//         moveEvacuee(3, lonValue+0.0001, latValue, z);
//         currentStep++;
//     }

//     function startSimulation() {
//         if (!isSimulationStarted) {
//             isSimulationStarted = true;
//             simulationInterval = setInterval(() => {
//                 if (!isPaused) {
//                     runSimulationStep();
//                 }
//             }, intervalMs);
//         }
//         else{
//             resumeSimulation();
//         }
//     }

//     function pauseSimulation() {
//         isPaused = true;
//     }

//     function resumeSimulation() {
//         if (isSimulationStarted && isPaused) {
//             isPaused = false;
//         }
//     }

    
//     evacueesList = [];
//     function addEvacueeToList(id, lon, lat, z) {
//         evacueesList.push({ id: id, lon: lon, lat: lat, z: z });
//     }
//     addEvacueeToList(1, -117.19564100579537, 34.05609714289057, z);
//     addEvacueeToList(2, -117.19564100579537-0.0001, 34.05609714289057-0.0001, z);
//     addEvacueeToList(3, -117.19564100579537+0.0001, 34.05609714289057, z);
//     // Add evacuee only after view is ready:
//     view.when(() => {
        
//         evacueesList.forEach(evacuee => {
//             addEvacuee(evacuee.id, evacuee.lon, evacuee.lat, evacuee.z);
//         });

//         // Button event handlers
//         document.getElementById('resumeBtn').addEventListener('click', startSimulation, console.log("Resume button clicked"));
//         document.getElementById('pauseBtn').addEventListener('click', pauseSimulation);
//         document.getElementById('stopBtn').addEventListener('click', () => {
//             window.location.href = 'http://localhost:5501/Code/frontend/dashboard/simulationHistory.html';
//         })
//     });

// });

import { playSimulation, pauseSimulation, setCurrentStep, handleControlButton, getIsPause, getCurrentStep } from "../map/mapSimulationPlaying.js";
import { addEvacuee, addFire } from "../map/mapGraphics.js";
import { closeMenu } from "../map/mapInteraction.js";

const evacueesGraphic = [];
const fireGraphic = [];
const evacueeMovement = [];
let totalSteps = 0;
const progressContainer = document.getElementById("progressContainer");
const progressBar = document.getElementById("progressBar");

let isDragging = false;
let simulationId = null;

// handle click
progressContainer.addEventListener("click", (e) => {
  const percent = getPercentage(e);
  console.log("Clicked:", percent + "%");
  updateProgress(percent);
  setCurrentStep(percent, totalSteps, evacueesGraphic, evacueeMovement);
});

// handle drag
progressContainer.addEventListener("mousedown", (e) => {
  isDragging = true;
  const percent = getPercentage(e);
  console.log("Start Drag:", percent + "%");
  updateProgress(percent);
});
window.addEventListener("mousemove", (e) => {
  if (isDragging) {
    const percent = getPercentage(e);
    console.log("Dragging:", percent + "%");
    updateProgress(percent);
  }
});
window.addEventListener("mouseup", () => {
  isDragging = false;
});

// function to get percentage
function getPercentage(e) {
  const rect = progressContainer.getBoundingClientRect();
  const offsetX = e.clientX - rect.left;
  let percent = (offsetX / rect.width) * 100;
  percent = Math.max(0, Math.min(100, percent)); // clamp between 0–100
  return Math.round(percent); // integer %
}

// update bar width
export function updateProgress(percent) {
  progressBar.style.width = percent + "%";
}

// update evacuees escaped number
export function updateEscapedNumber(num) {
    document.getElementById("evacueesText").innerHTML = "Evacuees Escaped : " + num + " / " + evacueeMovement.length + " evacuees";
}
// uodate time progress
export function updateTimeProgress(currentStep){
    const duration = totalSteps * 10 / 1000; 
    const minutes = Math.floor(duration / 60);
    const seconds = Math.floor(duration % 60);

    const currentDuration = currentStep * 10 / 1000; 
    const currentMinutes = Math.floor(currentDuration / 60);
    const currentSeconds = Math.floor(currentDuration % 60);

    // add leading zero if < 10
    const sec = seconds.toString().padStart(2, "0");
    const curSec = currentSeconds.toString().padStart(2, "0");

    document.getElementById("timeText").innerHTML =
        `${currentMinutes}:${curSec} / ${minutes}:${sec}`;
}

// update duration
function updateDuration() {
  const duration = totalSteps * 10 / 1000; // 10ms per stepl
  const minutes = Math.floor(duration / 60);
  const seconds = Math.floor(duration % 60);
  if (minutes == 0) {
    document.getElementById("durationText").innerHTML = "Duration: " + seconds + " seconds";

  }
  else{
    document.getElementById("durationText").innerHTML = "Duration: " + minutes + " minutes " + seconds + " seconds";
  }
}


// Button event handlers
document.getElementById('resumeBtn').addEventListener('click', () => {
    console.log("Resume button clicked");
    // startSimulation(evacueesGraphic, evacueeMovement);
    handleControlButton(evacueesGraphic, evacueeMovement, 10);
});
// document.getElementById('pauseBtn').addEventListener('click', pauseSimulation);
document.getElementById('stopBtn').addEventListener('click', () => {
    window.location.href = 'http://localhost:5501/Code/frontend/html/simulationHistory.html';
})

export function setPauseButton(){
    document.getElementById('resumeBtn').innerHTML = "&#9208;";
}

export function setResumeButton(){
    document.getElementById('resumeBtn').innerHTML = "&#9654;";
}

export function setReplayButton(){
    document.getElementById('resumeBtn').innerHTML = "&#10226;";
}

document.addEventListener("DOMContentLoaded", async () => {
    const loadingElement = document.getElementById("loadingModal"); 
    // hide the loading element
    loadingElement.style.display = "flex";
    const params = new URLSearchParams(window.location.search);
    simulationId = params.get("simulationId");
    console.log(simulationId);
    fetch(`http://localhost:5000/get_simulation_data?simulation_id=${simulationId}`, { 
        method: 'GET',
        credentials: 'include'
    })
    .then(response => {
      console.log("Status:", response.status);
      return response.json();
    })
    .then(data => {

        // console.log(data);
        console.log(data.length);
        loadingElement.style.display = "none";

        // render the metadata
        document.getElementById("simulationNameText").innerHTML += data.simulation_metadata.Simulation_Name;

        data.evacuees.forEach(ev => {
            console.log(ev);
            const evacueeGraphicAdded =addEvacuee(ev.Longitude, ev.Latitude, ev.Z);
            evacueesGraphic.push(evacueeGraphicAdded);

            // flatten all route arrays first
            const allRoutes = data.evacuees_routes.flatMap(r => r.route);

            // get all the route points for this evacuee
            const routePoints = allRoutes.filter(rp => rp.Evacuee_Id === ev.Evacuee_Id);

            // sort the route points by Step_Order
            routePoints.sort((a, b) => a.Step_Order - b.Step_Order);

            evacueeMovement.push(routePoints);
            totalSteps = Math.max(totalSteps, routePoints.length);
        });
    
        // console.log(evacueeMovement);

        data.hazards.forEach(hz => {
            // console.log(hz);
            const fireGraphicAdded = addFire(hz.Longitude, hz.Latitude, hz.Z);
            fireGraphic.push(fireGraphicAdded);
        });

        // update the progress bar, escaped number and duration
        updateProgress(0);
        updateEscapedNumber(0);
        updateDuration();

        // startSimulation
        playSimulation(evacueesGraphic, evacueeMovement, 10);
    })
    .catch(error => console.error('Error:', error)); 
    console.log("done")
});

let pendingPoint = null;
let isPaused = null;
// function to handle onclick add fire
document.getElementById('addFireBtn').addEventListener('click', () => {
  const { longitude, latitude, z } = window.lastClickedPoint;
  pendingPoint = { longitude, latitude, z };
  isPaused = getIsPause();
  // ask user for confirmation
  document.getElementById('confirmAddingMenuId').style.display = 'block';
  pauseSimulation();

  // const confirmAddBtn = document.getElementById('confirmAddBtn');
  // const cancelAddBtn = document.getElementById('cancelAddBtn');

  // window.lastClickedPoint = null;
  closeMenu();
});

confirmAddBtn.addEventListener('click', () => {
  // const { longitude, latitude, z } = window.lastClickedPoint;
  console.log(pendingPoint.longitude, pendingPoint.latitude, pendingPoint.z);
  // addFire(pendingPoint.longitude, pendingPoint.latitude, pendingPoint.z);

  let currentStep = getCurrentStep();

  // console.log(currentStep);
  // console.log(simulationId);

  regenerateSimulation(currentStep, "fire", pendingPoint);
  
  document.getElementById('confirmAddingMenuId').style.display = 'none';
});

cancelAddBtn.addEventListener('click', () => {
  document.getElementById('confirmAddingMenuId').style.display = 'none';

  // if the previous playing mode is play, resume the simulation
  if(isPaused === false){
    handleControlButton(evacueesGraphic, evacueeMovement, 10);
  }
});

// function to call the backend to add the new dynamic hazard to the simulation
function regenerateSimulation(currentStep, hazardType, hazardPosition) {
  const loadingElement = document.getElementById("loadingModal"); 
  // change the text to generating
  const loadingText = loadingElement.querySelector("p");
  loadingText.textContent = "Regenerating...";
  // show the loading element
  loadingElement.style.display = "flex";
  
  // call the backend to start the new simulation
  fetch('http://localhost:5000/add_dynamic_hazards', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      simulationId: simulationId,
      currentStep: currentStep,
      hazardType: hazardType,
      hazardPosition: hazardPosition
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log('Simulation started:', data);
    if (data.success) {
      // Refresh after a short delay so backend has time to update
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } else {
      alert('Failed to regenerate simulation: ' + data.message);
    }
  })
  .catch(error => {
    console.error('Error starting simulation:', error);
  })
  .finally(() => {
    loadingElement.style.display = "none";
  });
}