import React, { useEffect, useState } from 'react';
import { fetchModelComparison } from '../services/api';

export default function ModelComparison() {
  const [models, setModels] = useState([]);
  const [bestModel, setBestModel] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    fetchModelComparison()
      .then((data) => {
        if (!active) {
          return;
        }
        setModels(data.results || []);
        setBestModel(data.best_model || '');
      })
      .catch((err) => {
        if (!active) {
          return;
        }
        setError(err.message);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="card border-0 shadow-sm">
      <div className="card-body p-4">
        <h5 className="card-title mb-1">Model Comparison</h5>
        <p className="text-muted small mb-4">
          Live model metrics loaded from the trained backend bundle and evaluation summary.
        </p>

        {bestModel && (
          <div className="alert alert-secondary py-2 small">
            Best deployed model: <strong>{bestModel}</strong>
          </div>
        )}

        {error && <div className="alert alert-danger py-2 small">{error}</div>}

        {models.map((model) => (
          <div key={model.name} className="mb-3">
            <div className="d-flex justify-content-between small mb-1">
              <span>{model.name}</span>
              <span className="fw-semibold">{model.r2_score.toFixed(2)}</span>
            </div>
            <div className="progress" style={{ height: 10 }}>
              <div className="progress-bar bg-dark" style={{ width: `${model.r2_score * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
