import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api'
});

const getMessage = (error, fallback) =>
  (error.response && error.response.data && error.response.data.error) || fallback;

export async function predictAQI(payload) {
  try {
    const { data } = await api.post('/predict', payload);
    return data;
  } catch (error) {
    throw new Error(getMessage(error, 'Prediction failed'));
  }
}

export async function fetchModelComparison() {
  try {
    const { data } = await api.get('/model-comparison');
    return data;
  } catch (error) {
    throw new Error(getMessage(error, 'Unable to load model comparison'));
  }
}
