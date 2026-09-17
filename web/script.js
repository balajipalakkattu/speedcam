const video = document.getElementById("video");
const rawImg = document.getElementById("raw");
const processedImg = document.getElementById("processed");
const speedDiv = document.getElementById("speed");

// Wait this long between backend requests. This prevents Render from being
// overwhelmed while still processing the latest available camera frame.
const FRAME_INTERVAL_MS = 1000;
let requestInFlight = false;

function log(msg) {
    const logDiv = document.getElementById("log");
    logDiv.innerHTML += msg + "<br>";
}
log("script.js loaded");

async function startCamera() {
    log("Requesting camera...");
    const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }
    });
    log("Camera stream acquired");

    video.srcObject = stream;

    return new Promise(resolve => {
        video.onloadedmetadata = () => {
            log("Video metadata loaded");
            video.play();
            log("Video playing");
            resolve();
        };
    });
}

async function sendFrame() {
    if (requestInFlight) {
        log("Previous request still in progress; skipping frame");
        return;
    }

    if (video.videoWidth === 0 || video.videoHeight === 0) {
        log("Video not ready yet...");
        return;
    }

    requestInFlight = true;

    try {
        log("Capturing frame...");

        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0);

        // Show raw frame
        rawImg.src = canvas.toDataURL("image/jpeg");

        const blob = await new Promise(resolve =>
            canvas.toBlob(resolve, "image/jpeg")
        );
        if (!blob) {
            log("Could not create image blob");
            return;
        }

        const formData = new FormData();
        formData.append("frame", blob, "frame.jpg");

        log("Sending frame to backend...");
        const res = await fetch("https://speedcam.onrender.com/speed/estimate", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            throw new Error(`Backend returned ${res.status}`);
        }

        const data = await res.json();
        log("Response received");

        // Show processed frame
        processedImg.src = "data:image/jpeg;base64," + data.frame;

        // Show speed
        speedDiv.innerText = `Speed: ${data.speed_mph} mph`;
    } catch (err) {
        log("Request error: " + err);
    } finally {
        requestInFlight = false;
    }
}

// Use a timeout scheduled after each request instead of setInterval. This
// guarantees that requests cannot overlap when the backend is slow.
async function processFrames() {
    await sendFrame();
    setTimeout(processFrames, FRAME_INTERVAL_MS);
}

(async () => {
    try {
        await startCamera();
        processFrames();
    } catch (err) {
        log("Camera error: " + err);
    }
})();
