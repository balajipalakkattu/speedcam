const video = document.getElementById("video");
const rawImg = document.getElementById("raw");
const processedImg = document.getElementById("processed");
const speedDiv = document.getElementById("speed");

let ws = null;
let isConnected = false;

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

function connectWebSocket() {
    // Determine WebSocket URL based on current location
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//speedcam.onrender.com/speed/ws/estimate`;

    log(`Connecting to WebSocket: ${wsUrl}`);

    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
        log("WebSocket connected");
        isConnected = true;
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.error) {
                log("Server error: " + data.error);
                return;
            }

            // Show processed frame
            if (data.frame) {
                processedImg.src = "data:image/jpeg;base64," + data.frame;
            }

            // Show speed
            if (data.speed_mph !== undefined) {
                speedDiv.innerText = `Speed: ${data.speed_mph} mph`;
            }

            // Show detection info if available
            if (data.detection) {
                log(`Detection: [${data.detection.join(", ")}]`);
            }
        } catch (err) {
            log("Error parsing WebSocket message: " + err);
        }
    };

    ws.onerror = (error) => {
        log("WebSocket error: " + error);
        isConnected = false;
    };

    ws.onclose = () => {
        log("WebSocket closed");
        isConnected = false;
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
}

async function sendFrame() {
    if (!isConnected) {
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

        // Show raw frame
        rawImg.src = canvas.toDataURL("image/jpeg");

        // Convert canvas to blob and send as binary
        canvas.toBlob((blob) => {
            if (blob && isConnected) {
                ws.send(blob);
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
