window.lastClickedPoint = null;

import WebScene from "https://js.arcgis.com/4.32/@arcgis/core/WebScene.js";
import SceneView from "https://js.arcgis.com/4.32/@arcgis/core/views/SceneView.js";

export const webscene = new WebScene({
  portalItem: {
    id: "7685f7ba6b47426ea20d6f640cf98596"
  }
});

const view = new SceneView({
  container: "map",
  map: webscene
});

window.mapView = view;

  
// // show the menu
// function showMenu(menuElement, clickX, clickY) {
//     const menuHeight = menuElement.offsetHeight;
//     const menuWidth = menuElement.offsetWidth;
//     const viewportHeight = window.innerHeight;
//     const viewportWidth = window.innerWidth;
  
//     // Calculate vertical position
//     let topPosition = clickY;
//     const spaceBelow = viewportHeight - clickY;
//     if (spaceBelow < menuHeight) {
//       topPosition = clickY - menuHeight;
//       if (topPosition < 0) topPosition = 0;
//     }
  
//     // Calculate horizontal position to prevent overflow
//     let leftPosition = clickX;
//     const spaceRight = viewportWidth - clickX;
//     if (spaceRight < menuWidth) {
//       leftPosition = clickX - menuWidth;
//       if (leftPosition < 0) leftPosition = 0;
//     }
  
//     menuElement.style.top = `${topPosition}px`;
//     menuElement.style.left = `${leftPosition}px`;
//     menuElement.style.display = "block";
//   }
  
// // close the menu
// function closeMenu() {
//     const addMenu = document.getElementById("addMenuu");
//     addMenu.style.display = "none";
// }

// // close the menu when clicking outside of it
// // window.addEventListener("click", function(event) {
// //     closeMenu();
// // });

// document.addEventListener("DOMContentLoaded", function () {
//     // Close button
//     const closeBtn = document.getElementById("closeMenuBtn");
//     if (closeBtn) {
//       closeBtn.addEventListener("click", function () {
//         closeMenu();
//       });
//     }
  
//     // Add Evacuee button
//     const addEvacueeBtn = document.getElementById("addEvacueeBtn");
//     if (addEvacueeBtn) {
//       addEvacueeBtn.addEventListener("click", function () {
//         const { longitude, latitude,  } = window.lastClickedPoint;
//         addEvacuee(longitude, latitude, 12);
//         closeMenu();
//       });
//     }

//     // Add Fire button
//     const addFireBtn = document.getElementById("addFireBtn");
//     if (addFireBtn) {
//       addFireBtn.addEventListener("click", function () {
//         const { longitude, latitude,  } = window.lastClickedPoint;
//         addFire(longitude, latitude, 12);
//         closeMenu();
//       });
//     }
//   });

  

  
