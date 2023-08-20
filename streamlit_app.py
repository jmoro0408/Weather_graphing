# pylint: disable=invalid-name
import io
from datetime import datetime
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

plt.style.use("seaborn-v0_8-whitegrid")

CURRENT_MONTH = datetime.today().month
CURRENT_YEAR = datetime.today().year
MONTH_MAPPING = {
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
    response = requests.get(input_url, timeout=5.0)
    file_like_obj = io.StringIO(response.text)
    return file_like_obj.readlines()


def clean_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess a raw DataFrame.

    This function takes a raw DataFrame, performs cleaning and preprocessing operations,
    and returns a cleaned Pandas DataFrame. Cleaning includes removing unnecessary rows,
    converting text values to numeric, and organizing the data for analysis.

    Args:
        raw_df (pd.DataFrame): The raw DataFrame. Assumed

    Returns:
        pd.DataFrame: A cleaned and processed DataFrame ready for analysis.
    """
    raw_df.columns = raw_df.iloc[0]
    df = raw_df[1:]
    df = df.replace(to_replace=["---", "\n", None], value=np.nan)
    df["ann"] = df["ann\n"].str.replace("\n", "")
    df = (
        df.drop("ann\n", axis=1, errors="ignore")
        .apply(pd.to_numeric)
        .drop(["win", "spr", "sum", "aut", "ann"], axis=1, errors="ignore")
    )
    return df


def overwrite_months_to_come(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Overwrite data for upcoming months with NaN values.

    This function takes a DataFrame containing time-series data and overwrites the values for
    months that have not yet occurred (upcoming months) with NaN values.
    Args:
        df (pd.DataFrame): The DataFrame containing time-series data with 'year' and month columns.

    Returns:
        pd.DataFrame: The DataFrame with values for upcoming months overwritten as NaN.
    """
    # overwriting months not yet occurred
    months_to_overwrite = []
    for i in range(CURRENT_MONTH, 13):
        months_to_overwrite.append(MONTH_MAPPING[i])
    for month in months_to_overwrite:
        df.loc[df["year"] == CURRENT_YEAR, month] = np.nan
    return df


def generate_dfs_dict(
    fnames: list[str], urls: dict[str, str], titles: list[str]
) -> dict[str, pd.DataFrame]:
    """Generate a dictionary of DataFrames from raw text data fetched from URLs.

    This function fetches raw text data from URLs specified in the provided dictionary,
    processes the data, and generates a dictionary of Pandas DataFrames. The processing
    includes cleaning, formatting, and overwriting future months' data.

    Args:
        fnames (list[str]): List of names to associate with the generated DataFrames.
        urls (dict[str, str]): Dictionary mapping names to URLs for raw text data.

    Returns:
        dict[str, pd.DataFrame]: A dictionary where keys are names and values are processed Pandas DataFrames.

    Note:
        This function assumes that the `grab_url_text_data`, `clean_df`, and `overwrite_months_to_come` functions are defined elsewhere.
    """
    raw_data_dict = {}
    for fname, url in zip(fnames, urls.values()):
        data = grab_url_text_data(url)[5:]
        raw_data_dict[fname] = data

    dfs = []
    for data in raw_data_dict.values():
        lst_lsts = []
        for i in data:
            _temp = i.split(" ")
            lst_lsts.append([x for x in _temp if x])
        dfs.append(pd.DataFrame(lst_lsts))

    dfs_dict = dict(zip(titles, dfs))
    dfs_dict = {k: clean_df(v) for k, v in dfs_dict.items()}
    dfs_dict = {k: overwrite_months_to_come(v) for k, v in dfs_dict.items()}

    return dfs_dict


def generate_deciles(df: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    """Generate a DataFrame of deciles for specified months.

    This function calculates the deciles (10th, 50th, and 90th percentiles) along with the minimum and maximum
    values for the specified months' data in the given DataFrame. It creates a new DataFrame containing the calculated
    decile values for each specified month.

    Args:
        df (pd.DataFrame): The DataFrame containing the data for analysis.

    Returns:
        pd.DataFrame: A DataFrame containing calculated decile values for specified months.

    """
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


def point_style(val: float, month: str, deciles_df: pd.DataFrame) -> Union[str, np.nan]:
    """Determine the point style based on the value, month, and deciles.

    This function assigns a specific point style based on the given value, corresponding month,
    and the calculated deciles DataFrame. Different point styles are used to represent different
    ranges of values for visualization or analysis purposes.

    Args:
        val: The value for which the point style is to be determined.
        month: The month for which the value is associated.
        deciles_df: A DataFrame containing calculated decile values for different months.

    Returns:
        str or np.nan: A point style character ('^', 'h', 'o', 'D') or np.nan if not within any range.
    """
    _min = deciles_df[deciles_df.index == month][0.0].values[0]
    _0_1 = deciles_df[deciles_df.index == month][0.1].values[0]
    _0_5 = deciles_df[deciles_df.index == month][0.5].values[0]
    _0_9 = deciles_df[deciles_df.index == month][0.9].values[0]
    _max = deciles_df[deciles_df.index == month][1.0].values[0]

    if _min <= val <= _0_1:
        return "^"
    if _0_1 <= val <= _0_5:
        return "h"
    if _0_5 <= val <= _0_9:
        return "o"
    if _0_9 <= val <= _max:
        return "D"

    return np.nan


def create_long_df(deciles_dict: dict[pd.DataFrame], months: list) -> pd.DataFrame:
    """Create a long-format DataFrame from a dictionary of deciles DataFrames.

    This function takes a dictionary of deciles DataFrames, concatenates them, and transforms the data into
    a long-format DataFrame suitable for analysis and visualization. The resulting DataFrame contains
    'type', 'month', 'decile', and decile values as columns.

    Args:
        deciles_dict (dict[pd.DataFrame]): A dictionary of deciles DataFrames.

    Returns:
        pd.DataFrame: A long-format DataFrame containing 'type', 'month', 'decile', and decile values.
    """
    pd_keys = [val for val in list(deciles_dict.keys()) for _ in range(12)]
    month_keys = months * 5
    long_df = pd.concat(deciles_dict.values(), ignore_index=True)
    long_df["type"] = pd_keys
    long_df["month"] = month_keys
    long_df = long_df.melt(id_vars=["type", "month"]).rename(
        columns={"variable": "decile"}
    )
    return long_df


def calculate_marker(row: pd.Series, deciles_df: pd.DataFrame) -> Union[str, np.nan]:
    """Calculate and return a marker style based on row values and deciles DataFrame.

    This function calculates a marker style for a specific row based on its 'value' and 'month'
    columns and the provided deciles DataFrame. The calculated marker style is returned.

    Args:
        row (pd.Series): A Pandas Series representing a row of data with 'value' and 'month' columns.
        deciles_df (pd.DataFrame): A DataFrame containing decile values for different months.

    Returns:
        Union[str, np.nan]: A marker style character ('^', 'h', 'o', 'D') or np.nan if not within any range.
    """
    return point_style(row["value"], row["month"], deciles_df)


def main():
    urls = {
        "tmax": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/tmax.txt",
        "tmin": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/tmin.txt",
        "tmean": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/tmean.txt",
        "sunshine": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/sunshine.txt",
        "rainfall": r"https://weather-bucket-jmoro0408.s3.eu-north-1.amazonaws.com/rainfall.txt",
    }

    months = list(MONTH_MAPPING.values())

    titles = ["Max Temp", "Min Temp", "Mean Temp", "Sunshine", "Rainfall"]

    fnames = ["tmax", "tmin", "tmean", "sunshine", "rainfall"]
    dfs_dict = generate_dfs_dict(fnames=fnames, urls=urls, titles=titles)

    dfs_deciles_dict = {k: generate_deciles(v, months) for k, v in dfs_dict.items()}
    current_year_dict = {}
    for k, v in dfs_dict.items():
        df_current_year = v[v["year"] == CURRENT_YEAR].drop("year", axis=1)
        current_year_dict[k] = df_current_year

    long_df = create_long_df(dfs_deciles_dict, months=months)
    current_year_dict = {k: v.T for k, v in current_year_dict.items()}
    current_year_dict = {
        k: v.rename(columns={v.columns[0]: "value"})
        for k, v in current_year_dict.items()
    }
    for key, df in current_year_dict.items():
        deciles_df = dfs_deciles_dict[key]
        df["month"] = df.index
        df["marker"] = df.apply(calculate_marker, deciles_df=deciles_df, axis=1)

    units_map = {
        "Rainfall": "mm",
        "Sunshine": "hrs",
        "Max Temp": "Temp (C)",
        "Mean Temp": "Temp (C)",
        "Min Temp": "Temp (C)",
    }

    fig_data = {}

    for key in list(current_year_dict.keys()):
        unit = units_map[key]
        df_current_year = current_year_dict[key]
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
            df_current_year,
            x="month",
            y="value",
            symbol="marker",
            hover_data=["month", "value"],
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
    st.markdown(
        r"""Some charts of UK weather data. The average max temperature, 
                min temperature, mean temperature, sunshine hours and rainfall mm 
                for the UK is provided. The mean and 90% deciles are plotted, along with 
                min/max values. Values for the current year provided as markers, with marker
                shape aligned to which decile the value lies within.  
                Inspiration for this is taken from Nigel Marriot's blog and the original
                data is provided by the met office.\
                The charts will update monthly as new data is provided and you can read more about how I made this on my [website.](https://jmoro0408.github.io/project/weather-graphing-on-aws) \
                Depending on the data available, the starting dates range from \
                1836 (rainfall) to 1910 (sunshine) and the deciles are broken down as follows:\
                * 0th percentile (or the smallest value)\
                * 10th percentile (or the first decile) indicating the lowest 10% of observed values\
                * 50th percentile (or the median value) \
                * 90th percentile (or the ninth decile) indicating the highest 10% of observed values\
                * 100th percentile (or the largest value) 
                """
    )
    st.plotly_chart(fig_data["Rainfall"])
    st.plotly_chart(fig_data["Sunshine"])
    st.plotly_chart(fig_data["Max Temp"])
    st.plotly_chart(fig_data["Mean Temp"])
    st.plotly_chart(fig_data["Min Temp"])


if __name__ == "__main__":
    main()
