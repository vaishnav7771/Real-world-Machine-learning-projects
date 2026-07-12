# ⟡ Nexus Sales Intelligence — Streamlit Dashboard

An interactive, multi-page Streamlit app built on top of your
**End-to-End Sales Forecasting & Demand Intelligence** notebook (Tasks 1–6),
covering Task 7 (Deployment).

## Pages

| Page | Contents |
|---|---|
| **📊 Sales Overview** | Total sales by year (bar), monthly sales trend (line), sales by Region × Category with interactive filters |
| **🔮 Forecast Explorer** | Dropdown for Category/Region, 1–3 month horizon slider, forecast from the **best model** (SARIMA vs XGBoost, auto-selected by holdout MAE), MAE/RMSE shown |
| **🚨 Anomaly Report** | Weekly sales anomaly chart (Isolation Forest / Rolling Z-Score toggle), table of anomaly dates + sales values |
| **🧩 Product Demand Segments** | KMeans cluster chart (PCA projection) of sub-categories, table mapping sub-categories to demand clusters |

## Modeling notes (matches your notebook's methodology)

- **Forecasting**: Task 3 compared SARIMA, Prophet, and XGBoost. This app compares **SARIMA** and **XGBoost (lag features)** live for whichever Category/Region you pick, and auto-selects the one with the lower holdout MAE. **Prophet was intentionally left out** — its `cmdstan` build step is unreliable on Streamlit Community Cloud's free tier and frequently causes deployment failures.
- **Anomaly detection**: Isolation Forest (`n_estimators=100, contamination=0.05`) and Rolling Z-Score (4-week window, `|z| > 2`) on weekly sales — identical parameters to Task 5.
- **Clustering**: KMeans (k=3) on Total Sales Volume, Sales Growth Rate (%), Sales Volatility, and Average Order Value — identical features to Task 6. Cluster labels (e.g. "Growing Demand") are computed dynamically from each cluster's characteristics rather than hardcoded.

## Project structure

```
dashboard/
├── Home.py                          # Landing page
├── pages/
│   ├── 1_📊_Sales_Overview.py
│   ├── 2_🔮_Forecast_Explorer.py
│   ├── 3_🚨_Anomaly_Report.py
│   └── 4_🧩_Product_Demand_Segments.py
├── utils.py                         # Data loading, models, anomaly detection, clustering
├── style.py                         # Futuristic dark theme (CSS + Plotly template)
├── data/
│   └── train.csv                    # Superstore sales data
├── .streamlit/
│   └── config.toml                  # Theme config
└── requirements.txt
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Deploy to Streamlit Community Cloud (free)

1. **Create a GitHub repo** and push this entire `dashboard/` folder to it (as the repo root, or note the subfolder path for step 4).
   ```bash
   cd dashboard
   git init
   git add .
   git commit -m "Nexus Sales Intelligence dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with your GitHub account.
3. Click **"Create app"** → **"Deploy a public app from GitHub"**.
4. Select your repo, branch (`main`), and set the **main file path** to `Home.py` (or `dashboard/Home.py` if you pushed it inside a larger repo).
5. Click **Deploy**. The first build takes a few minutes (installing statsmodels/xgboost/scikit-learn).
6. Once live, you'll get a URL like `https://<your-app-name>.streamlit.app` — submit that link.

### If the build fails
- Check the "Manage app" logs for the specific package that failed.
- Make sure `data/train.csv` was actually committed (large CSVs are sometimes accidentally `.gitignore`'d).
- Streamlit Cloud's free tier has ~1GB memory; this app is lightweight enough to fit comfortably.

## Data

`data/train.csv` is the Superstore sales dataset (2015–2018): 9,800 orders across
Furniture, Office Supplies, and Technology categories, and East/West/Central/South regions.
