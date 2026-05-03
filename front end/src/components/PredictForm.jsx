import React, { useState } from 'react';
import { predictAQI } from '../services/api';

const CITIES = {
  Mumbai: { temperature: 30, temp_max: 34, temp_min: 26, humidity: 78, rainfall: 0.5, visibility: 4, wind_speed: 15, wind_max: 25 },
  Delhi: { temperature: 25, temp_max: 32, temp_min: 18, humidity: 55, rainfall: 0, visibility: 3, wind_speed: 10, wind_max: 20 },
  Bangalore: { temperature: 22, temp_max: 28, temp_min: 17, humidity: 65, rainfall: 0.2, visibility: 8, wind_speed: 12, wind_max: 18 },
  Chennai: { temperature: 32, temp_max: 38, temp_min: 27, humidity: 80, rainfall: 1.1, visibility: 6, wind_speed: 18, wind_max: 30 }
};

const initialForm = {
  temperature: '',
  temp_max: '',
  temp_min: '',
  humidity: '',
  rainfall: '',
  visibility: '',
  wind_speed: '',
  wind_max: '',
  city: 'Custom',
  model: 'gradient_boosting'
};

function validate(form) {
  const errors = {};
  const fields = ['temperature', 'temp_max', 'temp_min', 'humidity', 'rainfall', 'visibility', 'wind_speed', 'wind_max'];
  fields.forEach((field) => {
    if (form[field] === '' || form[field] === undefined) {
      errors[field] = 'Required';
    }
  });

  if (form.humidity !== '' && (Number(form.humidity) < 0 || Number(form.humidity) > 100)) {
    errors.humidity = 'Must be 0-100';
  }

  if (form.temperature !== '' && (Number(form.temperature) < -60 || Number(form.temperature) > 60)) {
    errors.temperature = 'Must be between -60 and 60';
  }

  return errors;
}

export default function PredictForm({ onResult }) {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: '' }));
  };

  const handleCitySelect = (event) => {
    const city = event.target.value;
    if (CITIES[city]) {
      setForm((current) => ({ ...current, ...CITIES[city], city }));
      setErrors({});
      return;
    }
    setForm((current) => ({ ...current, city: 'Custom' }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const validationErrors = validate(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    setApiError('');
    try {
      const result = await predictAQI({ ...form, model: 'gradient_boosting' });
      onResult(result);
    } catch (error) {
      setApiError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const field = (name, label, placeholder = '') => (
    <div className="col-sm-6">
      <label className="form-label small fw-semibold">{label}</label>
      <input
        type="number"
        name={name}
        value={form[name]}
        onChange={handleChange}
        placeholder={placeholder}
        className={`form-control form-control-sm ${errors[name] ? 'is-invalid' : ''}`}
      />
      {errors[name] && <div className="invalid-feedback">{errors[name]}</div>}
    </div>
  );

  return (
    <div className="card border-0 shadow-sm">
      <div className="card-body p-4">
        <h5 className="card-title mb-4">Enter Climate Conditions</h5>

        <div className="mb-3">
          <label className="form-label small fw-semibold">Quick Fill City Preset</label>
          <select className="form-select form-select-sm" onChange={handleCitySelect} defaultValue="">
            <option value="">Select a city</option>
            {Object.keys(CITIES).map((city) => (
              <option key={city} value={city}>{city}</option>
            ))}
          </select>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="row g-3">
            {field('temperature', 'Avg Temp (C)', '25')}
            {field('temp_max', 'Max Temp (C)', '32')}
            {field('temp_min', 'Min Temp (C)', '18')}
            {field('humidity', 'Humidity (%)', '65')}
            {field('rainfall', 'Rainfall / Snowmelt (mm)', '0')}
            {field('visibility', 'Visibility (km)', '6')}
            {field('wind_speed', 'Wind Speed (km/h)', '12')}
            {field('wind_max', 'Max Wind (km/h)', '20')}
          </div>

          <div className="mt-3">
            <label className="form-label small fw-semibold">ML Model</label>
            <div className="form-control form-control-sm bg-light">Gradient Boosting Regressor</div>
          </div>

          {apiError && <div className="alert alert-danger py-2 small mt-3 mb-0">{apiError}</div>}

          <button className="btn btn-dark w-100 mt-4" type="submit" disabled={loading}>
            {loading ? 'Predicting...' : 'Predict AQI'}
          </button>
        </form>
      </div>
    </div>
  );
}
