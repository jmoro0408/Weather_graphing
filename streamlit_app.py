import pickle
from pathlib import Path

import streamlit as st

st.title("UK Monthly Weather Data")

LOAD_DIR = Path(Path.cwd(), "visuals", "chart_data")
TMAX_DIR = Path(LOAD_DIR, "Max Temp.pkl")
TMEAN_DIR = Path(LOAD_DIR, "Mean Temp.pkl")
TMIN_DIR = Path(LOAD_DIR, "Min Temp.pkl")
RAINFALL_DIR = Path(LOAD_DIR, "Rainfall.pkl")
SUNSHINE_DIR = Path(LOAD_DIR, "Sunshine.pkl")


with open(TMAX_DIR, "rb") as f:
    tmax = pickle.load(f)
with open(TMEAN_DIR, "rb") as f:
    tmin = pickle.load(f)
with open(TMEAN_DIR, "rb") as f:
    tmean = pickle.load(f)
with open(RAINFALL_DIR, "rb") as f:
    rainfall = pickle.load(f)
with open(SUNSHINE_DIR, "rb") as f:
    sunshine = pickle.load(f)


st.plotly_chart(rainfall)
st.plotly_chart(sunshine)
st.plotly_chart(tmax)
st.plotly_chart(tmin)
st.plotly_chart(tmean)
