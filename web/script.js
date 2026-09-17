const video = document.getElementById("video");
const rawImg = document.getElementById("raw");
const processedImg = document.getElementById("processed");
const speedDiv = document.getElementById("speed");

function log(msg) {
    const logDiv = document.getElementById("log");
    logDiv.innerHTML += msg + "<br>";
}
log("script.js loaded");

log("startCamera() called");

async function startCamera() {
	document.body.addEventListener("click", () => {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            log("Camera started after user gesture");
        })
        .catch(err => log("Camera error: " + err));
});
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
	 log("sendFrame() called");

    if (video.videoWidth === 0 || video.videoHeight === 0) {
        log("Video not ready yet...");
        return;
    }
	log("Capturing frame...");

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    // Show raw frame
    rawImg.src = canvas.toDataURL("image/jpeg");

    // Convert to blob
    const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));
    const formData = new FormData();
    formData.append("frame", blob, "frame.jpg");

    log("Sending frame to backend...");

	let res;
	try {
		res = await fetch("https://speedcam.onrender.com:15000/speed/estimate", {
			method: "POST",
			body: formData
		});
		log("Response received");
	} catch (err) {
		log("Fetch error: " + err);
		return;
	}

    const data = await res.json();

    // Show processed frame
    processedImg.src = "data:image/jpeg;base64," + data.frame;

    // Show speed
    speedDiv.innerText = `Speed: ${data.speed_mph} mph`;
}

(async () => {
    await startCamera();
    setInterval(sendFrame, 200);
})();
