import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def md(text: str) -> dict:
    lines = text.strip("\n").split("\n")
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in lines[:-1]] + ([lines[-1]] if lines else []),
    }


def code(text: str) -> dict:
    lines = text.strip("\n").split("\n")
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in lines[:-1]] + ([lines[-1]] if lines else []),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
                "mimetype": "text/x-python",
                "codemirror_mode": {"name": "ipython", "version": 3},
                "pygments_lexer": "ipython3",
                "nbconvert_exporter": "python",
                "file_extension": ".py",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


common_setup = """
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

sns.set_style("whitegrid")
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 100)

BASE_DIR = Path.cwd()
AQI_DIR = BASE_DIR / "data" / "AQI"
HTML_DIR = BASE_DIR / "data" / "html_data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)
"""


scrape_helpers = """
import sys
import subprocess

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup


def parse_weather_html_files(html_root: Path) -> pd.DataFrame:
    rows = []

    for html_file in sorted(html_root.rglob("*.html")):
        year = html_file.parent.name
        month = html_file.stem.split("-")[0]

        soup = BeautifulSoup(html_file.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 4:
            continue

        climate_table = tables[3]
        for tr in climate_table.find_all("tr")[1:]:
            cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["td", "th"])]
            if len(cells) < 15 or not cells[0].isdigit():
                continue

            day = int(cells[0])
            rows.append(
                {
                    "Date": f"{year}-{int(month):02d}-{day:02d}",
                    "Avg_Temperature": cells[1],
                    "Max_Temperature": cells[2],
                    "Min_Temperature": cells[3],
                    "Sea_Level_Pressure": cells[4],
                    "Humidity": cells[5],
                    "Rainfall_Snowmelt": cells[6],
                    "Visibility": cells[7],
                    "Wind_Speed": cells[8],
                    "Max_Sustained_Wind_Speed": cells[9],
                    "Max_Wind_Gust": cells[10],
                    "City": "Bangalore",
                    "weather_source_file": html_file.name,
                }
            )

    weather_df = pd.DataFrame(rows)
    weather_df["Date"] = pd.to_datetime(weather_df["Date"], errors="coerce")

    numeric_weather_cols = [
        "Avg_Temperature",
        "Max_Temperature",
        "Min_Temperature",
        "Sea_Level_Pressure",
        "Humidity",
        "Rainfall_Snowmelt",
        "Visibility",
        "Wind_Speed",
        "Max_Sustained_Wind_Speed",
        "Max_Wind_Gust",
    ]

    for col in numeric_weather_cols:
        weather_df[col] = pd.to_numeric(
            weather_df[col].replace({"-": np.nan, "": np.nan}),
            errors="coerce"
        )

    weather_df["Month"] = weather_df["Date"].dt.month
    weather_df["Year"] = weather_df["Date"].dt.year
    weather_df["Day"] = weather_df["Date"].dt.day
    weather_df["DayOfWeek"] = weather_df["Date"].dt.dayofweek
    weather_df["IsWeekend"] = weather_df["DayOfWeek"].isin([5, 6]).astype(int)
    weather_df["Season"] = weather_df["Month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Summer", 4: "Summer", 5: "Summer",
        6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
        10: "Post-Monsoon", 11: "Post-Monsoon"
    })

    return weather_df


def load_and_aggregate_pm25(aqi_root: Path) -> pd.DataFrame:
    frames = []

    for csv_file in sorted(aqi_root.glob("*.csv")):
        df = pd.read_csv(csv_file)
        df.columns = [col.strip() for col in df.columns]
        df["Date"] = pd.to_datetime(df["Date"].astype(str).str.strip(), errors="coerce")
        df["Time"] = df["Time"].astype(str).str.strip()
        df["PM2.5"] = pd.to_numeric(df["PM2.5"], errors="coerce")
        frames.append(df)

    aqi_df = pd.concat(frames, ignore_index=True)
    aqi_df = aqi_df.drop_duplicates(subset=["Date", "Time", "PM2.5"]).copy()

    daily_pm25 = (
        aqi_df.groupby("Date", as_index=False)
        .agg(
            Daily_PM25=("PM2.5", "mean"),
            PM25_Observation_Count=("PM2.5", lambda s: s.notna().sum()),
        )
    )

    return daily_pm25
"""


nb1 = notebook([
    md("""
# 01 Data Loading and Understanding

This notebook builds a daily weather plus PM2.5 dataset by:
- scraping weather values from the monthly HTML climate files
- aggregating hourly PM2.5 values into daily PM2.5
- merging both sources by date
"""),
    code(common_setup),
    code(scrape_helpers),
    code("""
weather_df = parse_weather_html_files(HTML_DIR)
print("Weather data shape:", weather_df.shape)
weather_df.head()
"""),
    code("""
daily_pm25_df = load_and_aggregate_pm25(AQI_DIR)
print("Daily PM2.5 data shape:", daily_pm25_df.shape)
daily_pm25_df.head()
"""),
    code("""
merged_df = weather_df.merge(daily_pm25_df, on="Date", how="inner").sort_values("Date").reset_index(drop=True)

print("Merged dataset shape:", merged_df.shape)
print("Date range:", merged_df["Date"].min(), "to", merged_df["Date"].max())
merged_df.head()
"""),
    code("""
print("Shape of data:", merged_df.shape)
print("\\nData types:")
display(merged_df.dtypes.to_frame(name="dtype"))
"""),
    code("""
null_summary = pd.DataFrame({
    "missing_count": merged_df.isna().sum(),
    "missing_percent": (merged_df.isna().sum() / len(merged_df) * 100).round(2)
}).sort_values("missing_count", ascending=False)

null_summary
"""),
    code("""
merged_df.describe(include="all").transpose()
"""),
    code("""
plt.figure(figsize=(10, 5))
sns.histplot(merged_df["Daily_PM25"].dropna(), bins=30, kde=True)
plt.title("Target Distribution: Daily PM2.5")
plt.tight_layout()
plt.show()
"""),
    code("""
weather_df.to_csv(ARTIFACTS_DIR / "weather_daily_scraped.csv", index=False)
daily_pm25_df.to_csv(ARTIFACTS_DIR / "pm25_daily_aggregated.csv", index=False)
merged_df.to_csv(ARTIFACTS_DIR / "weather_pm25_merged.csv", index=False)

print("Saved merged PM2.5 dataset artifacts.")
"""),
])


nb2 = notebook([
    md("""
# 02 EDA Visualization

This notebook explores the relationship between weather features and daily PM2.5.
"""),
    code(common_setup),
    code("""
data = pd.read_csv(ARTIFACTS_DIR / "weather_pm25_merged.csv", parse_dates=["Date"])
data.head()
"""),
    code("""
numeric_cols = [
    "Avg_Temperature",
    "Max_Temperature",
    "Min_Temperature",
    "Humidity",
    "Rainfall_Snowmelt",
    "Visibility",
    "Wind_Speed",
    "Max_Sustained_Wind_Speed",
    "Daily_PM25",
    "Month",
    "Day",
    "DayOfWeek"
]

data[numeric_cols].describe().transpose()
"""),
    code("""
data[numeric_cols].hist(figsize=(16, 12), bins=25, edgecolor="black")
plt.suptitle("Histograms of Numeric Variables", y=1.02)
plt.tight_layout()
plt.show()
"""),
    code("""
plt.figure(figsize=(12, 8))
sns.heatmap(data[numeric_cols].corr(), annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Heatmap")
plt.tight_layout()
plt.show()
"""),
    code("""
plt.figure(figsize=(10, 5))
sns.boxplot(data=data, x="Season", y="Daily_PM25", order=["Winter", "Summer", "Monsoon", "Post-Monsoon"])
plt.title("Daily PM2.5 by Season")
plt.tight_layout()
plt.show()
"""),
    code("""
plt.figure(figsize=(10, 5))
sns.scatterplot(data=data, x="Humidity", y="Daily_PM25", alpha=0.7)
plt.title("Humidity vs Daily PM2.5")
plt.tight_layout()
plt.show()
"""),
    code("""
plt.figure(figsize=(10, 5))
sns.scatterplot(data=data, x="Visibility", y="Daily_PM25", alpha=0.7)
plt.title("Visibility vs Daily PM2.5")
plt.tight_layout()
plt.show()
"""),
])


nb3 = notebook([
    md("""
# 03 Data Preprocessing

This notebook prepares the base weather dataset for PM2.5 modeling and saves the cleaned daily table for feature engineering.
"""),
    code(common_setup),
    code("""
data = pd.read_csv(ARTIFACTS_DIR / "weather_pm25_merged.csv", parse_dates=["Date"])
data.head()
"""),
    code("""
base_columns = [
    "Date",
    "Avg_Temperature",
    "Max_Temperature",
    "Min_Temperature",
    "Humidity",
    "Rainfall_Snowmelt",
    "Visibility",
    "Wind_Speed",
    "Max_Sustained_Wind_Speed",
    "City",
    "Month",
    "Year",
    "Day",
    "DayOfWeek",
    "IsWeekend",
    "Season",
    "Daily_PM25"
]

model_data = data[base_columns].sort_values("Date").reset_index(drop=True)

print("Prepared dataset shape:", model_data.shape)
model_data.head()
"""),
    code("""
joblib.dump(model_data, ARTIFACTS_DIR / "pm25_base_model_data.joblib")
model_data.to_csv(ARTIFACTS_DIR / "pm25_base_model_data.csv", index=False)

print("Saved base PM2.5 modeling dataset.")
"""),
])


nb4 = notebook([
    md("""
# 04 Feature Engineering

This notebook creates lag and rolling PM2.5 features.

Note:
- these lag features use previous PM2.5 history
- this usually improves R2 a lot compared with weather-only prediction
"""),
    code(common_setup + """
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
"""),
    code("""
data = joblib.load(ARTIFACTS_DIR / "pm25_base_model_data.joblib")
data.head()
"""),
    code("""
feature_data = data.copy()

for lag in [1, 2, 3, 5, 7, 10, 14, 21, 30]:
    feature_data[f"PM25_lag_{lag}"] = feature_data["Daily_PM25"].shift(lag)

for window in [3, 5, 7, 10, 14, 21, 30]:
    feature_data[f"PM25_roll_mean_{window}"] = feature_data["Daily_PM25"].shift(1).rolling(window).mean()

feature_data["PM25_change_1"] = feature_data["Daily_PM25"].shift(1) - feature_data["Daily_PM25"].shift(2)
feature_data["PM25_change_3"] = feature_data["Daily_PM25"].shift(1) - feature_data["Daily_PM25"].shift(4)
feature_data["Temp_Range"] = feature_data["Max_Temperature"] - feature_data["Min_Temperature"]
feature_data["Month_sin"] = np.sin(2 * np.pi * feature_data["Month"] / 12)
feature_data["Month_cos"] = np.cos(2 * np.pi * feature_data["Month"] / 12)

feature_data = feature_data.dropna().reset_index(drop=True)

print("Feature engineered dataset shape:", feature_data.shape)
feature_data.head()
"""),
    code("""
feature_columns = [col for col in feature_data.columns if col not in ["Date", "Daily_PM25"]]
target_column = "Daily_PM25"

split_index = int(len(feature_data) * 0.75)
train_df = feature_data.iloc[:split_index].copy()
test_df = feature_data.iloc[split_index:].copy()

X_train = train_df[feature_columns]
X_test = test_df[feature_columns]
y_train = train_df[target_column]
y_test = test_df[target_column]

numeric_features = X_train.select_dtypes(include=[np.number]).columns.tolist()
categorical_features = [col for col in X_train.columns if col not in numeric_features]

preprocessor = ColumnTransformer(transformers=[
    ("num", Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ]), numeric_features),
    ("cat", Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ]), categorical_features)
])

X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

print("Train rows:", len(train_df))
print("Test rows :", len(test_df))
print("Processed X_train shape:", X_train_processed.shape)
print("Processed X_test shape :", X_test_processed.shape)
"""),
    code("""
joblib.dump(preprocessor, ARTIFACTS_DIR / "pm25_preprocessor.joblib")
joblib.dump(feature_data, ARTIFACTS_DIR / "pm25_feature_data.joblib")
joblib.dump(X_train_processed, ARTIFACTS_DIR / "pm25_X_train_processed.joblib")
joblib.dump(X_test_processed, ARTIFACTS_DIR / "pm25_X_test_processed.joblib")
joblib.dump(y_train.reset_index(drop=True), ARTIFACTS_DIR / "pm25_y_train.joblib")
joblib.dump(y_test.reset_index(drop=True), ARTIFACTS_DIR / "pm25_y_test.joblib")

print("Saved feature engineered artifacts.")
"""),
])


nb5 = notebook([
    md("""
# 05 Model Training

This notebook trains a curated set of strong PM2.5 regressors and compares them using R2, MAE, and RMSE.
"""),
    code("""
import sys
import subprocess

try:
    import xgboost
    print("xgboost version:", xgboost.__version__)
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xgboost"])
    import xgboost
    print("xgboost installed. version:", xgboost.__version__)
"""),
    code(common_setup + """
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor
"""),
    code("""
X_train_processed = joblib.load(ARTIFACTS_DIR / "pm25_X_train_processed.joblib")
X_test_processed = joblib.load(ARTIFACTS_DIR / "pm25_X_test_processed.joblib")
y_train = joblib.load(ARTIFACTS_DIR / "pm25_y_train.joblib")
y_test = joblib.load(ARTIFACTS_DIR / "pm25_y_test.joblib")

print("Training data shape:", X_train_processed.shape)
print("Testing data shape :", X_test_processed.shape)
"""),
    code("""
models = {
    "Gradient Boosting": GradientBoostingRegressor(
        random_state=42,
        n_estimators=700,
        learning_rate=0.02,
        max_depth=2
    ),
    "XGBoost": XGBRegressor(
        n_estimators=1200,
        max_depth=3,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42
    ),
    "Random Forest": RandomForestRegressor(
        n_estimators=1500,
        random_state=42,
        max_depth=None,
        min_samples_leaf=1
    ),
    "AdaBoost": AdaBoostRegressor(
        random_state=42,
        n_estimators=500,
        learning_rate=0.03
    ),
    "Extra Trees": ExtraTreesRegressor(
        n_estimators=1500,
        random_state=42,
        max_depth=18,
        min_samples_leaf=1
    ),
    "SVR": SVR(
        C=50,
        epsilon=0.05,
        gamma="scale"
    ),
    "KNN": KNeighborsRegressor(
        n_neighbors=3,
        weights="distance"
    )
}

print("Models to train:", list(models.keys()))
"""),
    code("""
trained_models = {}
training_results = []

for name, model in models.items():
    model.fit(X_train_processed, y_train)
    predictions = model.predict(X_test_processed)
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    trained_models[name] = model
    training_results.append({
        "model": name,
        "r2_score": r2,
        "mae": mae,
        "rmse": rmse
    })

results_df = pd.DataFrame(training_results).sort_values("r2_score", ascending=False).reset_index(drop=True)
results_df
"""),
    code("""
for name, model in trained_models.items():
    safe_name = name.lower().replace(" ", "_")
    joblib.dump(model, ARTIFACTS_DIR / f"{safe_name}_model.joblib")

results_df.to_csv(ARTIFACTS_DIR / "pm25_model_training_results.csv", index=False)
joblib.dump(list(trained_models.keys()), ARTIFACTS_DIR / "pm25_trained_model_names.joblib")

print("Saved trained PM2.5 models and summary.")
"""),
    code("""
plt.figure(figsize=(10, 5))
sns.barplot(data=results_df, x="r2_score", y="model", palette="viridis")
plt.title("PM2.5 Model R2 Score Comparison")
plt.xlim(0.5, 1.0)
plt.tight_layout()
plt.show()
"""),
])


nb6 = notebook([
    md("""
# 06 Model Evaluation

This notebook evaluates the trained PM2.5 regression models using:
- R2 score
- MAE
- RMSE
- actual vs predicted plot
- residual distribution
"""),
    code(common_setup + """
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
"""),
    code("""
X_test_processed = joblib.load(ARTIFACTS_DIR / "pm25_X_test_processed.joblib")
y_test = joblib.load(ARTIFACTS_DIR / "pm25_y_test.joblib")
model_names = joblib.load(ARTIFACTS_DIR / "pm25_trained_model_names.joblib")

evaluation_rows = []
predictions_map = {}

for name in model_names:
    safe_name = name.lower().replace(" ", "_")
    model = joblib.load(ARTIFACTS_DIR / f"{safe_name}_model.joblib")
    predictions = model.predict(X_test_processed)
    predictions_map[name] = predictions
    evaluation_rows.append({
        "model": name,
        "r2_score": r2_score(y_test, predictions),
        "mae": mean_absolute_error(y_test, predictions),
        "rmse": np.sqrt(mean_squared_error(y_test, predictions))
    })

evaluation_df = pd.DataFrame(evaluation_rows).sort_values("r2_score", ascending=False).reset_index(drop=True)
evaluation_df
"""),
    code("""
best_model_name = evaluation_df.iloc[0]["model"]
best_predictions = predictions_map[best_model_name]

print("Best model:", best_model_name)
print("Best R2 score:", evaluation_df.iloc[0]["r2_score"])
print("Best MAE:", evaluation_df.iloc[0]["mae"])
print("Best RMSE:", evaluation_df.iloc[0]["rmse"])
"""),
    code("""
plt.figure(figsize=(7, 7))
plt.scatter(y_test, best_predictions, alpha=0.7)
plt.xlabel("Actual PM2.5")
plt.ylabel("Predicted PM2.5")
plt.title(f"Actual vs Predicted PM2.5 - {best_model_name}")
min_val = min(y_test.min(), best_predictions.min())
max_val = max(y_test.max(), best_predictions.max())
plt.plot([min_val, max_val], [min_val, max_val], "r--")
plt.tight_layout()
plt.show()
"""),
    code("""
residuals = y_test - best_predictions

plt.figure(figsize=(8, 4))
sns.histplot(residuals, bins=20, kde=True)
plt.title(f"Residual Distribution - {best_model_name}")
plt.xlabel("Residual")
plt.tight_layout()
plt.show()
"""),
    code("""
evaluation_df.to_csv(ARTIFACTS_DIR / "pm25_model_evaluation_results.csv", index=False)
print("Saved PM2.5 evaluation summary.")
"""),
])


files = {
    "01_data_loading_and_understanding.ipynb": nb1,
    "02_eda_visualization.ipynb": nb2,
    "03_data_preprocessing.ipynb": nb3,
    "04_feature_engineering_lda.ipynb": nb4,
    "05_model_training.ipynb": nb5,
    "06_model_evaluation.ipynb": nb6,
}


for name, content in files.items():
    (ROOT / name).write_text(json.dumps(content, indent=1), encoding="utf-8")
    print(f"Created {name}")
