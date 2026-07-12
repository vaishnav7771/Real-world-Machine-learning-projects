"""
Shared utilities for the Sales Intelligence dashboard.

This mirrors the methodology from the underlying notebook
("End-to-End Sales Forecasting & Demand Intelligence System"):
  - Task 3/4: SARIMA vs XGBoost (lag-feature) forecasting, best model chosen by MAE
  - Task 5: Isolation Forest + Rolling Z-Score anomaly detection on weekly sales
  - Task 6: KMeans clustering of sub-categories on Total Sales / Growth / Volatility / AOV
"""
import os

# Must be set before numpy/scipy/xgboost/statsmodels are imported: keeps their
# native thread pools from contending with each other inside Streamlit's
# threaded script runner, which can otherwise cause rare native-code crashes.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import warnings
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "train.csv")

# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Order Date"])
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.month
    df["Quarter"] = df["Order Date"].dt.quarter
    df["YearMonth"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    return df


@st.cache_data
def yearly_sales(df):
    return df.groupby("Year", as_index=False)["Sales"].sum().sort_values("Year")


@st.cache_data
def monthly_sales(df):
    m = df.groupby(pd.Grouper(key="Order Date", freq="ME"))["Sales"].sum().reset_index()
    return m.rename(columns={"Order Date": "YearMonth"})


@st.cache_data
def sales_by_region_category(df):
    return df.groupby(["Region", "Category"], as_index=False)["Sales"].sum()


@st.cache_data
def monthly_series_for(df, dimension, value):
    """Monthly aggregated sales series (continuous, gap-filled) for a Category/Region value."""
    sub = df[df[dimension] == value]
    m = sub.groupby(pd.Grouper(key="Order Date", freq="ME"))["Sales"].sum()
    full_idx = pd.date_range(m.index.min(), m.index.max(), freq="ME")
    m = m.reindex(full_idx, fill_value=0.0)
    m.index.name = "YearMonth"
    return m


def get_season(month):
    if month in [12, 1, 2]:
        return 0  # Winter
    elif month in [3, 4, 5]:
        return 1  # Summer
    elif month in [6, 7, 8]:
        return 2  # Monsoon
    else:
        return 3  # Autumn


# ----------------------------------------------------------------------
# Forecasting: SARIMA vs XGBoost (lag features) — same two models as the
# notebook's Task 3 comparison; Prophet is intentionally excluded here
# because its cmdstan build is unreliable on Streamlit Community Cloud's
# free tier. Best model per series is selected by holdout MAE.
# ----------------------------------------------------------------------

def _sarima_forecast(train, horizon):
    model = SARIMAX(
        train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12),
        enforce_stationarity=False, enforce_invertibility=False,
    )
    fit = model.fit(disp=False)
    fc = fit.get_forecast(steps=horizon)
    return fc.predicted_mean


def _xgb_feature_frame(series):
    m = series.reset_index()
    m.columns = ["YearMonth", "Sales"]
    m["Lag_1"] = m["Sales"].shift(1)
    m["Lag_2"] = m["Sales"].shift(2)
    m["Lag_3"] = m["Sales"].shift(3)
    m["Rolling_Mean_3"] = m["Sales"].rolling(3).mean()
    m["Month"] = m["YearMonth"].dt.month
    m["Quarter"] = m["YearMonth"].dt.quarter
    m["Season"] = m["Month"].apply(get_season)
    return m


FEATURE_COLS = ["Lag_1", "Lag_2", "Lag_3", "Rolling_Mean_3", "Month", "Quarter", "Season"]


def _xgb_forecast(train_series, horizon):
    m = _xgb_feature_frame(train_series).dropna().reset_index(drop=True)
    X, y = m[FEATURE_COLS], m["Sales"]
    model = XGBRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=4,
        objective="reg:squarederror", random_state=42,
    )
    model.fit(X, y)

    # Iteratively roll forward, feeding predictions back in as lags
    history = list(train_series.values)
    last_date = train_series.index[-1]
    preds = []
    dates = []
    for _ in range(horizon):
        next_date = last_date + pd.offsets.MonthEnd(1)
        lag1, lag2, lag3 = history[-1], history[-2], history[-3]
        rolling = np.mean([lag1, lag2, lag3])
        month = next_date.month
        quarter = next_date.quarter
        season = get_season(month)
        X_future = pd.DataFrame([{
            "Lag_1": lag1, "Lag_2": lag2, "Lag_3": lag3,
            "Rolling_Mean_3": rolling, "Month": month,
            "Quarter": quarter, "Season": season,
        }])[FEATURE_COLS]
        pred = model.predict(X_future)[0]
        preds.append(pred)
        dates.append(next_date)
        history.append(pred)
        last_date = next_date

    return pd.Series(preds, index=pd.DatetimeIndex(dates))


@st.cache_resource
def fit_best_forecast_model(_df, dimension, value):
    """
    Fit SARIMA and XGBoost on a holdout split, pick the model with lower MAE,
    matching the notebook's Task 3/4 model-comparison approach.
    """
    series = monthly_series_for(_df, dimension, value)
    n = len(series)
    holdout = min(6, max(3, n // 5))
    train, test = series.iloc[:-holdout], series.iloc[-holdout:]

    results = {}
    try:
        sarima_preds = _sarima_forecast(train, holdout)
        mae = mean_absolute_error(test.values, sarima_preds.values)
        rmse = np.sqrt(mean_squared_error(test.values, sarima_preds.values))
        results["SARIMA"] = {"mae": mae, "rmse": rmse}
    except Exception:
        pass

    try:
        xgb_preds = _xgb_forecast(train, holdout)
        mae = mean_absolute_error(test.values, xgb_preds.values)
        rmse = np.sqrt(mean_squared_error(test.values, xgb_preds.values))
        results["XGBoost (Lag Features)"] = {"mae": mae, "rmse": rmse}
    except Exception:
        pass

    if not results:
        raise RuntimeError("No forecasting model could be fit for this series.")

    best_name = min(results, key=lambda k: results[k]["mae"])
    best_metrics = results[best_name]

    return {
        "series": series,
        "best_model": best_name,
        "mae": best_metrics["mae"],
        "rmse": best_metrics["rmse"],
        "all_results": results,
    }


def forecast_future(series, model_name, horizon):
    """Refit the chosen model on the FULL series and forecast `horizon` months ahead."""
    if model_name == "SARIMA":
        return _sarima_forecast(series, horizon)
    elif model_name == "XGBoost (Lag Features)":
        return _xgb_forecast(series, horizon)
    else:
        raise ValueError(f"Unknown model: {model_name}")


# ----------------------------------------------------------------------
# Anomaly detection (Task 5 / Page 3): Isolation Forest + Rolling Z-Score
# on WEEKLY sales, exactly as in the notebook.
# ----------------------------------------------------------------------

@st.cache_data
def detect_anomalies(df):
    weekly = df.groupby(pd.Grouper(key="Order Date", freq="W"))["Sales"].sum().reset_index()

    # Isolation Forest (matches notebook: n_estimators=100, contamination=0.05)
    iso_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    weekly["IsoAnomaly"] = iso_forest.fit_predict(weekly[["Sales"]]) == -1

    # Rolling Z-Score (matches notebook: 4-week window, |z| > 2)
    weekly["Rolling Mean"] = weekly["Sales"].rolling(window=4).mean()
    weekly["Rolling Std"] = weekly["Sales"].rolling(window=4).std()
    weekly["Z-Score"] = (weekly["Sales"] - weekly["Rolling Mean"]) / weekly["Rolling Std"]
    weekly["ZAnomaly"] = weekly["Z-Score"].abs() > 2

    avg_sales = weekly["Sales"].mean()
    weekly["Anomaly Type"] = np.where(weekly["Sales"] > avg_sales, "High Sales Anomaly", "Low Sales Anomaly")

    return weekly, avg_sales


# ----------------------------------------------------------------------
# Clustering (Task 6 / Page 4): KMeans on the same 4 features used in the
# notebook — Total Sales Volume, Sales Growth Rate (%), Sales Volatility,
# Average Order Value.
# ----------------------------------------------------------------------

@st.cache_data
def cluster_subcategories(df, n_clusters=3):
    monthly_sub = df.groupby(["Sub-Category", pd.Grouper(key="Order Date", freq="ME")])["Sales"].sum().reset_index()
    monthly_sub["Year"] = monthly_sub["Order Date"].dt.year

    yearly_sub = monthly_sub.groupby(["Sub-Category", "Year"])["Sales"].sum().reset_index()
    yearly_sub["YoY Growth (%)"] = yearly_sub.groupby("Sub-Category")["Sales"].pct_change() * 100
    avg_growth = yearly_sub.groupby("Sub-Category")["YoY Growth (%)"].mean().fillna(0)

    feat = pd.DataFrame({
        "Total Sales Volume": df.groupby("Sub-Category")["Sales"].sum(),
        "Average Order Value": df.groupby("Sub-Category")["Sales"].mean(),
        "Sales Volatility": monthly_sub.groupby("Sub-Category")["Sales"].std(),
        "Sales Growth Rate (%)": avg_growth,
    }).fillna(0).reset_index()

    X = feat[["Total Sales Volume", "Sales Growth Rate (%)", "Sales Volatility", "Average Order Value"]].values
    X_scaled = StandardScaler().fit_transform(X)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    feat["Cluster"] = km.fit_predict(X_scaled)

    # PCA projection for 2D plotting
    pca = PCA(n_components=2)
    coords = pca.fit_transform(X_scaled)
    feat["PC1"], feat["PC2"] = coords[:, 0], coords[:, 1]
    explained_var = pca.explained_variance_ratio_

    # Dynamically label clusters based on their characteristics rather than
    # hardcoded indices, so labels stay meaningful regardless of cluster order.
    summary = feat.groupby("Cluster").agg(
        {"Total Sales Volume": "mean", "Sales Growth Rate (%)": "mean", "Sales Volatility": "mean"}
    )
    growth_rank = summary["Sales Growth Rate (%)"].rank(ascending=False)
    volume_rank = summary["Total Sales Volume"].rank(ascending=False)

    def label_cluster(c):
        if growth_rank[c] == growth_rank.min() and summary.loc[c, "Sales Growth Rate (%)"] > 0:
            return "Growing Demand"
        elif summary.loc[c, "Sales Growth Rate (%)"] < 0:
            return "Declining Demand"
        elif volume_rank[c] == volume_rank.min():
            return "High Volume, Stable Demand"
        else:
            return "Moderate, Stable Demand"

    cluster_names = {c: label_cluster(c) for c in summary.index}
    feat["Demand Segment"] = feat["Cluster"].map(cluster_names)

    return feat.sort_values("Total Sales Volume", ascending=False), summary.round(2), explained_var
