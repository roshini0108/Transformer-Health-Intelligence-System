import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
    timeout: 10000,
    headers: {
        Accept: 'application/json',
    },
});

const pathId = (id) => encodeURIComponent(String(id).trim());

// Transformers
export const getTransformers = () => api.get('/transformers/');
export const getTransformer = (transformer_id) =>
    api.get(`/transformers/${pathId(transformer_id)}`);

// Predictions
export const getPredictions = () => api.get('/predictions/');
export const getPredictionsSummary = () => api.get('/predictions/summary');
export const getTransformerPredictions = (transformer_id, days = 30) =>
    api.get(`/predictions/${pathId(transformer_id)}`, { params: { days } });
export const runPrediction = (transformer_id) =>
    api.post(`/predictions/run/${pathId(transformer_id)}`);

// Readings
export const getReadings = (transformer_id, days = 30) =>
    api.get(`/readings/${pathId(transformer_id)}`, { params: { days } });

// Alerts
export const getAlerts = (unackOnly = false) =>
    api.get('/alerts/', { params: { unacknowledged_only: unackOnly } });
export const acknowledgeAlert = (id) =>
    api.post(`/alerts/${pathId(id)}/acknowledge`);

export default api;
