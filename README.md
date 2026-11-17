# Which Megaline plan brings in more money?

**Live app:** [megaline-plan-analysis.streamlit.app](https://megaline-plan-analysis.streamlit.app/) · **Notebook and project folder:** [AIOPS-Portfolio-Projects](https://github.com/ahmadhassan-aiops/AIOPS-Portfolio-Projects/tree/main/1.%20Data-analysis-with-python-Projects/Megaline%20Analysis)

An interactive presentation of a telecom revenue analysis by **Ahmad Hassan** (AI Engineer).
Megaline sells two prepaid plans, Surf ($20 + extras) and Ultimate ($70). Using 500 customers' calls, texts
and data for 2018, the analysis prices every customer's month, compares how the plans are used and tests
which plan earns more.

- **Key findings**: the answer, the numbers behind it, and recommendations for the advertising budget.
- **How customers use their plan**: minutes, texts and data per customer per month, by plan.
- **Revenue**: what customers pay, where Surf's revenue comes from, totals over the year.
- **Hypothesis tests**: Surf vs Ultimate and New York-New Jersey vs elsewhere (Welch's t-test with a
  Mann-Whitney check), with an adjustable significance level and a per-customer option.
- **The analysis table**: how raw call, text and data logs become one row per customer per month, with an
  explorer and CSV download.
- **Data & method**: preparation, two corrections to the original calculation, and the limits of the data.

Notebook (updated with the corrections described in the app): [AIOPS-Portfolio-Projects / Megaline Analysis](https://github.com/ahmadhassan-aiops/AIOPS-Portfolio-Projects/tree/main/1.%20Data-analysis-with-python-Projects/Megaline%20Analysis)

## How it is built

```
app.py            entry point (top navigation)
nav.py            page registry
views/            one module per page
lib/data.py       cached loaders for data/
lib/charts.py     Plotly styling and chart builders
lib/ui.py         headers, callouts, footer
lib/site.py       links and data credit for this app
build_data.py     offline: raw CSVs -> data/*.parquet + data/meta.json
data/             ~0.3 MB of prepared tables (shipped with the app)
Dockerfile        container image (port 7860), for hosts that run Docker
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

To rebuild the data after changing the analysis:

```bash
python build_data.py "path/to/Megaline Analysis"   # folder with the five megaline_*.csv files
```

## Data

Megaline is a fictional operator; the dataset is a training dataset of 500 anonymised customers.
Customer names are not used.
