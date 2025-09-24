import { addFire , addEvacuee} from "../map/mapGraphics.js";
import { closeMenu } from "../map/mapInteraction.js";
window.lastClickedPoint = null;
const days = JSON.parse(sessionStorage.getItem("days") || "[]");
const sessions = JSON.parse(sessionStorage.getItem("sessions") || "[]");

const isSessionSimulation = days.length > 0 && sessions.length > 0;
if (isSessionSimulation) {
    // document.getElementById('customSimPanel').style.display = 'none';
    // document.getElementById('sessionNameInput').style.display = 'inline-block';
    document.getElementById('sessionSelectButton').innerHTML += '('+days.length*sessions.length + ' simulations selected)';
}
console.log("Days:", days);
console.log("Sessions:", sessions);

const evacuuesAdded = [];
const hazardsAdded = [];


document.addEventListener("DOMContentLoaded", function () {

   
    // evacuee count
    const evacueeCountInput = document.getElementById("evacueeCountInput");
    
    // if the input is more than 10, put it as 10
    evacueeCountInput.addEventListener("blur", function () {
      let value = parseInt(evacueeCountInput.value, 10);
    
      if (isNaN(value) || value < 1) {
        value = 1;
      } else if (value > 10) {
        value = 10;
      }
    
      evacueeCountInput.value = value;
    });

    // Close button
    const closeBtn = document.getElementById("closeMenuBtn");
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        closeMenu();
      });
    }
  
    // Add Evacuee button
    const addEvacueeBtn = document.getElementById("addEvacueeBtn");
    if (addEvacueeBtn) {
      addEvacueeBtn.addEventListener("click", function () {
        const { longitude, latitude, z } = window.lastClickedPoint;
        const count = parseInt(evacueeCountInput.value, 10) || 1;
      
        // radius around the clicked point (adjust to suit your map scale)
        const radius = 0.00002; 
        addEvacuee(longitude, latitude, z);
      
          // add evacuee in the list
        evacuuesAdded.push({ longitude: longitude, latitude: latitude, z });
        for (let i = 0; i < count-1; i++) {
          // random offset inside a circle
          const angle = Math.random() * 2 * Math.PI;
          const distance = Math.random() * radius;
          const offsetLon = longitude + Math.cos(angle) * distance;
          const offsetLat = latitude + Math.sin(angle) * distance;
      
          // add evacuee in the map
          addEvacuee(offsetLon, offsetLat, z);
      
          // add evacuee in the list
          evacuuesAdded.push({ longitude: offsetLon, latitude: offsetLat, z });
        }
      
        closeMenu();
      });
      
    }

    // Add Fire button
    const addFireBtn = document.getElementById("addFireBtn");
    if (addFireBtn) {
      console.log("addFireBtn found ");
      addFireBtn.addEventListener("click", function () {
        console.log("addFireBtn clicked");
        const { longitude, latitude, z } = window.lastClickedPoint;

        // add fire in the map
        addFire(longitude, latitude, z);

        // add fire in the list
        hazardsAdded.push({hazard_type: "fire",longitude, latitude, z });

        closeMenu();
      });
    }
  });

  

  
  window.onload = function() {
    console.log("loadeddddddddddddddddddddddddddddddddddddddddddddddddddd");
    fetch('http://localhost:5000/login/status', {
        credentials: 'include' // Important: sends cookies (session)
    })
    .then(response => response.json())
    .then(data => {
        if (data.logged_in) {
            console.log(data);
            
            document.getElementById('signInButton').style.display = 'none';
            document.getElementById('historyButton').style.display = 'inline-block';
            document.getElementById('usernameText').innerText = data.user.name; 
            document.getElementById('usernameText').style.display = 'inline-block';

            console.log(data.user_roles);
            if(data.user_roles === 'Admin') {
                document.getElementById('userManagementText').style.display = 'inline-block';
            } else {
                document.getElementById('userManagementText').style.display = 'none';
            }
        } else {
            document.getElementById('signInButton').style.display = 'inline-block';
            document.getElementById('historyButton').style.display = 'none';
            document.getElementById('usernameText').style.display = 'none';
            document.getElementById('userManagementText').style.display = 'none';
        }
    })
    .catch(err => {
        console.error('Error checking login status:', err);
    })
  };

document.getElementById('signInButton').addEventListener('click', function() {
   window.location.href = 'http://localhost:5501/Code/frontend/auth/login.html';
});

document.getElementById('historyButton').addEventListener('click', function() {
    window.location.href = 'http://localhost:5501/Code/frontend/html/simulationHistory.html';
});

document.getElementById('userManagementText').addEventListener('click', function() {
  window.location.href = 'http://localhost:5501/Code/frontend/userManagement/userManagement.html';
});
  
document.getElementById('customSimButton').addEventListener('click', function() {
  const customSimData = {
    simulationName: document.getElementById('customNameInput').value,
    evacuees: evacuuesAdded,
    hazards: hazardsAdded,
  };
  console.log(customSimData.simulationName);
    // Show loading modal
    document.getElementById("loadingModal").style.display = "flex";
    fetch('http://localhost:5000/create_custom_sim', {
      credentials: 'include', // Important: sends cookies (session)
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify(customSimData),
    })
    .then(response => response.json())
    .then(data => {
      console.log(data);
      console.log(data.simulation_id);
        const simulationId = data.simulation_id;
        window.location.href = "http://localhost:5501/Code/frontend/html/simulationPlaying.html?simulationId=" + simulationId;


    })
    .catch((error) => {
        console.error('Error:', error);
    });
});

document.getElementById('sessionSelectButton').addEventListener('click', function() {
  window.location.href = 'http://localhost:5501/Code/frontend/html/selectDayAndSession.html';
});

document.getElementById('sessionSimButton').addEventListener('click', function() {
  const sessionSimData = {
    simulationName: document.getElementById('sessionNameInput').value,
    evacuees: evacuuesAdded,
    hazards: hazardsAdded,
  };
  console.log(sessionSimData.simulationName);
    fetch('http://localhost:5000/create_custom_sim', {
      credentials: 'include', // Important: sends cookies (session)
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify(customSimData),
    })
    .then(response => response.json())
    .then(data => {
      console.log(data);
      console.log(data.simulation_id);
        const simulationId = data.simulation_id;
        window.location.href = "http://localhost:5501/Code/frontend/html/simulationPlaying.html?simulationId=" + simulationId;


    })
    .catch((error) => {
        console.error('Error:', error);
    });
});