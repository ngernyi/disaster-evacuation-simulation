// mapGraphics.js
import Graphic from "https://js.arcgis.com/4.32/@arcgis/core/Graphic.js";

let dimensionGraphics = [];
let assemblyGraphics = [];
let staircaseGraphics = [];

export function showDimension() {
    if (!window.mapView) return;
  
    const dimensionLine_width = new Graphic({
      geometry: {
        type: "polyline",
        paths: [[
          [-117.19610446487934, 34.05637790271325, 2],
          [-117.19610696946594, 34.055836382811506, 2]
        ]],
        spatialReference: { wkid: 4326 }
      },
      symbol: {
        type: "line-3d",
        symbolLayers: [{
          type: "path",
          profile: "circle", // Makes it a tube
          width: 0.5,          // Width in meters
          material: { color: [255, 140, 0, 0.4] } // Semi-transparent Orange
        }]
      }
    });
  
    // Add a Label at the top of the line
    const label_width = new Graphic({
      geometry: {
        type: "point",
        x: -117.19610571717264, y: 34.056107142762378, z: 5, // Slightly above the line
        spatialReference: { wkid: 4326 }
      },
      symbol: {
        type: "text",
        color: "white",
        haloColor: "black",
        haloSize: "2px",
        text: "Building Width: 50m",
        font: { size: 12, weight: "bold" }
      }
    });

    const dimensionLine_length = new Graphic({
        geometry: {
          type: "polyline",
          paths: [[
            [-117.19607498771788, 34.055820665612465, 2],
            [-117.19529974049262, 34.05582082463027, 2]
          ]],
          spatialReference: { wkid: 4326 }
        },
        symbol: {
          type: "line-3d",
          symbolLayers: [{
            type: "path",
            profile: "circle", // Makes it a tube
            width: 0.5,          // Width in meters
            material: { color: [255, 0, 255, 0.4] } // Semi-transparent Orange
          }]
        }
      });
    
      // Add a Label at the top of the line
      const label_length = new Graphic({
        geometry: {
          type: "point",
          x: -117.19568736410525, y: 34.0558207451213675, z: 5, // Slightly above the line
          spatialReference: { wkid: 4326 }
        },
        symbol: {
          type: "text",
          color: "white",
          haloColor: "black",
          haloSize: "2px",
          text: "Building length: 70m",
          font: { size: 12, weight: "bold" }
        }
      });

      const dimensionLine_height = new Graphic({
        geometry: {
          type: "polyline",
          paths: [[
            [-117.19610634989095, 34.055827108055055, 0],
            [-117.19610634989095, 34.055827108055055, 15]
          ]],
          spatialReference: { wkid: 4326 }
        },
        symbol: {
          type: "line-3d",
          symbolLayers: [{
            type: "path",
            profile: "circle", // Makes it a tube
            width: 0.5,          // Width in meters
            material: { color: [0, 255, 255, 0.4] } // Semi-transparent Orange
          }]
        }
      });
    
      // Add a Label at the top of the line
      const label_height = new Graphic({
        geometry: {
          type: "point",
          x: -117.19610634989095, y: 34.055827108055055, z: 16, // Slightly above the line
          spatialReference: { wkid: 4326 }
        },
        symbol: {
          type: "text",
          color: "white",
          haloColor: "black",
          haloSize: "2px",
          text: "Building height: 15m",
          font: { size: 12, weight: "bold" }
        }
      });

      dimensionGraphics = [dimensionLine_width, label_width, dimensionLine_length, label_length,dimensionLine_height , label_height];
      
  
    window.mapView.graphics.addMany([dimensionLine_width, label_width, dimensionLine_length, label_length,dimensionLine_height , label_height]);
  }

export function showAssemblyPoint(){
    if (!window.mapView) return;

    const assemblyGraphic1 = new Graphic({
        geometry: {
          type: "point",
          longitude: -117.1956520625412,
          latitude: 34.05639161712975,
          z: 0,
          spatialReference: { wkid: 4326 }
        },
        symbol: {
            type: "point-3d",
            symbolLayers: [{
              type: "icon",
              resource: { 
                // This pulls a specific "pin" shape from the Esri library
                primitive: "circle" 
              },
              size: 30,
              material: { color: [0, 200, 0] }, // Safety Green
              outline: { color: "white", size: 2 }
            }],
            // Use vertical offset so the "drop" floats above the ground/evacuees
            verticalOffset: {
              screenLength: 30,
              maxWorldLength: 200,
              minWorldLength: 10
            },
            callout: {
              type: "line",
              size: 2,
              color: "white"
            }
          }
        });

      // Add a Label at the top of the line
      const label_assembly_point_1 = new Graphic({
        geometry: {
          type: "point",
          x: -117.1956520625412, y: 34.05639161712975, z: 2, // Slightly above the line
          spatialReference: { wkid: 4326 }
        },
        symbol: {
          type: "text",
          color: "white",
          haloColor: "black",
          haloSize: "2px",
          text: "Assembly Point 1 (Tennis Court)",
          font: { size: 15, weight: "bold" }
        }
      });

      const assemblyGraphic2 = new Graphic({
        geometry: {
          type: "point",
          longitude: -117.19512781129663,
          latitude: 34.056053736202315,
          z: 0,
          spatialReference: { wkid: 4326 }
        },
        symbol: {
            type: "point-3d",
            symbolLayers: [{
              type: "icon",
              resource: { 
                // This pulls a specific "pin" shape from the Esri library
                primitive: "circle" 
              },
              size: 30,
              material: { color: [0, 200, 0] }, // Safety Green
              outline: { color: "white", size: 2 }
            }],
            // Use vertical offset so the "drop" floats above the ground/evacuees
            verticalOffset: {
              screenLength: 30,
              maxWorldLength: 200,
              minWorldLength: 10
            },
            callout: {
              type: "line",
              size: 2,
              color: "white"
            }
          }
        });

      // Add a Label at the top of the line
      const label_assembly_point_2 = new Graphic({
        geometry: {
          type: "point",
          x: -117.19512781129663, y: 34.056053736202315, z: 2, // Slightly above the line
          spatialReference: { wkid: 4326 }
        },
        symbol: {
          type: "text",
          color: "white",
          haloColor: "black",
          haloSize: "2px",
          text: "Assembly Point 2 (Car Park)",
          font: { size: 15, weight: "bold" }
        }
      });

      const assemblyGraphic3 = new Graphic({
        geometry: {
          type: "point",
          longitude: -117.19623505024354,
          latitude: 34.05621487659595,
          z: 0,
          spatialReference: { wkid: 4326 }
        },
        symbol: {
            type: "point-3d",
            symbolLayers: [{
              type: "icon",
              resource: { 
                // This pulls a specific "pin" shape from the Esri library
                primitive: "circle" 
              },
              size: 30,
              material: { color: [0, 200, 0] }, // Safety Green
              outline: { color: "white", size: 2 }
            }],
            // Use vertical offset so the "drop" floats above the ground/evacuees
            verticalOffset: {
              screenLength: 30,
              maxWorldLength: 200,
              minWorldLength: 10
            },
            callout: {
              type: "line",
              size: 2,
              color: "white"
            }
          }
        });

      // Add a Label at the top of the line
      const label_assembly_point_3 = new Graphic({
        geometry: {
          type: "point",
          x: -117.19623505024354, y: 34.05621487659595, z: 2, // Slightly above the line
          spatialReference: { wkid: 4326 }
        },
        symbol: {
          type: "text",
          color: "white",
          haloColor: "black",
          haloSize: "2px",
          text: "Assembly Point 3 (Car Park)",
          font: { size: 15, weight: "bold" }
        }
      });

      assemblyGraphics = [assemblyGraphic1, label_assembly_point_1, assemblyGraphic2, label_assembly_point_2, assemblyGraphic3, label_assembly_point_3];
    
      window.mapView.graphics.addMany([assemblyGraphic1, label_assembly_point_1, assemblyGraphic2, label_assembly_point_2, assemblyGraphic3, label_assembly_point_3]);
}

export function showStairCase(){
  if (!window.mapView) return;
  const stairPoint1 = new Graphic({
    geometry: {
      type: "point",
      x: -117.19557424707945,
      y: 34.056118766847334,
      z: 0, // This is where the bottom of the callout starts
      spatialReference: { wkid: 4326 }
    },
    // ADD THIS SECTION:
    elevationInfo: {
      mode: "relative-to-ground" 
      
    },
    symbol: {
      type: "point-3d",
      symbolLayers: [{
        type: "icon",
        resource: { href: "../assets/images/construction.png" },
        size: 30,
        outline: { color: "white", size: 2 }
      }],
      // The callout connects the geometry Z (10) to the verticalOffset
      verticalOffset: { 
        screenLength: 200, // Increase this to make the line longer
        maxWorldLength: 15, 
        minWorldLength: 5 
      },
      callout: { 
        type: "line", 
        size: 2, 
        color: "cyan" 
      }
    }
  });

  const stairPoint2 = new Graphic({
    geometry: {
      type: "point",
      x: -117.19578962444298,
      y: 34.0560899781941,
      z: 0, // This is where the bottom of the callout starts
      spatialReference: { wkid: 4326 }
    },
    // ADD THIS SECTION:
    elevationInfo: {
      mode: "relative-to-ground" 
      
    },
    symbol: {
      type: "point-3d",
      symbolLayers: [{
        type: "icon",
        resource: { href: "../assets/images/construction.png" },
        size: 30,
        outline: { color: "white", size: 2 }
      }],
      // The callout connects the geometry Z (10) to the verticalOffset
      verticalOffset: { 
        screenLength: 200, // Increase this to make the line longer
        maxWorldLength: 15, 
        minWorldLength: 5 
      },
      callout: { 
        type: "line", 
        size: 2, 
        color: "cyan" 
      }
    }
  });

  const stairPoint3 = new Graphic({
    geometry: {
      type: "point",
      x: -117.19603379555,
      y: 34.05624942388,
      z: 0, // This is where the bottom of the callout starts
      spatialReference: { wkid: 4326 }
    },
    // ADD THIS SECTION:
    elevationInfo: {
      mode: "relative-to-ground" 
      
    },
    symbol: {
      type: "point-3d",
      symbolLayers: [{
        type: "icon",
        resource: { href: "../assets/images/construction.png" },
        size: 30,
        outline: { color: "white", size: 2 }
      }],
      // The callout connects the geometry Z (10) to the verticalOffset
      verticalOffset: { 
        screenLength: 200, // Increase this to make the line longer
        maxWorldLength: 15, 
        minWorldLength: 5 
      },
      callout: { 
        type: "line", 
        size: 2, 
        color: "cyan" 
      }
    }
  });

  const stairPoint4 = new Graphic({
    geometry: {
      type: "point",
      x: -117.195333804329,
      y: 34.055954726546,
      z: 0, // This is where the bottom of the callout starts
      spatialReference: { wkid: 4326 }
    },
    // ADD THIS SECTION:
    elevationInfo: {
      mode: "relative-to-ground" 
      
    },
    symbol: {
      type: "point-3d",
      symbolLayers: [{
        type: "icon",
        resource: { href: "../assets/images/construction.png" },
        size: 30,
        outline: { color: "white", size: 2 }
      }],
      // The callout connects the geometry Z (10) to the verticalOffset
      verticalOffset: { 
        screenLength: 200, // Increase this to make the line longer
        maxWorldLength: 15, 
        minWorldLength: 5 
      },
      callout: { 
        type: "line", 
        size: 2, 
        color: "cyan" 
      }
    }
  });
  
  staircaseGraphics = [stairPoint1, stairPoint2, stairPoint3, stairPoint4];


  window.mapView.graphics.addMany([stairPoint1, stairPoint2, stairPoint3, stairPoint4]);

}

// The Toggle Function
export function toggleLayer(layerType, isVisible) {
  let targetArray;

  // Use a switch or if/else to determine which group to toggle
  if (layerType === 'dimension') {
      targetArray = dimensionGraphics;
  } else if (layerType === 'assembly') {
      targetArray = assemblyGraphics;
  } else if (layerType === 'staircase') {
      targetArray = staircaseGraphics;
  }

  // Safety check: only loop if the array exists and has graphics
  if (targetArray && targetArray.length > 0) {
      console.log(`Toggling ${layerType} to ${isVisible}`);
      targetArray.forEach(graphic => {
          graphic.visible = isVisible;
      });
  } else {
      console.warn(`No graphics found for layer type: ${layerType}`);
  }
}