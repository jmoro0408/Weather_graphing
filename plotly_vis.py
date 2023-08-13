import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.style.use("seaborn-v0_8-whitegrid")
from datetime import datetime

import plotly.express as px
import plotly.graph_objects as go

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

LOAD_DIR = Path(Path.cwd(), "data")
fnames = ["rainfall.txt", "sunshine.txt", "tmax.txt", "tmean.txt", "tmin.txt"]
titles = ["Rainfall", "Sunshine", "Max Temp", "Mean Temp", "Min Temp"]
raw_data_dict = {}
for fname in fnames:
    with open(Path(LOAD_DIR, fname)) as f:
        data = f.readlines()[5:]
    raw_data_dict[fname[:-4]] = data

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
SAVE_HTML_DIR = Path(Path.cwd(), "visuals", "html")
SAVE_PICKLE_DIR = Path(Path.cwd(), "visuals", "chart_data")
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
    fig.write_html(Path(SAVE_HTML_DIR, f"{key}.html"))
    with open(Path(SAVE_PICKLE_DIR, f"{key}.pkl"), "wb") as handle:
        pickle.dump(fig, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # fig.show()
