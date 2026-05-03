import React from 'react';

const bands = [
  { label: 'Good', color: '#22c55e', min: 0, max: 30 },
  { label: 'Satisfactory', color: '#84cc16', min: 30, max: 60 },
  { label: 'Moderate', color: '#f59e0b', min: 60, max: 90 },
  { label: 'Poor', color: '#f97316', min: 90, max: 120 },
  { label: 'Very Poor', color: '#ef4444', min: 120, max: 250 },
  { label: 'Severe', color: '#7f1d1d', min: 250, max: 500 }
];

export default function AQIGauge({ value, category }) {
  const clamped = Math.max(0, Math.min(500, Number(value || 0)));
  const progress = (clamped / 500) * 100;

  return (
    <div className="card border-0 shadow-sm">
      <div className="card-body p-4">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="card-title mb-0">AQI Gauge</h5>
          <span className="badge text-bg-dark">{category}</span>
        </div>

        <div className="progress" style={{ height: 18 }}>
          {bands.map((band) => (
            <div
              key={band.label}
              className="progress-bar"
              title={`${band.label}: ${band.min}-${band.max}`}
              style={{ width: `${((band.max - band.min) / 500) * 100}%`, backgroundColor: band.color }}
            />
          ))}
        </div>

        <div className="position-relative mt-2" style={{ height: 20 }}>
          <div
            className="position-absolute top-0 translate-middle-x"
            style={{ left: `${progress}%` }}
          >
            <div className="fw-bold">{clamped.toFixed(2)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
