
let rightClickStart = null;
    
function waitForMapView(callback) {
    if (window.mapView) {
      callback(window.mapView);
    } else {
      setTimeout(() => waitForMapView(callback), 50);
    }
  }
  
  waitForMapView((view) => {
    view.when(() => {
        console.log("mapView loaded");
        console.log("mapView loaded");
        window.mapView.container.addEventListener("mousedown", (event) => {
            console.log("mousedown");
            
            if (event.button === 2) { // Right button
                // prevent default behavior
                event.preventDefault();
            
                // Capture the screen position when mouse is pressed
                rightClickStart = { x: event.clientX, y: event.clientY };  
            }
            else if (event.button === 0) { // Left button
                // if clicked on the menu
                if (event.target.closest("#addMenuu")) {
                    return;
                }
                // if clicked on the map
                else {
                    // set the lastClickedPoint as null
                    closeMenu();
                    window.lastClickedPoint = null;
                }
            }
        });
        
        window.mapView.container.addEventListener("mouseup", async (event) => {
            if (event.button === 2) { // Right button
            // get the final point where user release the mouse
            const finalScreenPoint = { x: event.clientX, y: event.clientY };
            
            // check if the mouse is clicked and released in the same place
            if (rightClickStart && finalScreenPoint.x === rightClickStart.x && finalScreenPoint.y === rightClickStart.y) {
                // record the hit point where user clicked
                const hit = await window.mapView.hitTest(rightClickStart);
        
                // get the first hit point
                if (hit.results.length > 0) {
                    // Get the first hit point — usually the closest 3D object surface
                    const hitPoint = hit.results[0].mapPoint;

                    console.log(hitPoint);
                
                    // Store this precise 3D point
                    window.lastClickedPoint = hitPoint;
                
                    
                    } else {
                    // No building or object hit, fallback to ground point
                    const mapPoint = window.mapView.toMap({ x: event.clientX, y: event.clientY });
                    if (mapPoint) {
                        window.lastClickedPoint = mapPoint;
                    }
                }
        
                // call the function to position the menu nicely
                showMenu(addMenuu, event.clientX, event.clientY);
                }
                else{
                    // set the lastClickedPoint as null
                    window.lastClickedPoint = null;
                }
            }

        });
    });
  });




// show the menu
export function showMenu(menuElement, clickX, clickY) {
    const menuHeight = menuElement.offsetHeight;
    const menuWidth = menuElement.offsetWidth;
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;
  
    // Calculate vertical position
    let topPosition = clickY;
    const spaceBelow = viewportHeight - clickY;
    if (spaceBelow < menuHeight) {
      topPosition = clickY - menuHeight;
      if (topPosition < 0) topPosition = 0;
    }
  
    // Calculate horizontal position to prevent overflow
    let leftPosition = clickX;
    const spaceRight = viewportWidth - clickX;
    if (spaceRight < menuWidth) {
      leftPosition = clickX - menuWidth;
      if (leftPosition < 0) leftPosition = 0;
    }
  
    menuElement.style.top = `${topPosition}px`;
    menuElement.style.left = `${leftPosition}px`;
    menuElement.style.display = "block";

    const evacueeCountInput = document.getElementById("evacueeCountInput");
    // set the default as 1
    evacueeCountInput.value = 1;
  }
  
// close the menu
export function closeMenu() {
    const addMenu = document.getElementById("addMenuu");
    addMenu.style.display = "none";
}