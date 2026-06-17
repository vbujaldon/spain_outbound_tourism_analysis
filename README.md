# 🌍 Tourism Intelligence Framework
## Evaluating Digital Demand Signals for Airline Seat Allocation

> **International Outbound Tourism Analysis — Spain (July 2019 – December 2025)**

---

## 📋Executive Summary

This project evaluates whether publicly available digital demand signals can anticipate Spanish outbound tourism demand, with application to tour operator and travel agency seat allocation decisions (typically negotiated **11–12 months in advance**).

The empirical analysis revealed **selective but limited predictive capacity**. Using Spearman rank correlation (justified by Shapiro–Wilk normality tests confirming non-normal distributions across all key variables), results show:

- Median Spearman r = **0.187** (monthly searches) and **0.176** (Google Trends) across 45 commercial destinations
- **40%** of destinations show statistically significant correlations (p < 0.05)
- Only **13% (6 of 45 destinations)** maintain useful predictive signal (r ≥ 0.3) at the 11-month planning horizon: Cambodia, China, Brazil, Oman, Colombia, Cabo Verde
- Search signals behave predominantly as **real-time monitors (lag 0–3 months)**, not as annual forecasting tools

Rather than forcing a universal forecasting model with unstable signal quality, the project evolved into a **Territorial Tourism Intelligence Framework** combining digital signals, official mobility data, and territorial concentration analysis.

---

## 🗂️ Data Architecture & Pipeline

The project integrates multiple heterogeneous data sources:

1. **INE Experimental Outbound Mobility Dataset** — Mobile phone positioning data, corrected to 100% of the Spanish population via CNMC telecom market share factors. Granularity: municipality × destination × month. Coverage: July 2019 – December 2025.

2. **Digital Signals**
   - **DataForSEO API** — Google monthly search volumes (absolute). Lower sparsity (<1% zeros) and higher structural stability.
   - **PyTrends (Google Trends)** — Relative search interest indices. ~60% structural zero values due to relative normalization compression, limiting baseline tracking utility.

3. **Semantic Mapping Layer** — Manually curated ontology translating broad search intent (e.g., *"viaje a los Balcanes"*, *"ruta por Indochina"*) into standard geopolitical destinations, built through web scraping of sector portals (webAZUL, webTDO) and validated against INE destination nomenclature.

4. **INE ETR (Encuesta de Turismo de Residentes)** — Used to derive continent-level behavioral adjustment factors (leisure trip ratios: América 38%, Asia & Oceania 61%, Africa 30%), validated against NTTO SIAT Spain profile data.

---

## 🔍 Key Findings

### 📡Signal Quality
| Signal | Zero Values | Structural Stability | Recommendation |
|---|---|---|---|
| DataForSEO (monthly searches) | ~1% | ✅ High | Primary signal |
| Google Trends (PyTrends) | ~25% | ⚠️ Low | Complement only |

Google Trends ~25% zeros are caused by **relative normalization compression**: when benchmark queries have very high volume, smaller destinations are compressed to zero despite real search activity.

### ⏱️ Predictive Capacity & Lag Analysis
Search signals are predominantly **concurrent** with tourism demand (optimal lag **0–3 months**). At the 11-month planning horizon:


```
Lag 0–3 months  ████████████████████  Best performance (real-time monitoring)
Lag 4–8 months  ██████████            Moderate decline
Lag 9–11 months ████                  Useful only for 6 destinations
Lag 12+ months  ██                    Excluded (seasonal autocorrelation risk)
```

- ✅ **6 of 45** commercial destinations: actionable signal (r ≥ 0.3) at lag 11m
- ❌ **14 of 45** destinations: negative correlation at lag 11m
- ⚠️ Signals are a **complement** to, not a substitute for, INE mobility data

### Behavioral Adjustment
A continent-level behavioral factor derived from INE ETR leisure/total trip ratios produced marginal improvements over the unadjusted baseline. A national-level factor significantly degraded correlations, confirming that within-continent heterogeneity requires at minimum continent-level segmentation.

### 🗺️ Territorial Concentration (Pareto Structure)
Long-haul outbound demand from Spain follows a strong Pareto structure:
```
Madrid + Barcelona  ████████████████████████████████  66% of long-haul demand
Top 7 provinces     ████████████████████████████████████████  ~80% of total
(14% of 50 prov.)
```

- 🏙️ **Madrid** alone: ~41% of commercial long-haul outbound
- 🏙️ **Barcelona**: ~24%
- 🏖️ Interior provinces → extreme August concentration
- 🌆 Metropolitan hubs → flatter, year-round profiles

--- 
### 🔢 Statistical Methodology

All correlations use **Spearman rank correlation**, justified by Shapiro–Wilk normality tests:

| Variable | Shapiro-Wilk W | p-value | Result |
|---|---|---|---|
| total_tourists | 0.33 | ≈ 0 | ❌ Not normal |
| monthly_searches | 0.71 | ≈ 0 | ❌ Not normal |
| trend_index | 0.86 | ≈ 0 | ❌ Not normal |

> Pearson correlation is inappropriate for right-skewed tourism data where a few large markets (USA: ~400K tourists) would dominate results.

---


## 🛠️ Tech Stack

| Domain | Technologies |
|---|---|
| 🐍 Language | Python 3.12 |
| 🔧 Data Engineering | Pandas · NumPy · Parquet |
| 🌐 Web Scraping & APIs | Selenium · BeautifulSoup · PyTrends · DataForSEO |
| 📊 Statistical Analysis | SciPy (Spearman · Shapiro-Wilk) |
| 📈 Visualization | Matplotlib · Seaborn · Plotly |
| 🚀 App Deployment | Streamlit |
| 💻 Development | Jupyter Notebook · VS Code |

---

## 📁 Repository Structure

```
TOURISM_PROJECT/
│
├── data/
│   ├── raw/                    # INE dumps, API responses, INE ETR files
│   ├── interim/
│   │   └── geo/                # Geographic enrichment files
│   └── processed/              # Final Parquet files ready for analysis
│
├── notebooks/
│   ├── 01_new_INE_data_cleaning.ipynb
│   ├── 02a_scraping_keywords_webAZUL.ipynb
│   ├── 02b_scraping_keywords_webTDO.ipynb
│   ├── 03_new_keyword_mapping.ipynb
│   ├── 04_search_query_creation.ipynb
│   ├── 05_new_DataForSeo_volume_searches.ipynb
│   ├── 06_new_Pytrends_google_trends.ipynb
│   ├── 07_build_final_datasets.ipynb
│   ├── 7.1_geographic_enrichment.ipynb
│   ├── 08_eda_demand_signals.ipynb
│   ├── 9.1_behavioral_adjustment_factor_continent.ipynb
│   └── 10_territorial_mobility_intelligence.ipynb
│
├── outputs/
│   ├── figures/                # Exported charts and maps
│   └── keywords/               # Keyword files for DataForSEO and Pytrends
│
├── tourism_dashboard/          # Streamlit application
│
├── Report/                     # Project report and presentation
├── requirements.txt
└── README.md
```

---

## 🚀 Future Work

- **Country-level behavioral factors** — INE ETR only disaggregates by continent; country-level VFR/leisure decomposition would improve signal adjustment accuracy
- **Expanded search intent coverage** — Beyond `"viaje a"`: `"circuito a"`, `"vuelos a"`, `"vacaciones en"` to capture broader agency-mediated demand
- **OAG/IATA capacity integration** — Cross-validate demand signals against actual seat supply data
- **Operational forecasting models** — Autoregressive features, macroeconomic indicators and transport connectivity variables
- **Streamlit dashboard** — Production-ready version adapted for travel agency operational use

---

## 📅 Data Period Note

INE mobility data covers **July 2019 – December 2025**.

| Period | Status | Notes |
|---|---|---|
| Jul–Dec 2019 | ✅ Used | H2 only — 2019 incomplete |
| 2020–2021 | ⚠️ Excluded from correlation/lag | COVID-19 structural distortion |
| 2022–2025 | ✅ Primary analysis period | Post-pandemic normalization |

---

## 📚 References

- Instituto Nacional de Estadística (INE). *Experimental Tourism Mobility from Mobile Phone Data*. 2019–2025.
- Instituto Nacional de Estadística (INE). *Encuesta de Turismo de Residentes (ETR)*. 2019–2025.
- NTTO. *Survey of International Air Travelers (SIAT) — Spain Profile*. 2024.
- DataForSEO. *Google Ads Search Volume API*. https://docs.dataforseo.com
- Choi, H. & Varian, H. (2012). Predicting the Present with Google Trends. *Economic Record*, 88(s1), 2–9.
- Önder, I. (2017). Forecasting tourism demand with Google Trends. *International Journal of Tourism Research*, 19(6), 648–660.


*Project by Vanessa Bujaldon · Data Analytics Specialization · June 2026*

