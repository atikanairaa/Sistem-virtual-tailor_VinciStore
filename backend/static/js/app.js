/**
 * Main Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const tabLive = document.getElementById('tabLive');
    const tabUpload = document.getElementById('tabUpload');
    const contentLive = document.getElementById('contentLive');
    const contentUpload = document.getElementById('contentUpload');
    
    const videoFeed = document.getElementById('videoFeed');
    const overlayCanvas = document.getElementById('overlayCanvas');
    const imagePreview = document.getElementById('imagePreview');
    const imageInput = document.getElementById('imageInput');
    const drawCanvas = document.getElementById('drawCanvas');
    
    const btnStartWebcam = document.getElementById('btnStartWebcam');
    const btnStopWebcam = document.getElementById('btnStopWebcam');
    const btnAnalyzePhoto = document.getElementById('btnAnalyzePhoto');
    const btnResetCalibration = document.getElementById('btnResetCalibration');
    const btnAddToCart = document.getElementById('btnAddToCart');
    
    const calibMethod = document.getElementById('calibMethod');
    const calibValue = document.getElementById('calibValue');
    const userHeight = document.getElementById('userHeight');
    const productCatalog = document.getElementById('productCatalog');
    
    // State
    let isLiveMode = true;
    let mediaStream = null;
    let autoCaptureInterval = null;
    let overlayAnimationId = null;
    let isWebcamRunning = false;
    let referencePixelLength = null;
    let selectedImageBase64 = null;
    let selectedProductId = null;
    let isAnalyzing = false;
    let consecutiveGoodFrames = 0;

    // --- Product Catalog ---
    async function loadProducts() {
        const data = await api.getProducts();
        if (data && data.success) {
            productCatalog.innerHTML = '';
            data.products.forEach(p => {
                const card = document.createElement('div');
                card.className = 'product-card';
                card.dataset.id = p.id;
                card.innerHTML = `
                    <img src="${p.image_url}" alt="${p.name}">
                    <h4>${p.name}</h4>
                    <p>Size: ${p.target_dress_size_cm}cm</p>
                `;
                card.addEventListener('click', () => selectProduct(p.id, card));
                productCatalog.appendChild(card);
            });
            
            // Check if there's a selected product in session
            const sessionData = await api.getSelectedProduct();
            if (sessionData && sessionData.product) {
                selectProduct(sessionData.product.id, document.querySelector(`.product-card[data-id="${sessionData.product.id}"]`));
            } else {
                if (window.location.pathname.includes('virtual-tailor')) {
                    ui.showToast('Silakan pilih produk terlebih dahulu', 'error');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1500);
                }
            }
        }
    }

    async function selectProduct(id, cardElement) {
        selectedProductId = id;
        document.querySelectorAll('.product-card').forEach(c => c.classList.remove('selected'));
        if (cardElement) cardElement.classList.add('selected');
        
        await api.selectProduct(id);
        ui.showToast('Produk dipilih', 'success');
        btnAddToCart.style.display = 'none'; // reset cart button
    }

    // Tabs
    tabLive.addEventListener('click', () => {
        isLiveMode = true;
        tabLive.classList.add('active');
        tabUpload.classList.remove('active');
        contentLive.classList.add('active');
        contentUpload.classList.remove('active');
        
        if (isWebcamRunning) videoFeed.style.display = 'block';
        imagePreview.style.display = 'none';
        ui.setDrawingEnabled(calibMethod.value === 'reference');
    });

    tabUpload.addEventListener('click', () => {
        isLiveMode = false;
        tabUpload.classList.add('active');
        tabLive.classList.remove('active');
        contentUpload.classList.add('active');
        contentLive.classList.remove('active');
        
        stopWebcam();
        
        videoFeed.style.display = 'none';
        if (selectedImageBase64) imagePreview.style.display = 'block';
        ui.setDrawingEnabled(calibMethod.value === 'reference');
    });

    calibMethod.addEventListener('change', () => {
        const calibLabel = document.getElementById('calibLabel');
        const userHeightInput = document.getElementById('userHeight');
        const heightGroup = userHeightInput ? userHeightInput.parentElement : null;
        
        if (calibMethod.value === 'reference') {
            if (calibLabel) calibLabel.innerText = 'Reference Width (cm)';
            if (heightGroup) heightGroup.style.display = 'block'; // ML models need height
            calibValue.value = '8.56'; // Default card size
            ui.setDrawingEnabled(true);
            ui.showToast('Please draw a line over the reference object (e.g. ID card) in the image');
        } else if (calibMethod.value === 'reference_auto') {
            if (calibLabel) calibLabel.innerText = 'Card Width (cm)';
            if (heightGroup) heightGroup.style.display = 'block'; // ML models need height
            calibValue.value = '8.56'; // Default card size
            ui.setDrawingEnabled(false);
            ui.showToast('Pegang objek referensi (mis. Kartu KTP/ATM) agar terlihat jelas di kamera');
        } else if (calibMethod.value === 'height') {
            if (calibLabel) calibLabel.innerText = 'Your Height (cm)';
            if (heightGroup) heightGroup.style.display = 'block';
            calibValue.value = userHeight.value || '170';
            ui.setDrawingEnabled(false);
        }
    });

    window.addEventListener('referenceDrawn', async (e) => {
        referencePixelLength = e.detail.pixelLength;
    });

    function getCalibrationData() {
        return {
            calibration_type: calibMethod.value,
            calibration_value_cm: parseFloat(calibValue.value) || 170,
            user_height_cm: parseFloat(userHeight.value) || 170,
            reference_pixel_length: referencePixelLength
        };
    }

    // --- WebRTC Logic ---
    async function startWebcam() {
        if (!selectedProductId) {
            ui.showToast('Silakan pilih produk terlebih dahulu!', 'error');
            return;
        }

        if (calibMethod.value === 'reference' && !referencePixelLength && !isLiveMode) {
            ui.showToast('Silakan gambar garis referensi terlebih dahulu.', 'error');
            return;
        }

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
            btnStopWebcam.disabled = false;
            
            videoFeed.onloadedmetadata = () => {
                videoFeed.play();
                overlayCanvas.width = videoFeed.videoWidth;
                overlayCanvas.height = videoFeed.videoHeight;
                drawOverlay();
                consecutiveGoodFrames = 0;
                autoCaptureInterval = setInterval(performPrescan, 1000); // Poll faster (1s) for the 3-frame countdown
            };
            
            ui.showToast('Kamera dimulai. Sesuaikan tubuh Anda dengan kotak panduan.', 'success');
        } catch (e) {
            ui.showToast('Akses kamera ditolak atau terjadi kesalahan: ' + e.message, 'error');
            btnStartWebcam.disabled = false;
        }
    }

    function stopWebcam() {
        btnStopWebcam.disabled = true;
        if (autoCaptureInterval) clearInterval(autoCaptureInterval);
        if (overlayAnimationId) cancelAnimationFrame(overlayAnimationId);
        
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }
        
        isWebcamRunning = false;
        videoFeed.srcObject = null;
        videoFeed.style.display = 'none';
        
        const ctx = overlayCanvas.getContext('2d');
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        
        btnStartWebcam.style.display = 'flex';
        btnStartWebcam.disabled = false;
        btnStopWebcam.style.display = 'none';
        
        ui.updateMeasurements(null); // Clear results
    }

    function drawOverlay() {
        if (!isWebcamRunning) return;
        const ctx = overlayCanvas.getContext('2d');
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        
        // Draw ROI Box
        const w = overlayCanvas.width;
        const h = overlayCanvas.height;
        let rw = w * 0.6;
        let rh = h * 0.8;
        
        let instructionText = "Mundur sedikit agar seluruh tubuh terlihat di dalam kotak";
        if (calibMethod.value === 'reference_auto' || calibMethod.value === 'reference') {
            rw = w * 0.7;
            rh = h * 0.6;
            instructionText = "Maju sedikit. Pegang kartu KTP/ATM di area dada atau perut";
        }
        
        const rx = (w - rw) / 2;
        const ry = (h - rh) / 2;
        
        ctx.strokeStyle = isAnalyzing ? '#4CAF50' : 'rgba(255, 255, 255, 0.7)';
        ctx.lineWidth = 4;
        ctx.setLineDash([15, 10]);
        ctx.strokeRect(rx, ry, rw, rh);
        
        // Instruction text
        ctx.fillStyle = 'white';
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(instructionText, w/2, ry - 15);
        
        // --- UI-Synchronized Card Box ---
        if (calibMethod.value === 'reference_auto') {
            const card_w = w * 0.3;
            const card_h = card_w / 1.586;
            const card_x = (w - card_w) / 2;
            const card_y = h * 0.44; // Sync with backend ROI

            ctx.strokeStyle = '#2196F3'; // Blue
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.strokeRect(card_x, card_y, card_w, card_h);
            
            ctx.fillStyle = '#2196F3';
            ctx.font = '14px Arial';
            ctx.fillText("Tempatkan KTP di sini", w/2, card_y - 10);
        }
        // --------------------------------
        
        overlayAnimationId = requestAnimationFrame(drawOverlay);
    }

    function captureBase64Frame() {
        if (!isWebcamRunning) return null;
        const canvas = document.createElement('canvas');
        canvas.width = videoFeed.videoWidth;
        canvas.height = videoFeed.videoHeight;
        canvas.getContext('2d').drawImage(videoFeed, 0, 0);
        return canvas.toDataURL('image/jpeg', 0.8);
    }

    async function performPrescan() {
        if (isAnalyzing || !isWebcamRunning) return;
        
        const base64Image = captureBase64Frame();
        if (!base64Image) return;

        const result = await api.prescan(base64Image, getCalibrationData());
        
        if (result && result.success && result.aligned) {
            consecutiveGoodFrames++;
            
            if (consecutiveGoodFrames >= 3) {
                ui.showToast('Pose sesuai! Mengambil gambar otomatis...', 'success');
                clearInterval(autoCaptureInterval); // stop scanning
                performFinalAnalysis(base64Image);
            } else {
                ui.showToast(`Tahan posisi... ${consecutiveGoodFrames}/3`, 'success');
            }
        } else {
            consecutiveGoodFrames = 0;
            if (result && result.message) {
                // Optional: update UI with message
            }
        }
    }

    async function performFinalAnalysis(base64Image) {
        isAnalyzing = true;
        ui.showToast('Menganalisis pose...');
        
        const data = await api.analyze(base64Image, getCalibrationData());
        
        if (data && data.success) {
            ui.showToast('Analisis selesai', 'success');
            ui.updateMeasurements(data);
            btnAddToCart.style.display = 'block';
            
            // Optionally pause video
            videoFeed.pause();
        } else {
            ui.showToast(data.error || 'Analisis gagal', 'error');
            // Resume prescan
            consecutiveGoodFrames = 0;
            autoCaptureInterval = setInterval(performPrescan, 1000);
        }
        isAnalyzing = false;
    }

    // --- Photo Upload Logic ---
    imageInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (event) => {
                selectedImageBase64 = event.target.result;
                imagePreview.src = selectedImageBase64;
                imagePreview.style.display = 'block';
                btnAnalyzePhoto.disabled = false;
                referencePixelLength = null;
                ui.clearCanvas();
                btnAddToCart.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }
    });

    async function analyzePhoto() {
        if (!selectedProductId) return ui.showToast('Silakan pilih produk terlebih dahulu!', 'error');
        if (!selectedImageBase64) return;
        if (calibMethod.value === 'reference' && !referencePixelLength) {
            return ui.showToast('Silakan gambar garis pada objek referensi terlebih dahulu.', 'error');
        }
        
        btnAnalyzePhoto.disabled = true;
        ui.showToast('Menganalisis foto...');
        
        const data = await api.analyze(selectedImageBase64, getCalibrationData());
        
        if (data && data.success) {
            ui.showToast('Analisis selesai', 'success');
            ui.updateMeasurements(data);
            btnAddToCart.style.display = 'block';
        } else {
            ui.showToast(data.error || 'Analisis gagal', 'error');
            ui.updateMeasurements(null);
        }
        btnAnalyzePhoto.disabled = false;
    }

    // Bindings
    btnStartWebcam.addEventListener('click', startWebcam);
    btnStopWebcam.addEventListener('click', stopWebcam);
    btnAnalyzePhoto.addEventListener('click', analyzePhoto);
    btnResetCalibration.addEventListener('click', () => {
        if (isLiveMode && isWebcamRunning) {
            ui.updateMeasurements(null);
            btnAddToCart.style.display = 'none';
            videoFeed.play();
            isAnalyzing = false;
            clearInterval(autoCaptureInterval);
            consecutiveGoodFrames = 0;
            autoCaptureInterval = setInterval(performPrescan, 1000);
            ui.showToast('Kalibrasi diulang. Silakan sesuaikan pose kembali.', 'success');
        } else {
            ui.updateMeasurements(null);
            btnAddToCart.style.display = 'none';
            referencePixelLength = null;
            ui.clearCanvas();
        }
    });

    btnAddToCart.addEventListener('click', async () => {
        const valFitStatus = document.getElementById('valFitStatus');
        const valBodyShape = document.getElementById('valBodyShape');
        const fitStatusText = valFitStatus ? valFitStatus.innerText : null;
        const bodyShapeText = valBodyShape ? valBodyShape.innerText : null;

        try {
            const response = await fetch('/api/v1/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fit_status_text: fitStatusText,
                    body_shape_text: bodyShapeText
                })
            });
            const data = await response.json();
            
            if (response.ok && data.success) {
                ui.showToast('Produk berhasil ditambahkan ke keranjang!', 'success');
                // Reset process
                btnAddToCart.style.display = 'none';
                if (isLiveMode && isWebcamRunning) {
                    stopWebcam();
                }
                setTimeout(() => {
                    window.location.href = '/keranjang';
                }, 500);
            } else {
                ui.showToast(data.error || 'Gagal menambahkan ke keranjang', 'error');
            }
        } catch (err) {
            console.error(err);
            ui.showToast('Terjadi kesalahan saat menambahkan ke keranjang', 'error');
        }
    });

    // Sync height
    userHeight.addEventListener('input', () => {
        if (calibMethod.value === 'height') calibValue.value = userHeight.value;
    });

    // Init
    api.checkHealth().then(ok => {
        if(ok) ui.showToast('Terhubung ke server backend', 'success');
        else ui.showToast('Tidak dapat terhubung ke server backend', 'error');
    });
    
    loadProducts();
    // Initialize UI state based on selected dropdown
    calibMethod.dispatchEvent(new Event('change'));
});
