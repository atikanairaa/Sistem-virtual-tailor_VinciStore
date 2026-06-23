/**
 * UI and Drawing Handlers
 */

class UIManager {
    constructor() {
        this.canvas = document.getElementById('drawCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.isDrawing = false;
        this.startPoint = null;
        this.endPoint = null;
        this.pixelLength = null;

        this.drawHint = document.getElementById('drawHint');
        this.mediaContainer = document.getElementById('mediaContainer');

        this.setupCanvas();
    }

    setupCanvas() {
        // Resize canvas to match its container exactly
        const resizeCanvas = () => {
            const rect = this.mediaContainer.getBoundingClientRect();
            this.canvas.width = rect.width;
            this.canvas.height = rect.height;
            if (this.startPoint && this.endPoint) {
                this.drawLine(); // redraw on resize (may skew, but better than nothing)
            }
        };

        window.addEventListener('resize', resizeCanvas);
        // Initial sizing delay to allow layout to settle
        setTimeout(resizeCanvas, 100);

        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('mouseleave', (e) => this.onMouseUp(e));

        // Touch support
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            this.onMouseDown(mouseEvent);
        });
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            this.onMouseMove(mouseEvent);
        });
        this.canvas.addEventListener('touchend', (e) => this.onMouseUp(e));
    }

    getPointerPos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    onMouseDown(e) {
        if (!this.canvasEnabled) return;
        this.isDrawing = true;
        this.startPoint = this.getPointerPos(e);
        this.endPoint = null;
        this.pixelLength = null;
        this.clearCanvas();
    }

    onMouseMove(e) {
        if (!this.isDrawing || !this.canvasEnabled) return;
        this.endPoint = this.getPointerPos(e);
        this.drawLine();
    }

    onMouseUp(e) {
        if (!this.isDrawing || !this.canvasEnabled) return;
        this.isDrawing = false;
        if (this.startPoint && this.endPoint) {
            this.calculateLength();
            // Trigger custom event so app knows length is ready
            window.dispatchEvent(new CustomEvent('referenceDrawn', {
                detail: { pixelLength: this.pixelLength }
            }));
            this.showToast(`Garis referensi tergambar: ${Math.round(this.pixelLength)}px`);
        }
    }

    drawLine() {
        this.clearCanvas();
        if (!this.startPoint || !this.endPoint) return;

        this.ctx.beginPath();
        this.ctx.moveTo(this.startPoint.x, this.startPoint.y);
        this.ctx.lineTo(this.endPoint.x, this.endPoint.y);
        this.ctx.strokeStyle = '#10b981'; // success color
        this.ctx.lineWidth = 3;
        this.ctx.lineCap = 'round';
        this.ctx.stroke();

        // Draw points
        this.ctx.beginPath();
        this.ctx.arc(this.startPoint.x, this.startPoint.y, 5, 0, Math.PI * 2);
        this.ctx.arc(this.endPoint.x, this.endPoint.y, 5, 0, Math.PI * 2);
        this.ctx.fillStyle = '#ef4444'; // danger color
        this.ctx.fill();
    }

    clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    calculateLength() {
        const dx = this.endPoint.x - this.startPoint.x;
        const dy = this.endPoint.y - this.startPoint.y;

        // We need to map canvas pixels to actual image/video pixels
        // Let's find the current visible media
        const activeMedia = document.getElementById('imagePreview').style.display !== 'none'
            ? document.getElementById('imagePreview')
            : document.getElementById('videoFeed');

        let scaleX = 1;
        let scaleY = 1;

        if (activeMedia.tagName === 'IMG' && activeMedia.naturalWidth) {
            // How much is the image scaled inside the canvas?
            // Object-fit: contain logic
            const imgAspect = activeMedia.naturalWidth / activeMedia.naturalHeight;
            const canvasAspect = this.canvas.width / this.canvas.height;

            let drawWidth, drawHeight;
            if (canvasAspect > imgAspect) {
                drawHeight = this.canvas.height;
                drawWidth = drawHeight * imgAspect;
            } else {
                drawWidth = this.canvas.width;
                drawHeight = drawWidth / imgAspect;
            }
            scaleX = activeMedia.naturalWidth / drawWidth;
            scaleY = activeMedia.naturalHeight / drawHeight;
        } else if (activeMedia.tagName === 'IMG' && activeMedia.videoWidth) {
            // For video, we don't have naturalWidth right away, but our backend sends fixed 640x480 images
            // so the IMG tag receives a 640x480 frame.
            const imgAspect = 640 / 480;
            const canvasAspect = this.canvas.width / this.canvas.height;
            let drawWidth, drawHeight;
            if (canvasAspect > imgAspect) {
                drawHeight = this.canvas.height;
                drawWidth = drawHeight * imgAspect;
            } else {
                drawWidth = this.canvas.width;
                drawHeight = drawWidth / imgAspect;
            }
            scaleX = 640 / drawWidth;
            scaleY = 480 / drawHeight;
        }

        // Apply scale (using an average scale for diagonal lines)
        const avgScale = (scaleX + scaleY) / 2;
        this.pixelLength = Math.sqrt(dx * dx + dy * dy) * avgScale;
    }

    setDrawingEnabled(enabled) {
        this.canvasEnabled = enabled;
        if (enabled) {
            this.canvas.style.pointerEvents = 'auto';
            this.drawHint.classList.add('visible');
        } else {
            this.canvas.style.pointerEvents = 'none';
            this.drawHint.classList.remove('visible');
            this.clearCanvas();
            this.pixelLength = null;
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('statusToast');
        toast.textContent = message;

        if (type === 'error') toast.style.borderColor = 'var(--danger)';
        else if (type === 'success') toast.style.borderColor = 'var(--success)';
        else toast.style.borderColor = 'var(--primary)';

        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    updateMeasurements(data) {
        const resultsDiv = document.getElementById('measurementsResults');

        if (!data || !data.measurements) {
            resultsDiv.innerHTML = '<div class="measurement-item"><span class="measurement-label">Status</span><span class="measurement-value" style="color:var(--danger)">Tidak ada data pengukuran.</span></div>';
            return;
        }

        const m = data.measurements;
        let html = '';

        if (m.shoulder_width_cm)
            html += `<div class="measurement-item"><span class="measurement-label">Lebar Bahu</span><span class="measurement-value">${m.shoulder_width_cm.toFixed(1)} cm</span></div>`;

        if (m.hip_width_cm)
            html += `<div class="measurement-item"><span class="measurement-label">Lebar Pinggul</span><span class="measurement-value">${m.hip_width_cm.toFixed(1)} cm</span></div>`;

        if (m.chest_width_cm)
            html += `<div class="measurement-item"><span class="measurement-label">Lebar Dada</span><span class="measurement-value">${m.chest_width_cm.toFixed(1)} cm</span></div>`;

        if (m.chest_circumference_cm)
            html += `<div class="measurement-item"><span class="measurement-label">Lingkar Dada</span><span class="measurement-value" style="font-size:1.3rem; color: var(--primary);">${m.chest_circumference_cm.toFixed(1)} cm</span></div>`;

        if (m.body_shape)
            html += `<div class="measurement-item"><span class="measurement-label">Bentuk Tubuh</span><span class="measurement-value" id="valBodyShape">${m.body_shape}</span></div>`;

        if (m.fit_recommendation) {
            // Color coding based on actual KNN model labels
            const fitColors = {
                'Regular Fit': { color: 'var(--success)', emoji: '✅' },
                'Oversize Fit': { color: '#d97706', emoji: '📦' }, // Darker orange/gold for better visibility
                'Tight Fit': { color: 'var(--danger)', emoji: '⚠️' },
                'Not Recommended': { color: '#f97316', emoji: '🚫' },
                'Unknown': { color: 'var(--text-muted)', emoji: '❓' },
            };
            const fitInfo = fitColors[m.fit_recommendation] || { color: 'var(--primary)', emoji: '👕' };
            html += `<div class="measurement-item">
                <span class="measurement-label">Rekomendasi Kesesuaian</span>
                <span class="measurement-value" id="valFitStatus" style="color: ${fitInfo.color}; font-size: 1.2rem; font-weight: 700;">
                    ${fitInfo.emoji} ${m.fit_recommendation}
                </span>
            </div>`;
        }

        if (!html) {
            html = '<div class="measurement-item"><span class="measurement-label">Status</span><span class="measurement-value" style="color:var(--text-muted)">Tidak ada pengukuran tersedia.</span></div>';
        }

        resultsDiv.innerHTML = html;

        const calStatus = document.getElementById('calibrationStatusBadge');
        calStatus.className = 'status-badge status-calibrated';
        calStatus.textContent = 'Selesai';
    }
}

window.ui = new UIManager();
