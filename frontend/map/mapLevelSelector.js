import { webscene } from "./mapSetup.js";

const buildingQuery = {
    "Building Wireframe": "BUILDINGID = 'Q'",
    "Interior Space": "BUILDING = 'Q'",
    "Walls": "BUILDINGKEY = 'Q'",
    "Doors": "BUILDINGKEY = 'Q'",
  };

export function showFloors(event) {
    // retrieve the query stored in the selected value
    const floorQuery = event.target.value;

    console.log(floorQuery);
  
    // update the definition expression of all layers except the wireframe layer
    webscene.layers.forEach((layer) => {
      if (layer.title !== "Building Wireframe") {
        layer.definitionExpression = buildingQuery[layer.title] + " AND " + floorQuery;
      }
    });

    // fetchAllWalls();
  
    // ===================TO TRIGGER WALL EXTRACTION==================
    // const wallsLayer = webscene.layers.find(l => l.title === "Walls");

    // const query = wallsLayer.createQuery();
    // query.returnGeometry = true;
    // query.outFields = ["*"];
    // // query.outSpatialReference = { wkid: 4326 }; // or the layer's SR
    // query.maxAllowableOffset = 0; // disable generalization
    // // query.geometryPrecision = 6; // increase decimal precision


    // // ✅ Filter only Building Q and Floor 1
    // query.where = "BUILDINGKEY = 'Q' AND FLOOR = 2 AND OBJECTID = 1";

    // wallsLayer.queryFeatures(query).then((result) => {
    //   let output = "";

    //   result.features.forEach((feature, index) => {
    //     const geom = feature.geometry;
    //     output += `\nFeature ${index + 1}:\n`;

    //     if (geom.rings) {
    //       geom.rings.forEach((ring, rIdx) => {
    //         output += `  Ring ${rIdx + 1}:\n`;
    //         ring.forEach((coord) => {
    //           const [x, y, z] = coord;
    //           output += `    ${x}, ${y}, ${z}\n`;
    //         });
    //       });
    //     } else if (geom.paths) {
    //       geom.paths.forEach((path, pIdx) => {
    //         output += `  Path ${pIdx + 1}:\n`;
    //         path.forEach((coord) => {
    //           const [x, y, z] = coord;
    //           output += `    ${x}, ${y}, ${z}\n`;
    //         });
    //       });
    //     }
    //   });

    //   // ✅ Trigger download of TXT file
    //   const blob = new Blob([output], { type: "text/plain" });
    //   const url = URL.createObjectURL(blob);
    //   const a = document.createElement("a");
    //   a.href = url;
    //   a.download = "walls_floor2.txt";
    //   a.click();
    //   URL.revokeObjectURL(url);
    // });


    
}


// const wallsLayer = webscene.layers.find(l => l.title === "Walls");

// async function fetchAllWalls() {
//   let allFeatures = [];
//   let lastOID = 0;
//   const batchSize = 2000; // matches service maxRecordCount
//   const wallsLayer = webscene.layers.find(l => l.title === "Walls");
//   while (true) {
//     const query = wallsLayer.createQuery();
//     query.returnGeometry = true;
//     query.outFields = ["*"];
//     query.maxAllowableOffset = 0;
//     query.where = `BUILDINGKEY = 'Q' AND FLOOR = 3 AND OBJECTID > ${lastOID}`;
//     query.orderByFields = ["OBJECTID ASC"];
//     query.num = batchSize;

//     const result = await wallsLayer.queryFeatures(query);

//     if (result.features.length === 0) break;
//     allFeatures = allFeatures.concat(result.features);

//     // advance OID window
//     lastOID = result.features[result.features.length - 1].attributes.OBJECTID;

//     console.log(`Fetched ${result.features.length} more features (total: ${allFeatures.length})`);

//     if (result.features.length < batchSize) {
//       // ✅ last batch, exit loop
//       break;
//     }
//   }

//   // return allFeatures;
//   let features = allFeatures;
//   console.log(`✅ Finished. Total features exported: ${features.length}`);

//   let output = "";

//   features.forEach((feature, index) => {
//     const geom = feature.geometry;
//     output += `\nFeature ${index + 1}:\n`;

//     if (!geom) {
//       output += "  ⚠️ No geometry found\n";
//       return;
//     }

//     if (geom.rings) {
//       geom.rings.forEach((ring, rIdx) => {
//         output += `  Ring ${rIdx + 1}:\n`;
//         ring.forEach((coord) => {
//           const [x, y, z] = coord;
//           output += `    ${x}, ${y}, ${z}\n`;
//         });
//       });
//     } else if (geom.paths) {
//       geom.paths.forEach((path, pIdx) => {
//         output += `  Path ${pIdx + 1}:\n`;
//         path.forEach((coord) => {
//           const [x, y, z] = coord;
//           output += `    ${x}, ${y}, ${z}\n`;
//         });
//       });
//     } else if (geom.type === "point") {
//       const { x, y, z } = geom;
//       output += `    ${x}, ${y}, ${z}\n`;
//     }
//   });

//   // ✅ Trigger download AFTER loop is fully done
//   const blob = new Blob([output], { type: "text/plain" });
//   const url = URL.createObjectURL(blob);
//   const a = document.createElement("a");
//   a.href = url;
//   a.download = "walls_floor3.txt";
//   document.body.appendChild(a); // ensure it’s in DOM
//   a.click();
//   document.body.removeChild(a);
//   URL.revokeObjectURL(url);
// }

// fetchAllWalls().then((features) => {
  
// });


document.getElementById('levelSelect').addEventListener('change', (event) => {
    showFloors(event);
});
  