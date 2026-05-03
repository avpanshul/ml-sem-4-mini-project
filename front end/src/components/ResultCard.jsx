import React from 'react';

const CATEGORY_STYLES = {
  Good: { bg: '#f0fdf4', border: '#22c55e', text: '#15803d' },
  Satisfactory: { bg: '#f7fee7', border: '#84cc16', text: '#3f6212' },
  Moderate: { bg: '#fffbeb', border: '#f59e0b', text: '#92400e' },
  Poor: { bg: '#fff7ed', border: '#f97316', text: '#9a3412' },
  'Very Poor': { bg: '#fef2f2', border: '#ef4444', text: '#991b1b' },
  Severe: { bg: '#7f1d1d', border: '#7f1d1d', text: '#ffffff' }
};

const MODEL_LABELS = {
  xgboost: 'XGBoost Regressor',
  gradient_boosting: 'Gradient Boosting Regressor',
  random_forest: 'Random Forest Regressor',
  extra_trees: 'Extra Trees Regressor',
  adaboost: 'AdaBoost Regressor',
  knn: 'KNN Regressor',
  svr: 'SVR Regressor'
};

export default function ResultCard({ result }) {
  const style = CATEGORY_STYLES[result.category] || { bg: '#f9f9f9', border: '#999999', text: '#333333' };
  const modelLabel = MODEL_LABELS[result.model_used] || (result.model_used && result.model_used.replace(/_/g, ' '));

  return (
    <div className="card mt-4 border-2" style={{ background: style.bg, borderColor: style.border }}>
      <div className="card-body p-4 text-center">
        <p className="small text-muted mb-1">Predicted by {modelLabel}</p>

        {result.type === 'regression' ? (
          <>
            <div style={{ fontSize: 56, fontWeight: 700, color: style.text, lineHeight: 1 }}>
              {result.aqi}
            </div>
            <div className="small text-muted mb-2">Estimated PM2.5 / AQI-like score</div>
          </>
        ) : (
          <div style={{ fontSize: 20, fontWeight: 600, color: style.text }}>
            Classification result
          </div>
        )}

        <span className="badge px-3 py-2 fs-6" style={{ background: style.border, color: '#ffffff' }}>
          {result.category}
        </span>

        {result.probabilities && (
          <div className="mt-3 text-start">
            {Object.entries(result.probabilities).map(([category, percent]) => (
              <div key={category} className="mb-2">
                <div className="d-flex justify-content-between small">
                  <span>{category}</span>
                  <span>{percent}%</span>
                </div>
                <div className="progress" style={{ height: 6 }}>
                  <div
                    className="progress-bar"
                    style={{
                      width: `${percent}%`,
                      background: CATEGORY_STYLES[category] ? CATEGORY_STYLES[category].border : '#888888'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        <p className="small text-muted mt-3 mb-0">
          {result.timestamp ? new Date(result.timestamp).toLocaleString() : ''}
        </p>
      </div>
    </div>
  );
}
