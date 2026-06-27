/**
 * API Client - Height-Only Version
 */
class APIClient {
    constructor() {
        this.baseUrl = '/api/v1';
    }

    async checkHealth() {
        try {
            const res = await fetch(`${this.baseUrl}/health`);
            return res.ok;
        } catch { return false; }
    }

    async getProducts() {
        try {
            const res = await fetch(`${this.baseUrl}/products`);
            return await res.json();
        } catch (e) { return { success: false }; }
    }

    async selectProduct(productId) {
        try {
            const res = await fetch(`${this.baseUrl}/session/product`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: productId })
            });
            return await res.json();
        } catch (e) { return { success: false, error: e.message }; }
    }

    async getSelectedProduct() {
        try {
            const res = await fetch(`${this.baseUrl}/session/product`);
            return await res.json();
        } catch { return { success: false }; }
    }

    async prescan(base64Image, calibrationData) {
        try {
            const payload = {
                image: base64Image,
                calibration_type: 'height',
                user_height_cm: calibrationData.user_height_cm,
                calibration_value_cm: calibrationData.user_height_cm
            };
            const res = await fetch(`${this.baseUrl}/prescan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (e) { return { success: false, error: e.message }; }
    }

    async analyze(base64Image, calibrationData) {
        try {
            const payload = {
                image: base64Image,
                calibration_type: 'height',
                user_height_cm: calibrationData.user_height_cm,
                calibration_value_cm: calibrationData.user_height_cm
            };
            const res = await fetch(`${this.baseUrl}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin', // Menjaga session login tetap aktif
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (e) { return { success: false, error: e.message }; }
    }
}
const api = new APIClient();