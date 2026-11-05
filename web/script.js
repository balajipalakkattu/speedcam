const video = document.getElementById("video");
const speedDiv = document.getElementById("speed");

let ws = null;
let isConnected = false;
let frameInFlight = false;

function log(msg) {
    const logDiv = document.getElementById("log");
    logDiv.appendChild(document.createTextNode(msg));
    logDiv.appendChild(document.createElement("br"));
    logDiv.scrollTop = logDiv.scrollHeight;
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

function connectWebSocket() {
    const wsUrl = "wss://speedcam.onrender.com/speed/ws/estimate";

    log(`Connecting to WebSocket: ${wsUrl}`);

    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
        log("WebSocket connected");
        isConnected = true;
        frameInFlight = false;
    };

    ws.onmessage = (event) => {
        frameInFlight = false;
        try {
            const data = JSON.parse(event.data);

            if (data.error) {
                log("Server error: " + data.error);
                return;
            }

            if (data.speed_mph !== undefined) {
                speedDiv.innerText = `Speed: ${data.speed_mph} mph`;
            }
        } catch (err) {
            log("Error parsing WebSocket message: " + err);
        }
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        log("WebSocket network error; check the browser console and server logs");
        isConnected = false;
    };

    ws.onclose = (event) => {
        const reason = event.reason ? `, reason: ${event.reason}` : "";
        log(`WebSocket closed (code ${event.code}${reason})`);
        isConnected = false;
        frameInFlight = false;
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
}

async function sendFrame() {
    if (!isConnected || !ws || ws.readyState !== WebSocket.OPEN || frameInFlight) {
        return;
    }

    if (video.videoWidth === 0 || video.videoHeight === 0) {
        return;
    }

    try {
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0);

        // Wait for the server response before sending another frame.
        frameInFlight = true;
        canvas.toBlob((blob) => {
            if (!blob || !isConnected || !ws || ws.readyState !== WebSocket.OPEN) {
                frameInFlight = false;
                return;
            }

            try {
                ws.send(blob);
            } catch (err) {
                frameInFlight = false;
                log("Frame send error: " + err);
            }
        }, "image/jpeg", 0.9);
    } catch (err) {
        log("Frame capture error: " + err);
    }
}

// Send frames continuously while connected
async function processFrames() {
    sendFrame();
    // Send frame every 100ms (adjust based on your needs)
    setTimeout(processFrames, 100);
}

(async () => {
    try {
        await startCamera();
        connectWebSocket();
        processFrames();
    } catch (err) {
        log("Camera error: " + err);
    }
})();
