// mapGraphics.js
import Graphic from "https://js.arcgis.com/4.32/@arcgis/core/Graphic.js";
// function to add fire symbool to the map
export function addFire(lon, lat, z) {
    console.log("from graphic file",lon, lat);
    const fireGraphic = new Graphic({
        geometry: { type: "point", longitude: lon, latitude: lat, z, spatialReference: { wkid: 4326 } },
        symbol: {
        type: "point-3d",
        symbolLayers: [{ type: "object", resource: { primitive: "sphere" }, material: { color: "red" }, height: 3, width: 3, depth: 3, anchor: "center" }]
        }
    });
    window.mapView.graphics.add(fireGraphic);

    return fireGraphic;
}

// function to add evacuee symbol to the map
export function addEvacuee(lon, lat, z) {
  const evacueeGraphic = new Graphic({
    geometry: { type: "point", longitude: lon, latitude: lat, z:z, spatialReference: { wkid: 4326 } },
    symbol: {
      type: "point-3d",
      symbolLayers: [{ type: "object", resource: { primitive: "sphere" }, material: { color: "blue" }, height: 3, width: 1, depth: 1, anchor: "center" }]
    }
  });
  window.mapView.graphics.add(evacueeGraphic);

  return evacueeGraphic;
}

// function to set the Evacuees position
export function setEvacueePosition(evacueeGraphic, lon, lat, z) {
  if (!evacueeGraphic) {
    evacueeGraphic.geometry.longitude = lon;
    evacueeGraphic.geometry.latitude = lat;
    evacueeGraphic.geometry.z = z;
  }
}

// /* function to move the evacuees
// * params : 
// * 1) an array storing the evacuees position
// * 2) movement frequency
// * 3) evacuees graphic
// */
// export function moveEvacuee(evacueePosition, frequency, evacueeGraphic) {
//   for (let i = 0; i < evacueePosition.length; i++) {
//       let currentPosition = evacueePosition[i];

//       // call the set evacuees position function
//       setEvacueePosition(evacueeGraphic, currentPosition[0], currentPosition[1], currentPosition[2]);

//       // delay for frequency
//       setTimeout(() => {
          
//       }, frequency);
//   }
// }