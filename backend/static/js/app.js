/**
 * Main Application Logic - HEIGHT ONLY STABLE VERSION WITH VALIDATION
 */

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const videoFeed = document.getElementById('videoFeed');
    const overlayCanvas = document.getElementById('overlayCanvas');
    const imagePreview = document.getElementById('imagePreview');
    const imageInput = document.getElementById('imageInput');
    const btnStartWebcam = document.getElementById('btnStartWebcam');
    const btnStopWebcam = document.getElementById('btnStopWebcam');
    const btnAnalyzePhoto = document.getElementById('btnAnalyzePhoto');
    const btnResetAnalysis = document.getElementById('btnResetAnalysis');
    const btnAddToCart = document.getElementById('btnAddToCart');
    
    // Validasi Elements
    const userHeightInput = document.getElementById('displayHeight');
    const heightError = document.getElementById('heightError');

    // State
    let isLiveMode = true;
    let mediaStream = null;
    let autoCaptureInterval = null;
    let overlayAnimationId = null;
    let isWebcamRunning = false;
    let selectedImageBase64 = null;
    let isAnalyzing = false;
    let consecutiveGoodFrames = 0;

    // --- Validation Logic ---
    function validateHeight() {
        const val = userHeightInput.value;
        if (!val || val <= 0) {
            heightError.style.display = 'block';
            userHeightInput.style.borderColor = 'var(--danger)';
            ui.showToast('Harap masukkan tinggi badan terlebih dahulu!', 'error');
            return false;
        }
        heightError.style.display = 'none';
        userHeightInput.style.borderColor = 'var(--primary)';
        return true;
    }

    function getCalibrationData() {
        const heightEl = document.getElementById('displayHeight');
        const val = heightEl ? parseFloat(heightEl.value) : 165;
        
        console.log("SENDING TO AI - Height:", val);
        
        return {
            calibration_type: 'height',
            user_height_cm: val,
            calibration_value_cm: val
        };  
    }

    // --- WebRTC Logic ---
    async function startWebcam() {
        // CEK VALIDASI SEBELUM MULAI
        if (!validateHeight()) return;

        btnStartWebcam.disabled = true;
        try {
            ui.showToast('Memulai kamera...');
            mediaStream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 640, height: 480, facingMode: "user" } 
            });
            
            videoFeed.srcObject = mediaStream;
            videoFeed.style.display = 'block';
            isWebcamRunning = true;
            btnStartWebcam.style.display = 'none';
            btnStopWebcam.style.display = 'flex';
            
            videoFeed.onloadedmetadata = () => {
                videoFeed.play();
                overlayCanvas.width = videoFeed.videoWidth;
                overlayCanvas.height = videoFeed.videoHeight;
                drawOverlay();
                consecutiveGoodFrames = 0;
                autoCaptureInterval = setInterval(performPrescan, 1000);
            };
        } catch (e) {
            ui.showToast('Gagal kamera: ' + e.message, 'error');
            btnStartWebcam.disabled = false;
        }
    }

    function stopWebcam() {
        if (autoCaptureInterval) clearInterval(autoCaptureInterval);
        if (overlayAnimationId) cancelAnimationFrame(overlayAnimationId);
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }
        isWebcamRunning = false;
        videoFeed.srcObject = null;
        videoFeed.style.display = 'none';
        btnStartWebcam.style.display = 'flex';
        btnStartWebcam.disabled = false;
        btnStopWebcam.style.display = 'none';
    }

    function drawOverlay() {
        if (!isWebcamRunning) return;
        const ctx = overlayCanvas.getContext('2d');
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        const w = overlayCanvas.width, h = overlayCanvas.height;
        const rw = w * 0.6, rh = h * 0.85;
        const rx = (w - rw) / 2, ry = (h - rh) / 2;
        
        ctx.strokeStyle = isAnalyzing ? '#10b981' : 'rgba(255, 255, 255, 0.7)';
        ctx.lineWidth = 4;
        ctx.setLineDash([15, 10]);
        ctx.strokeRect(rx, ry, rw, rh);
        
        ctx.fillStyle = 'white';
        ctx.font = 'bold 16px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText("Posisikan seluruh tubuh di dalam kotak", w/2, ry - 15);
        
        overlayAnimationId = requestAnimationFrame(drawOverlay);
    }

    async function performPrescan() {
        if (isAnalyzing || !isWebcamRunning) return;
        
        // Tetap validasi tinggi saat proses berjalan (jika user menghapus angka saat kamera nyala)
        if (!userHeightInput.value) {
            stopWebcam();
            validateHeight();
            return;
        }

        const canvas = document.createElement('canvas');
        canvas.width = videoFeed.videoWidth; canvas.height = videoFeed.videoHeight;
        canvas.getContext('2d').drawImage(videoFeed, 0, 0);
        const base64Image = canvas.toDataURL('image/jpeg', 0.8);

        const result = await api.prescan(base64Image, getCalibrationData());
        if (result && result.success && result.aligned) {
            consecutiveGoodFrames++;
            if (consecutiveGoodFrames >= 3) {
                ui.showToast('Pose sesuai! Menganalisis...', 'success');
                clearInterval(autoCaptureInterval);
                performFinalAnalysis(base64Image);
            } else {
                ui.showToast(`Tahan posisi... ${consecutiveGoodFrames}/3`, 'success');
            }
        } else {
            consecutiveGoodFrames = 0;
        }
    }

    async function performFinalAnalysis(base64Image) {
        isAnalyzing = true;
        ui.showToast('Menganalisis tubuh...');
        const data = await api.analyze(base64Image, getCalibrationData());
        if (data && data.success) {
            ui.showToast('Analisis Selesai', 'success');
            ui.updateMeasurements(data);
            btnAddToCart.style.display = 'block';
            videoFeed.pause();
        } else {
            ui.showToast(data.error || 'Analisis gagal', 'error');
            consecutiveGoodFrames = 0;
            autoCaptureInterval = setInterval(performPrescan, 1000);
        }
        isAnalyzing = false;
    }

    // --- Photo Upload ---
    imageInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            const reader = new FileReader();
            reader.onload = (event) => {
                selectedImageBase64 = event.target.result;
                imagePreview.src = selectedImageBase64;
                imagePreview.style.display = 'block';
                btnAnalyzePhoto.disabled = false;
                btnAddToCart.style.display = 'none';
                ui.updateMeasurements(null);
            };
            reader.readAsDataURL(e.target.files[0]);
        }
    });

    btnAnalyzePhoto.addEventListener('click', async () => {
        // CEK VALIDASI SEBELUM ANALISA FOTO
        if (!validateHeight()) return;

        btnAnalyzePhoto.disabled = true;
        ui.showToast('Menganalisis foto...');
        const data = await api.analyze(selectedImageBase64, getCalibrationData());
        if (data && data.success) {
            ui.updateMeasurements(data);
            btnAddToCart.style.display = 'block';
        } else {
            ui.showToast(data.error || 'Gagal', 'error');
        }
        btnAnalyzePhoto.disabled = false;
    });

    // --- Reset ---
    btnResetAnalysis.addEventListener('click', () => {
        ui.updateMeasurements(null);
        btnAddToCart.style.display = 'none';
        if (isLiveMode && isWebcamRunning) {
            videoFeed.play();
            isAnalyzing = false;
            consecutiveGoodFrames = 0;
            if (autoCaptureInterval) clearInterval(autoCaptureInterval);
            autoCaptureInterval = setInterval(performPrescan, 1000);
        } else {
            selectedImageBase64 = null;
            imagePreview.style.display = 'none';
            imageInput.value = '';
            btnAnalyzePhoto.disabled = true;
        }
    });

    // Tab Switching
    document.getElementById('tabLive').addEventListener('click', () => {
        isLiveMode = true;
        document.getElementById('contentLive').style.display = 'block';
        document.getElementById('contentUpload').style.display = 'none';
        if (isWebcamRunning) videoFeed.style.display = 'block';
        imagePreview.style.display = 'none';
    });

    document.getElementById('tabUpload').addEventListener('click', () => {
        isLiveMode = false;
        document.getElementById('contentLive').style.display = 'none';
        document.getElementById('contentUpload').style.display = 'block';
        stopWebcam();
        if (selectedImageBase64) imagePreview.style.display = 'block';
    });

    btnStartWebcam.addEventListener('click', startWebcam);
    btnStopWebcam.addEventListener('click', stopWebcam);
});