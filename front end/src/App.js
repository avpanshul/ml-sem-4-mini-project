import React, { useState } from 'react';
import PredictForm from './components/PredictForm';
import ResultCard from './components/ResultCard';
import ModelComparison from './components/ModelComparison';
import AQIGauge from './components/AQIGauge';

export default function App() {
  const [result, setResult] = useState(null);

  const handleResult = (data) => {
    setResult(data);
  };

  return (
    <div className="min-vh-100 bg-light">
      <div className="container py-5">
        <div className="row justify-content-center mb-4">
          <div className="col-lg-10 text-center">
            <span className="badge text-bg-dark mb-3">Random Forest AQI Predictor</span>
            <h1 className="display-5 fw-bold">Air Quality Prediction with Random Forest</h1>
            <p className="text-muted mb-0">
              Use the final deployed Random Forest regressor and compare it against the
              rest of the trained PM2.5 models.
            </p>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-5">
            <PredictForm onResult={handleResult} />
            {result && <ResultCard result={result} />}
          </div>

          <div className="col-lg-7">
            {result && result.type === 'regression' && (
              <div className="mb-4">
                <AQIGauge value={result.aqi} category={result.category} />
              </div>
            )}
            <div className="mb-4">
              <ModelComparison />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
