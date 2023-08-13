#TODO This whole file needs refactored
import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

plt.style.use("seaborn-v0_8-whitegrid")
from datetime import datetime

import plotly.express as px
import plotly.graph_objects as go
import requests

urls = {
    "tmax": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/tmax.txt",
    "tmin": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/tmin.txt",
    "tmean": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/tmean.txt",
    "sunshine": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/sunshine.txt",
    "rainfall": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/rainfall.txt",
}


def grab_url_text_data(
    input_url: str,
) -> str:
    """

    Args:
        url (str): url to grab text data from, should direct to a .txt html
        e.g "http://www.gutenberg.org/files/11/11-0.txt"
        save_text_dir (Union[Path, str]): directory to save text data in .

    Returns:
    """
    r = requests.get(input_url)
    file_like_obj = io.StringIO(r.text)
    lines = file_like_obj.readlines()
    return lines


current_month = datetime.today().month
current_year = datetime.today().year
month_mapping = {
    1: "jan",
    2: "feb",
    3: "mar",
    4: "apr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "aug",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dec",
}
months = list(month_mapping.values())
current_month_name = month_mapping[current_month]
months_to_overwrite = []
for i in range(current_month, 13):
    months_to_overwrite.append(month_mapping[i])


fnames = ["tmax", "tmin", "tmean", "sunshine", "rainfall"]
titles = ["Max Temp", "Min Temp", "Mean Temp", "Sunshine", "Rainfall"]
raw_data_dict = {}
for fname, url in zip(fnames, urls.values()):
    data = grab_url_text_data(url)[5:]
    raw_data_dict[fname] = data


dfs = []
for name, data in raw_data_dict.items():
    lst_lsts = []
    for i in range(len(data)):
        _temp = data[i].split(" ")
        lst_lsts.append([i for i in _temp if i])
    df = pd.DataFrame(lst_lsts)
    dfs.append(df)
dfs_dict = dict(zip(titles, dfs))


def clean_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    raw_df.columns = raw_df.iloc[0]
    df = raw_df[1:]
    df = df.replace(to_replace=["---", "\n", None], value=np.nan)
    df["ann"] = df["ann\n"].str.replace("\n", "")
    df = df.drop("ann\n", axis=1, errors="ignore")
    df = df.apply(pd.to_numeric)
    df = df.drop(["win", "spr", "sum", "aut", "ann"], axis=1, errors="ignore")
    return df


dfs_dict = {k: clean_df(v) for k, v in dfs_dict.items()}


def overwrite_months_to_come(df: pd.DataFrame) -> pd.DataFrame:
    # overwriting months not yet occured
    months_to_overwrite = []
    for i in range(current_month, 13):
        months_to_overwrite.append(month_mapping[i])
    for month in months_to_overwrite:
        df.loc[df["year"] == current_year, month] = np.nan
    return df


dfs_dict = {k: overwrite_months_to_come(v) for k, v in dfs_dict.items()}
months = dfs_dict["Rainfall"].drop("year", axis=1).columns.to_list()


def generate_deciles(df: pd.DataFrame) -> pd.DataFrame:
    decile_0 = df[months].min()
    decile_10 = df[months].quantile(0.1)
    decile_50 = df[months].quantile(0.5)
    decile_90 = df[months].quantile(0.9)
    decile_100 = df[months].max()
    df_deciles = pd.concat(
        [decile_0, decile_10, decile_50, decile_90, decile_100], axis=1
    )
    df_deciles = df_deciles.rename_axis("month")
    return df_deciles


dfs_deciles_dict = {k: generate_deciles(v) for k, v in dfs_dict.items()}
dfs_2023_dict = {}
for k, v in dfs_dict.items():
    df_2023 = v[v["year"] == 2023].drop("year", axis=1)
    dfs_2023_dict[k] = df_2023


def point_style(val, month, deciles_df):
    _min = deciles_df[deciles_df.index == month][0.0].values[0]
    _0_1 = deciles_df[deciles_df.index == month][0.1].values[0]
    _0_5 = deciles_df[deciles_df.index == month][0.5].values[0]
    _0_9 = deciles_df[deciles_df.index == month][0.9].values[0]
    _max = deciles_df[deciles_df.index == month][1.0].values[0]
    if _min <= val <= _0_1:
        return "^"
    elif _0_1 <= val <= _0_5:
        return "h"
    elif _0_5 <= val <= _0_9:
        return "o"
    elif _0_9 <= val <= _max:
        return "D"
    else:
        return np.nan


pd_keys = [val for val in list(dfs_deciles_dict.keys()) for _ in range(12)]
month_keys = months * 5
long_df = pd.concat(dfs_deciles_dict.values(), ignore_index=True)
long_df["type"] = pd_keys
long_df["month"] = month_keys
long_df = long_df.melt(id_vars=["type", "month"])
long_df = long_df.rename(columns={"variable": "decile"})
dfs_2023_dict = {k: v.T for k, v in dfs_2023_dict.items()}
dfs_2023_dict = {
    k: v.rename(columns={v.columns[0]: "value"}) for k, v in dfs_2023_dict.items()
}
for key, df in dfs_2023_dict.items():
    deciles_df = dfs_deciles_dict[key]
    df["month"] = df.index
    df["marker"] = df.apply(
        lambda x: point_style(x["value"], x["month"], deciles_df), axis=1
    )
units_map = {
    "Rainfall": "mm",
    "Sunshine": "hrs",
    "Max Temp": "Temp (C)",
    "Mean Temp": "Temp (C)",
    "Min Temp": "Temp (C)",
}

fig_data = {}

for key in list(dfs_2023_dict.keys()):
    unit = units_map[key]
    df_2023 = dfs_2023_dict[key]
    df = long_df[long_df["type"] == key]
    lines = px.line(
        df,
        x="month",
        y="value",
        title=key,
        color="decile",
        color_discrete_sequence=[
            "firebrick",
            "firebrick",
            "grey",
            "seagreen",
            "seagreen",
        ],
        line_dash="decile",
        line_dash_sequence=["solid", "dash", "solid", "dash", "solid"],
        line_shape="spline",  # or 'linear')
    )
    scatter = px.scatter(
        df_2023, x="month", y="value", symbol="marker", hover_data=["month", "value"]
    )
    scatter.update_traces(
        marker=dict(size=10, line=dict(width=2, color="DarkSlateGrey")),
        selector=dict(mode="markers"),
    )
    fig = go.Figure(data=lines.data + scatter.data)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title=unit, title=key)
    fig_data[key] = fig
    # fig.show()


st.title("UK Monthly Weather Data")
st.header("About")
st.markdown(r"""Some charts of UK weather data. The average max temperature, 
            min temperature, mean temperature, sunshine hours and rainfall mm 
            for the UK is provided. The mean and 90% deciles are plotted, along with 
            min/mas values. Values for the current year provided as markers, with marker
            shape aligned to which decile the value lies within.  
            Inspiration for this is taken from Nigel Marriot's blog and the original
            data is provided by the met office.\
            The charts will update monthly as new data is provided.\
            You can read more about how I made this on my website. """)
st.plotly_chart(fig_data["Rainfall"])
st.plotly_chart(fig_data["Sunshine"])
st.plotly_chart(fig_data["Max Temp"])
st.plotly_chart(fig_data["Mean Temp"])
st.plotly_chart(fig_data["Min Temp"])
