# Air Quality Prediction Using Weather Data

This project predicts daily PM2.5 / AQI-like pollution levels using weather features and time-series PM2.5 history.  
The final deployed model is a `Random Forest Regressor`, served through a Flask backend and a React frontend.

## Project Overview

The workflow in this project is:

1. Load and merge daily weather data with PM2.5 observations
2. Clean and preprocess the dataset
3. Create lag and rolling PM2.5 features
4. Train multiple regression models
5. Compare models using `R²`, `MAE`, and `RMSE`
6. Select the final model for deployment
7. Serve predictions through a web app

## Final Model

- Final deployed model: `Random Forest`
- Current train/test split: `795` train rows and `251` test rows
- Test-set `R²` scores:
  - `Random Forest`: `0.820760`
  - `Extra Trees`: `0.815294`
  - `AdaBoost`: `0.801368`
  - `XGBoost`: `0.799729`
  - `Gradient Boosting`: `0.798571`
  - `SVR`: `0.762164`
  - `KNN`: `0.760043`

## Notebook Pipeline

The notebooks are organized in sequence:

- [01_data_loading_and_understanding.ipynb](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/01_data_loading_and_understanding.ipynb)
  Loads weather and AQI data, merges them, and saves base artifacts.
- [02_eda_visualization.ipynb](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/02_eda_visualization.ipynb)
  Performs exploratory data analysis and visualizations.
- [03_data_preprocessing.ipynb](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/03_data_preprocessing.ipynb)
  Cleans the merged dataset and prepares the base modeling table.
- [04_feature_engineering_lda.ipynb](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/04_feature_engineering_lda.ipynb)
  Adds lag, rolling mean, and seasonal features, then creates the chronological train/test split.
- [05_model_training.ipynb](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/05_model_training.ipynb)
  Trains all regression models and compares their scores.
- [06_model_evaluation.ipynb](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/06_model_evaluation.ipynb)
  Evaluates the trained models and confirms the best one.
- [07_model_testing_and_prediction.ipynb](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/07_model_testing_and_prediction.ipynb)
  Demonstrates predictions using the best trained model.
- [08_model_saving_loading.ipynb](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/08_model_saving_loading.ipynb)
  Saves and reloads the deployment bundle.

## Main Project Files

- [app.py](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/app.py)
  Flask backend for prediction APIs and static frontend serving.
- [generate_notebooks.py](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/generate_notebooks.py)
  Script used to generate/update notebook structures.
- [requirements.txt](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/requirements.txt)
  Python dependencies.
- [vercel.json](C:/Users/Anshul/Desktop/ml%20sem%204%20mini%20project/vercel.json)
  Deployment configuration.

## Important Folders

- `data/AQI/`
  Raw AQI / PM2.5 CSV files.
- `data/html_data/`
  Raw weather HTML files used for scraping and aggregation.
- `artifacts/`
  Processed datasets, preprocessors, trained model files, and evaluation outputs.
- `deployment_assets/`
  Final deployment bundle:
  - `best_pm25_model_bundle.joblib`
- `front end/`
  React frontend source and build files.

## Backend API

Main endpoints in `app.py`:

- `GET /api/health`
  Returns backend status and deployed model name.
- `GET /api/model-comparison`
  Returns model metrics shown on the frontend.
- `POST /api/predict`
  Accepts weather inputs and returns predicted AQI / PM2.5 category and score.

## Frontend

The frontend is built with React and currently displays:

- climate input form
- AQI gauge
- predicted AQI result card
- model comparison section
- deployed model as `Random Forest`

Frontend source is in:

- `front end/src/`

Production build output is in:

- `front end/build/`

## How To Run Locally

### Backend

```bash
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd "front end"
npm install
npm start
```

If you want the production frontend build:

```bash
cd "front end"
npm run build
```

## Files To Upload To GitHub

You should upload these project files and folders:

- `README.md`
- `.gitignore`
- `requirements.txt`
- `vercel.json`
- `app.py`
- `generate_notebooks.py`
- `01_data_loading_and_understanding.ipynb`
- `02_eda_visualization.ipynb`
- `03_data_preprocessing.ipynb`
- `04_feature_engineering_lda.ipynb`
- `05_model_training.ipynb`
- `06_model_evaluation.ipynb`
- `07_model_testing_and_prediction.ipynb`
- `08_model_saving_loading.ipynb`
- `data/`
- `artifacts/`
- `deployment_assets/`
- `front end/src/`
- `front end/public/`
- `front end/package.json`
- `front end/package-lock.json`
- `front end/.env.example`
- `front end/README.md`

## Files You Should Usually Not Upload

Unless you specifically want built or temporary files in the repo, do not upload:

- `front end/node_modules/`
- `__pycache__/`
- `front end/frontend-run.log`

Optional:

- `front end/build/`
  Upload this only if you want the compiled frontend included in the repository.  
  If your deployment process builds the frontend automatically, you can skip it.

## How To Replace The Old README On GitHub

You have two easy options.

### Option 1: Replace from GitHub website

1. Open your repository on GitHub.
2. Open the existing `README.md`.
3. Click the pencil icon to edit.
4. Delete the old content.
5. Copy and paste the new `README.md` content from this project.
6. Scroll down and click `Commit changes`.

### Option 2: Replace by uploading from your computer

1. Open your repository on GitHub.
2. Click `Add file`.
3. Click `Upload files`.
4. Drag the new `README.md` into the page.
5. If GitHub shows that `README.md` already exists, it will replace it in the commit.
6. Add a commit message like `Update project README`.
7. Click `Commit changes`.

## Recommended GitHub Upload Order

If you are manually uploading files in the browser, do it in this order:

1. Upload `README.md`, notebooks, `app.py`, `generate_notebooks.py`, and config files
2. Upload `front end/src/`, `front end/public/`, and frontend package files
3. Upload `artifacts/` and `deployment_assets/`
4. Upload `data/` if you want the raw dataset included in the repo

## Notes

- The current project state uses `Random Forest` as the final deployed model.
- The frontend model comparison values are sourced from the notebook-backed results.
- The notebooks have been updated to reflect the latest split, scores, and final model selection.
