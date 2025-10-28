import Graphic from "https://js.arcgis.com/4.32/@arcgis/core/Graphic.js";
import { setPauseButton, setReplayButton, setResumeButton, updateEscapedNumber, updateProgress, updateTimeProgress } from "../ui/simulationPlaying.js";


let isPaused = true;
let isEnded = false;
let currentStep = 0;
// function to play the simulation
/*  params:
    - currentStep : current step of the simulation
    - evacueesGraphic : all evacuees graphic
    - evacueesMovement : all evacuees movement
    - interval : interval between each step
*/
export function playSimulation(evacueeGraphic, evacueeMovement, interval) {

    const flatevacueeMovement = evacueeMovement;
    // console.log("graphic length",evacueeGraphic.length);
    // console.log("flat",flatevacueeMovement);

    let maxLength = flatevacueeMovement.reduce((max, movement) => Math.max(max, movement.length), 0);
    // if currentStep is greater than the number of steps, stop the simulation
    if (currentStep > maxLength) {
        console.log("stopSimulation");
        setReplayButton();
        isPaused = true;
        isEnded = true;
        return;
    }

    updateEvacueesAtStep(currentStep, evacueeGraphic, evacueeMovement);

    // call the function again after the interval
    setTimeout(() => {
        if (!isPaused) {
            currentStep++;
            playSimulation(evacueeGraphic, evacueeMovement, interval);
            // updateProgress(step / evacueeMovement.reduce((max, m) => Math.max(max, m.length), 0) * 100);
            // updateEscapedNumber(currentEscapedNumber);
            // updateTimeProgress(step);
        }
        else{
            console.log("Simulation paused");
        }
    }, interval);

    

    // console.log("runSimulation ",currentStep);
}

function updateEvacueesAtStep(step, evacueeGraphic, evacueeMovement) {
    let currentEscapedNumber = 0;

    for (let i = 0; i < evacueeGraphic.length; i++) {
        const evacuee = evacueeGraphic[i];
        const movement = evacueeMovement[i];
        let nextPosition = movement[step];

        if (!nextPosition) {
            nextPosition = movement[movement.length - 1];
            currentEscapedNumber++;
        }

        evacuee.geometry = {
            type: "point",
            longitude: nextPosition.Longitude,
            latitude: nextPosition.Latitude,
            z: nextPosition.Z,
            spatialReference: { wkid: 4326 }
        };
    }

    updateProgress(step / evacueeMovement.reduce((max, m) => Math.max(max, m.length), 0) * 100);
    updateEscapedNumber(currentEscapedNumber);
    updateTimeProgress(step);
}



export function pauseSimulation() {
    isPaused = true;
    setResumeButton();
}

export function resumeSimulation(evacueeGraphic, evacueeMovement, interval) {
    isPaused = false;
    setPauseButton();

    // restart the loop
    playSimulation(evacueeGraphic, evacueeMovement, interval);
}

export function startSimulation(evacueeGraphic ,evacueeMovement){
    console.log("startSimulation clicked");
    console.log(evacueeGraphic.length);
    // check if everything is rendered
    // if (window.mapView) {
    //     // for (let i = 0; i < evacueeGraphic.length; i++) {
    //     //     playSimulation(evacueeGraphic[i], evacueeMovement[i], 1000);
    //     // }
    //     playSimulation(evacueeGraphic, evacueeMovement, 100);

    //     isPaused = false;
    //     setPauseButton();
    // }
}

export function handleControlButton(evacueeGraphic, evacueeMovement, interval){
    if (isPaused) {
        if (isEnded) {
            currentStep = 0;
            isEnded = false;
        }
        resumeSimulation(evacueeGraphic, evacueeMovement, interval);
    }
    else {
        pauseSimulation();
    }
}

export function setCurrentStep(percentage, totalSteps, evacueeGraphic, evacueeMovement){

    // set the current step to the percentage
    currentStep = Math.round((percentage / 100) * totalSteps);
    
    // adjust the evacuees to the current frame
    updateEvacueesAtStep(currentStep, evacueeGraphic, evacueeMovement);
    if(currentStep != totalSteps){
        isEnded = false;
    }

    // update the control button state
    if (isPaused) {
        setResumeButton();
    }
    else {
        setPauseButton();
    }
}