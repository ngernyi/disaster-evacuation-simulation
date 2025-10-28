// import arcgis modules
require([
  "esri/WebScene",
  "esri/views/SceneView",
  "esri/Graphic",
  "esri/symbols/PointSymbol3D",
  "esri/symbols/ObjectSymbol3DLayer",
  "esri/geometry/Point"
], function (WebScene, SceneView, Graphic, PointSymbol3D, ObjectSymbol3DLayer, Point) {

  // get the 3d scene
  const webscene = new WebScene({
    portalItem: {
      id: "7685f7ba6b47426ea20d6f640cf98596"
    }
  });

  // render the 3d scene in map
  const view = new SceneView({
    container: "map",
    map: webscene
  });

  // view.when(() => {
  //   const path = [
  //     [-117.19564524436946, 34.05609840400424, 11],
  //     [-117.19536524436946, 34.05609840400424, 11],
  //     [-117.19535524436946, 34.05619840400424, 11],
  //     [-117.19546524436946, 34.05619840400424, 11]
  //   ];

  //   // ✅ Create a 3D sphere as a placeholder for a human
  //   const humanSymbol = new PointSymbol3D({
  //     symbolLayers: [
  //       new ObjectSymbol3DLayer({
  //         resource: { primitive: "sphere" },
  //         material: { color: "blue" },
  //         height: 2,
  //         width: 2,
  //         depth: 2
  //       })
  //     ]
  //   });

  //   const humanGraphic = new Graphic({
  //     geometry: new Point({
  //       longitude: path[0][0],
  //       latitude: path[0][1],
  //       z: path[0][2],
  //       spatialReference: { wkid: 4326 }
  //     }),
  //     symbol: humanSymbol
  //   });

  //   view.graphics.add(humanGraphic);

  //   // Move the object along the path
  //   let index = 0;
  //   const speed = 1000;

  //   const moveHuman = () => {
  //     index = (index + 1) % path.length;
  //     const [lon, lat, z] = path[index];
  //     humanGraphic.geometry = new Point({
  //       longitude: lon,
  //       latitude: lat,
  //       z: z,
  //       spatialReference: { wkid: 4326 }
  //     });
  //   };

  //   setInterval(moveHuman, speed);

  //   view.goTo({
  //     target: new Point({
  //       longitude: path[0][0],
  //       latitude: path[0][1],
  //       z: path[0][2],
  //       spatialReference: { wkid: 4326 }
  //     }).extent.expand(2),
  //     tilt: 60
  //   });
  // });
});


document.getElementById("googleSignInButton").addEventListener("click", function() {
  // Redirect to Flask backend Google login route
  window.location.href = "http://localhost:5000/login";
});

document.getElementById("microsoftSignInButton").addEventListener("click", function() {
  // Redirect to Flask backend Google login route
  window.location.href = "http://localhost:5000/login/microsoft";
});

// fetch('http://127.0.0.1:5000/login/callback', { credentials: 'include' })
//   .then(res => res.json())
//   .then(data => {
//     if (data.success) {
//       window.location.href = 'http://127.0.0.1:5501/Code/frontend/map/landingPage.html';
//     }
//   });

