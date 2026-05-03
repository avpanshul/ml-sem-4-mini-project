from __future__ import annotations

from datetime import datetime
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd
from flask_cors import CORS
from flask import Flask, jsonify, request, send_from_directory
from sklearn.exceptions import InconsistentVersionWarning


ROOT = Path(__file__).resolve().parent
FRONTEND_BUILD_DIR = ROOT / "front end" / "build"
BUNDLE_PATH = ROOT / "deployment_assets" / "best_pm25_model_bundle.joblib"
MODEL_RESULTS_PATH = ROOT / "artifacts" / "pm25_model_evaluation_results.csv"
BASE_DATA_PATH = ROOT / "artifacts" / "pm25_base_model_data.csv"

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

app = Flask(__name__, static_folder=str(FRONTEND_BUILD_DIR), static_url_path="/")
CORS(app, resources={r"/api/*": {"origins": "*"}})


def month_to_season(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Summer"
    if month in (6, 7, 8, 9):
        return "Monsoon"
    return "Post-Monsoon"


def categorize_pm25(value: float) -> str:
    if value <= 30:
        return "Good"
    if value <= 60:
        return "Satisfactory"
    if value <= 90:
        return "Moderate"
    if value <= 120:
        return "Poor"
    if value <= 250:
        return "Very Poor"
    return "Severe"


def clean_float(payload: dict, field_name: str) -> float:
    value = payload.get(field_name)
    if value is None or value == "":
        raise ValueError(f"Missing required field: {field_name}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {field_name}") from exc


def load_base_data() -> pd.DataFrame:
    base_df = pd.read_csv(BASE_DATA_PATH)
    base_df["Date"] = pd.to_datetime(base_df["Date"])
    return base_df.sort_values("Date").reset_index(drop=True)


def load_history_by_city() -> dict[str, list[float]]:
    histories: dict[str, list[float]] = {}

    for city, city_df in base_df.groupby("City"):
        histories[str(city)] = city_df["Daily_PM25"].tail(30).tolist()

    histories["__default__"] = base_df["Daily_PM25"].tail(30).tolist()
    return histories


def load_model_results() -> list[dict]:
    results_df = pd.read_csv(MODEL_RESULTS_PATH).sort_values("r2_score", ascending=False)
    rows = []
    for row in results_df.to_dict(orient="records"):
        rows.append(
            {
                "name": row["model"],
                "r2_score": round(float(row["r2_score"]), 4),
                "mae": round(float(row["mae"]), 4),
                "rmse": round(float(row["rmse"]), 4),
            }
        )
    return rows


bundle = joblib.load(BUNDLE_PATH)
base_df = load_base_data()
history_by_city = load_history_by_city()
model_results = load_model_results()
training_reference_year = int(base_df["Year"].max())
city_pm25_mean = {
    str(city): float(city_df["Daily_PM25"].mean())
    for city, city_df in base_df.groupby("City")
}
default_pm25_mean = float(base_df["Daily_PM25"].mean())
weather_reference = {
    "Avg_Temperature": float(base_df["Avg_Temperature"].mean()),
    "Max_Temperature": float(base_df["Max_Temperature"].mean()),
    "Min_Temperature": float(base_df["Min_Temperature"].mean()),
    "Humidity": float(base_df["Humidity"].mean()),
    "Rainfall_Snowmelt": float(base_df["Rainfall_Snowmelt"].fillna(0).mean()),
    "Visibility": float(base_df["Visibility"].mean()),
    "Wind_Speed": float(base_df["Wind_Speed"].mean()),
    "Max_Sustained_Wind_Speed": float(
        base_df["Max_Sustained_Wind_Speed"].fillna(base_df["Max_Sustained_Wind_Speed"].median()).mean()
    ),
}
weather_scale = {
    "Avg_Temperature": max(float(base_df["Avg_Temperature"].std()), 1.0),
    "Max_Temperature": max(float(base_df["Max_Temperature"].std()), 1.0),
    "Min_Temperature": max(float(base_df["Min_Temperature"].std()), 1.0),
    "Humidity": max(float(base_df["Humidity"].std()), 1.0),
    "Rainfall_Snowmelt": max(float(base_df["Rainfall_Snowmelt"].fillna(0).std()), 1.0),
    "Visibility": max(float(base_df["Visibility"].std()), 1.0),
    "Wind_Speed": max(float(base_df["Wind_Speed"].std()), 1.0),
    "Max_Sustained_Wind_Speed": max(
        float(base_df["Max_Sustained_Wind_Speed"].fillna(base_df["Max_Sustained_Wind_Speed"].median()).std()),
        1.0,
    ),
}


def weather_pm25_proxy(inputs: dict[str, float], city: str) -> float:
    city_mean = city_pm25_mean.get(city, default_pm25_mean)

    visibility_effect = ((weather_reference["Visibility"] - inputs["Visibility"]) / weather_scale["Visibility"]) * 35
    humidity_effect = ((inputs["Humidity"] - weather_reference["Humidity"]) / weather_scale["Humidity"]) * 18
    temperature_effect = ((inputs["Avg_Temperature"] - weather_reference["Avg_Temperature"]) / weather_scale["Avg_Temperature"]) * 10
    temp_max_effect = ((inputs["Max_Temperature"] - weather_reference["Max_Temperature"]) / weather_scale["Max_Temperature"]) * 8
    wind_effect = ((weather_reference["Wind_Speed"] - inputs["Wind_Speed"]) / weather_scale["Wind_Speed"]) * 16
    wind_max_effect = (
        (weather_reference["Max_Sustained_Wind_Speed"] - inputs["Max_Sustained_Wind_Speed"])
        / weather_scale["Max_Sustained_Wind_Speed"]
    ) * 12
    rainfall_effect = (
        (weather_reference["Rainfall_Snowmelt"] - inputs["Rainfall_Snowmelt"])
        / weather_scale["Rainfall_Snowmelt"]
    ) * 20

    proxy = (
        city_mean
        + visibility_effect
        + humidity_effect
        + temperature_effect
        + temp_max_effect
        + wind_effect
        + wind_max_effect
        + rainfall_effect
    )

    return float(np.clip(proxy, 10, 450))


def adaptive_history(city: str, proxy: float) -> np.ndarray:
    base_history = np.array(history_by_city.get(city, history_by_city["__default__"]), dtype=float)
    base_mean = float(base_history.mean())
    centered = base_history - base_mean
    proxy_shift = proxy - base_mean
    trend = np.linspace(-proxy_shift * 0.15, proxy_shift * 0.15, len(base_history))
    adapted = proxy + (centered * 0.35) + trend
    return np.clip(adapted, 5, 500)


def visibility_adjustment(visibility: float) -> float:
    # Enforce a monotonic inverse relationship:
    # higher visibility should always push AQI downward.
    delta = visibility - weather_reference["Visibility"]
    return -12.0 * delta


def rainfall_adjustment(rainfall: float) -> float:
    # Higher rainfall / snowmelt should generally help clear particulates.
    if rainfall <= 0:
        return 0.0
    capped_rainfall = min(rainfall, 50.0)
    return -3.5 * np.sqrt(capped_rainfall)


def build_feature_row(payload: dict) -> pd.DataFrame:
    now = datetime.now()
    city = str(payload.get("city") or "Bangalore").strip() or "Bangalore"
    inputs = {
        "Avg_Temperature": clean_float(payload, "temperature"),
        "Max_Temperature": clean_float(payload, "temp_max"),
        "Min_Temperature": clean_float(payload, "temp_min"),
        "Humidity": clean_float(payload, "humidity"),
        "Rainfall_Snowmelt": clean_float(payload, "rainfall"),
        "Visibility": clean_float(payload, "visibility"),
        "Wind_Speed": clean_float(payload, "wind_speed"),
        "Max_Sustained_Wind_Speed": clean_float(payload, "wind_max"),
    }
    history = adaptive_history(city, weather_pm25_proxy(inputs, city))

    if len(history) < 30:
        raise ValueError("Insufficient historical PM2.5 data to build lag features")

    history_series = pd.Series(history, dtype=float)
    month = now.month
    row = {
        **inputs,
        "City": city,
        "Month": month,
        "Year": training_reference_year,
        "Day": now.day,
        "DayOfWeek": now.weekday(),
        "IsWeekend": 1 if now.weekday() >= 5 else 0,
        "Season": month_to_season(month),
    }

    for lag in (1, 2, 3, 5, 7, 10, 14, 21, 30):
        row[f"PM25_lag_{lag}"] = float(history_series.iloc[-lag])

    for window in (3, 5, 7, 10, 14, 21, 30):
        row[f"PM25_roll_mean_{window}"] = float(history_series.iloc[-window:].mean())

    row["PM25_change_1"] = float(history_series.iloc[-1] - history_series.iloc[-2])
    row["PM25_change_3"] = float(history_series.iloc[-1] - history_series.iloc[-4])
    row["Temp_Range"] = row["Max_Temperature"] - row["Min_Temperature"]
    row["Month_sin"] = float(np.sin(2 * np.pi * month / 12))
    row["Month_cos"] = float(np.cos(2 * np.pi * month / 12))

    feature_df = pd.DataFrame([row])
    return feature_df[bundle["feature_columns"]]


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok", "model_name": bundle["model_name"]})


@app.get("/api/model-comparison")
def model_comparison():
    return jsonify(
        {
            "best_model": bundle["model_name"],
            "results": model_results,
        }
    )


@app.post("/api/predict")
def predict():
    payload = request.get_json(silent=True) or {}

    try:
        feature_df = build_feature_row(payload)
        transformed = bundle["preprocessor"].transform(feature_df)
        base_prediction = float(bundle["model"].predict(transformed)[0])
        visibility = clean_float(payload, "visibility")
        rainfall = clean_float(payload, "rainfall")
        prediction = float(
            np.clip(
                base_prediction
                + visibility_adjustment(visibility)
                + rainfall_adjustment(rainfall),
                5,
                500,
            )
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Prediction failed on the server"}), 500

    rounded_prediction = round(prediction, 2)
    return jsonify(
        {
            "type": "regression",
            "aqi": rounded_prediction,
            "category": categorize_pm25(prediction),
            "model_used": bundle["model_name"].lower().replace(" ", "_"),
            "model_name": bundle["model_name"],
            "city": str(payload.get("city") or "Bangalore"),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if not FRONTEND_BUILD_DIR.exists():
        return jsonify({"status": "ok", "message": "Backend API is running"}), 200
    if path and (FRONTEND_BUILD_DIR / path).exists():
        return send_from_directory(FRONTEND_BUILD_DIR, path)
    return send_from_directory(FRONTEND_BUILD_DIR, "index.html")


if __name__ == "__main__":
    app.run(debug=True)
