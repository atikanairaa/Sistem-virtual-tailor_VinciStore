class APIClient {
    constructor() {
        this.baseUrl = '/api/v1';
    }

    async checkHealth() {
        try {
            const res = await fetch(`${this.baseUrl}/health`);
            return res.ok;
        } catch {
            return false;
        }
    }

    async getProducts() {
        try {
            const res = await fetch(`${this.baseUrl}/products`);
            return await res.json();
        } catch (e) {
            console.error('Error fetching products:', e);
            return { success: false };
        }
    }

    async selectProduct(productId) {
        try {
            const res = await fetch(`${this.baseUrl}/session/product`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: productId })
            });
            return await res.json();
        } catch (e) {
            console.error('Error selecting product:', e);
            return { success: false, error: e.message };
        }
    }

    async getSelectedProduct() {
        try {
            const res = await fetch(`${this.baseUrl}/session/product`);
            return await res.json();
        } catch (e) {
            return { success: false };
        }
    }

    async prescan(base64Image, calibrationData) {
        try {
            const payload = {
                image: base64Image,
                ...calibrationData
            };
            const res = await fetch(`${this.baseUrl}/prescan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (e) {
            return { success: false, error: e.message };
        }
    }

    async analyze(base64Image, calibrationData) {
        try {
            const payload = {
                image: base64Image,
                ...calibrationData
            };
            const res = await fetch(`${this.baseUrl}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (e) {
            return { success: false, error: e.message };
        }
    }
}
const api = new APIClient();
