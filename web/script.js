const video = document.getElementById("video");
const speedDiv = document.getElementById("speed");
const toggleFramesButton = document.getElementById("toggleFrames");

let ws = null;
let isConnected = false;
let frameInFlight = false;
let sendingPaused = false;
let framesSent = 0;
let responsesReceived = 0;
let frameSentAt = null;
let reconnectAttempt = 0;

function log(msg) {
    const logDiv = document.getElementById("log");
    logDiv.appendChild(document.createTextNode(msg));
    logDiv.appendChild(document.createElement("br"));
    logDiv.scrollTop = logDiv.scrollHeight;
}
log("script.js loaded");

toggleFramesButton.addEventListener("click", () => {
    sendingPaused = !sendingPaused;
    toggleFramesButton.textContent = sendingPaused ? "Play" : "Pause";
    toggleFramesButton.setAttribute("aria-pressed", String(sendingPaused));
    log(sendingPaused ? "Frame sending paused" : "Frame sending resumed");
});

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
    if (ws && (ws.readyState === WebSocket.CONNECTING ||
        ws.readyState === WebSocket.OPEN)) {
        return;
    }

    const wsUrl = "wss://speedcam.onrender.com/speed/ws/estimate";

    log(`Connecting to WebSocket: ${wsUrl}`);

    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";
    let receivedResponse = false;

    ws.onopen = () => {
        log("WebSocket connected");
        isConnected = true;
        frameInFlight = false;
        frameSentAt = null;
    };

    ws.onmessage = (event) => {
        receivedResponse = true;
        reconnectAttempt = 0;
        const responseTime = frameSentAt === null ? null : Date.now() - frameSentAt;
        frameInFlight = false;
        frameSentAt = null;
        try {
            const data = JSON.parse(event.data);

            if (data.error) {
                log("Server error: " + data.error);
                return;
            }

            if (data.speed_mph !== undefined) {
                responsesReceived += 1;
                speedDiv.innerText = `Speed: ${data.speed_mph} mph`;
                if (responsesReceived === 1 || responsesReceived % 10 === 0) {
                    const detection = data.detected === undefined
                        ? "detection status unavailable"
                        : data.detected ? "vehicle detected" : "no vehicle detected";
                    log(
                        `API response ${responsesReceived}: ${data.speed_mph} mph, ` +
                        `${detection}, ${responseTime} ms`
                    );
                }
            } else {
                log("API response received without speed_mph");
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
        if (!receivedResponse) {
            log(
                "No API response on this connection. Browser WebSocket APIs hide " +
                "handshake HTTP status; check Render/proxy logs for 429."
            );
        }
        isConnected = false;
        frameInFlight = false;
        const delaySeconds = Math.min(3 * (2 ** Math.min(reconnectAttempt, 5)), 60);
        reconnectAttempt += 1;
        log(`Retrying WebSocket in ${delaySeconds} seconds`);
        setTimeout(connectWebSocket, delaySeconds * 1000);
    };
}

async function sendFrame() {
    if (sendingPaused || !isConnected || !ws ||
        ws.readyState !== WebSocket.OPEN || frameInFlight) {
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
            if (sendingPaused || !blob || !isConnected || !ws ||
                ws.readyState !== WebSocket.OPEN) {
                frameInFlight = false;
                return;
            }

            try {
                ws.send(blob);
                framesSent += 1;
                frameSentAt = Date.now();
                if (framesSent === 1 || framesSent % 10 === 0) {
                    log(
                        `Sent frame ${framesSent}: ${canvas.width}x${canvas.height}, ` +
                        `${Math.round(blob.size / 1024)} KB`
                    );
                }
                setTimeout(() => {
                    if (frameInFlight && frameSentAt !== null &&
                        Date.now() - frameSentAt >= 10000) {
                        log("No API response for 10 seconds; frame is still pending");
                    }
                }, 10000);
            } catch (err) {
                frameInFlight = false;
                frameSentAt = null;
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
