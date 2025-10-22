#%%
# 國際商品指數 
#%%

import requests
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import io
import os
import json
import pandas as pd
import numpy as np
import datetime, time, random
from datetime import datetime
import random
import sqlite3
import unicodedata
import json
import yfinance as yf
import tempfile
import streamlit as st
import plotly.figure_factory as ff
import plotly.graph_objects as go
import plotly.express as px
from backtesting import Backtest, Strategy
from scipy.optimize import curve_fit
from scipy.stats import linregress
import datetime
from datetime import datetime, timedelta
from plotly.subplots import make_subplots



#%%
# Streamlit 讀取 index+etf+daily_price+pe_pb 整理
def download_sqlite_from_github(url):
    raw_url = url.replace(
        "github.com/06Cata/Taiwan_Stock/blob/main/",
        "raw.githubusercontent.com/06Cata/Taiwan_Stock/main/"
    )
    response = requests.get(raw_url)
    if response.status_code != 200:
        raise Exception(f"下載失敗，網址：{raw_url}")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
    temp_file.write(response.content)
    temp_file.close()
    return temp_file.name


def _read_and_concat_sqlite_tables_material():
    urls = [
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_material_unrated.sqlite3",
    ]
    table_names = [
        "merged_material_unrated",
    ]
    dfs = []
    total = len(urls)
    progress_bar = st.progress(0, text="下載資料中...")

    for idx, (url, table_name) in enumerate(zip(urls, table_names), 1):
        st.write(f"第一次會較久，共 {total} 份，目前下載第 {idx} 份…")
        path = download_sqlite_from_github(url)
        conn = sqlite3.connect(path)
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        dfs.append(df)
        progress_bar.progress(idx / total, text=f"已下載第 {idx} 份，共 {total} 份")
    progress_bar.empty()  # 下載結束移除進度條
    df_concat = pd.concat(dfs, ignore_index=True)
    st.write('ok')
    return df_concat


def _read_and_concat_sqlite_tables_material_local():
    paths = [
        "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_material_unrated.sqlite3"
    ]
    table_names = [
        "merged_material_unrated"
    ]
    dfs = []
    for path, table_name in zip(paths, table_names):
        conn = sqlite3.connect(path)
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        dfs.append(df)
    df_concat = pd.concat(dfs, ignore_index=True)
    return df_concat


#%%
# Streamlit 快取全量資料（全程只抓一次）
@st.cache_data(show_spinner="載入資料中…", persist=True)
def read_and_concat_sqlite_tables():
    return _read_and_concat_sqlite_tables_material_local()


# %%
# 日期區間快取（根據滑桿/股票篩資料）
@st.cache_data(show_spinner=False)
def read_merged_df_2(daily_df_merge_index_pepb, date_range):
    date_dict = {
    '3年': 1095,
    '2年6個月': 913,
    '2年': 730,
    '1年6個月': 548,
    '1年': 365,
    '6個月': 183,
    '3個月': 92,
    '2個月': 61,
    '1個月': 31
    }
    days = date_dict.get(date_range, 730)
    today = datetime.now()
    date = (today - timedelta(days=days)).strftime('%Y%m%d')
    df = daily_df_merge_index_pepb.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Date'] >= pd.to_datetime(date)]
    df = df.sort_values(by='Date')
    return df


# ===================== plotly =====================


# 商品（特別是BCI、黃金、能源農產品）大漲期，通常是通膨壓力上升、經濟轉向時期
# 商品指數大漲時，適合考慮分散到「抗通膨資產」
# 商品全線上揚，可能在景氣通膨週期高峰，要小心高點回檔
# 商品跌、只剩金銀逆勢，可能是避險時刻

# 如果**商品和美股同時大跌，才是真正「景氣衰退危機」**警訊
# 若商品漲＋美股漲，通常是景氣復甦（或市場極度樂觀）
# 只有商品漲、股市不動/漲不動，代表企業獲利開始受壓，未來有回調風險

from plotly.subplots import make_subplots

#%%
# 國際商品指數
def plotly_material(data):
    # ====== 資料前處理：確保 index 與 dtype 正確 ======
    # 1. 如有 'Date' 欄位，設為 index 並轉型
    if 'Date' in data.columns:
        data = data.copy()
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.set_index('Date').sort_index()

    # 2. 所有必要欄位（如果有物件型態，全部轉成 float）
    for col in data.columns:
        if data[col].dtype == "O":
            data[col] = pd.to_numeric(data[col], errors='coerce')
    
    # ====== 指標中文名稱對應 ======
    names = {
        "BCI":   "BCI（彭博商品指數代理 / Bloomberg Commodity ETF）",
        "GSG":   "GSG（標普GSCI代理 / S&P GSCI ETF）",
        "CL=F":  "WTI 原油期貨 / WTI Crude Oil Futures",
        "GC=F":  "黃金期貨 / Gold Futures",
        "SI=F":  "白銀期貨 / Silver Futures",
        "HG=F":  "銅期貨 / Copper Futures",
        "ZC=F":  "玉米期貨 / Corn Futures",
        "ZS=F":  "大豆期貨 / Soybean Futures",
        "ZW=F":  "小麥期貨 / Wheat Futures",
        "NG=F":  "天然氣期貨 / Natural Gas Futures",
        "^GSPC": "標普500指數 / S&P 500 Index",
        "SPY": "SPY（SPDR 標普500 ETF / S&P 500 ETF）",
        "VOO": "VOO（Vanguard 標普500 ETF / S&P 500 ETF）",
        "QQQ":  "QQQ（納指100 ETF）/ Nasdaq 100 ETF",
        "VTI":  "VTI（美國全市場 ETF）/ Total US Market ETF",
        "^IRX": "2年美國公債殖利率 / 2Y US Treasury Yield",
        "^FVX": "5年美國公債殖利率 / 5Y US Treasury Yield",
        "^TNX": "10年美國公債殖利率 / 10Y US Treasury Yield",
        "^TWII" : "台灣加權指數 / TAIEX",
        "^IXIC": "納斯達克指數 / Nasdaq Composite",
        "^N225": "日經225指數 / Nikkei 225",
        "^GDAXI": "德國DAX指數 / DAX 40",
    }

    # ===== 圖1：大宗商品9大指標標準化對照 =====
    cols1 = ["BCI", "GSG", "CL=F","GC=F", "SI=F", "HG=F", "ZC=F", "ZS=F", "ZW=F"] 
    norm = data[cols1].dropna().copy()
    norm = norm / norm.iloc[0] * 100

    fig = go.Figure()
    for c in cols1:
        if c in norm.columns:
            fig.add_trace(go.Scatter(
                x=norm.index, y=norm[c],
                mode="lines", name=names.get(c, c), line=dict(width=1.0)
            ))
    fig.update_layout(
        title="BCI / GSG / 期貨 | Normalized to 100",
        xaxis_title="日期 / Date",
        yaxis_title="指數（起點=100） / Index (Base=100)",
        legend_title="",
        hovermode="x unified",
        width=1000, height=550,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
    )
)

    # ===== 圖2：各國股市 vs 美債殖利率 =====
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    # 指數
    for col, color in zip(["^GSPC", "^IXIC", "^TWII", "^N225", "^GDAXI"], ['red', None, None, None, None]):
        if col in data.columns:
            fig2.add_trace(
                go.Scatter(x=data.index, y=data[col], name=names.get(col, col), mode="lines", line=dict(width=1.0, color=color) if color else dict(width=1.0)),
                secondary_y=False,
            )
    # 美債殖利率
    for col in ["^IRX", "^FVX", "^TNX"]:
        if col in data.columns:
            fig2.add_trace(
                go.Scatter(x=data.index, y=data[col], name=names.get(col, col), mode="lines", line=dict(width=1.0)),
                secondary_y=True,
            )
    fig2.update_layout(
        title="各國指數 vs 美債殖利率 US 2/5/10Y Yield",
        hovermode="x unified",
        legend_title="",
        width=1000, height=550,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
    )
)
    
    fig2.update_xaxes(title_text="日期 / Date")
    fig2.update_yaxes(title_text="各國指數", secondary_y=False)
    fig2.update_yaxes(title_text="美債殖利率 US 2/5/10Y Yield", secondary_y=True)

    # ===== 圖2_2：SPY/VOO/QQQ/VTI =====
    fig2_2 = make_subplots(specs=[[{"secondary_y": True}]])
    for col, color in zip(["SPY", "VOO", "QQQ", "VTI"], ['red', 'orange', 'purple', 'green']):
        if col in data.columns:
            fig2_2.add_trace(
                go.Scatter(x=data.index, y=data[col], name=names.get(col, col), mode="lines", line=dict(width=1.0, color=color)),
                secondary_y=False,
            )
    fig2_2.update_layout(
        title="SPY / VOO / QQQ / VTI",
        hovermode="x unified",
        legend_title="",
        width=1000, height=350,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
    )
)
    
    fig2_2.update_xaxes(title_text="日期 / Date")

    # ===== 圖3：BCI vs S&P/US10Y 90日滾動相關 =====
    key_cols = ["BCI", "^GSPC", "^TNX", "CL=F"]
    for col in key_cols:
        if col not in data.columns:
            print(f"缺少欄位：{col}，圖三無法計算完整！")
    data_key = data[[col for col in key_cols if col in data.columns]].dropna(how="any")
    ret = data_key.pct_change().dropna()
    roll = 90
    fig3 = go.Figure()
    if "BCI" in ret.columns and "^GSPC" in ret.columns:
        corr_spx   = ret["BCI"].rolling(roll).corr(ret["^GSPC"])
        fig3.add_trace(go.Scatter(x=corr_spx.index, y=corr_spx, mode="lines",
                            name="相關(BCI, 標普500) - 90日 / Corr(BCI, S&P500) - 90D", line=dict(width=1.0)))
    if "BCI" in ret.columns and "^TNX" in ret.columns:
        corr_yield = ret["BCI"].rolling(roll).corr(ret["^TNX"])
        fig3.add_trace(go.Scatter(x=corr_yield.index, y=corr_yield, mode="lines",
                            name="相關(BCI, 美債10年殖利率) - 90日 / Corr(BCI, US10Y) - 90D", line=dict(width=1.0)))
    fig3.add_hline(y=0, line_dash="dash")
    fig3.update_layout(
        title="BCI 與 股市/利率 的90日滾動相關 | 90D Rolling Correlation",
        xaxis_title="日期 / Date",
        yaxis_title="相關係數 / Correlation",
        legend_title="",
        hovermode="x unified",
        width=1000, height=350,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
    )
)

    # ===== Summary 區間相關 =====
    summary = pd.DataFrame({
        "相關(BCI, 標普500) / Corr(BCI, S&P500)": [ret["BCI"].corr(ret["^GSPC"])] if ("BCI" in ret and "^GSPC" in ret) else [None],
        "相關(BCI, 10年殖利率) / Corr(BCI, US10Y%)": [ret["BCI"].corr(ret["^TNX"])] if ("BCI" in ret and "^TNX" in ret) else [None],
        "相關(WTI, 標普500) / Corr(WTI, S&P500)": [ret["CL=F"].corr(ret["^GSPC"])] if ("CL=F" in ret and "^GSPC" in ret) else [None],
        "相關(WTI, 10年殖利率) / Corr(WTI, US10Y%)": [ret["CL=F"].corr(ret["^TNX"])] if ("CL=F" in ret and "^TNX" in ret) else [None],
    }).round(3)

    return fig, fig2, fig2_2, fig3, summary


# fig, fig2, fig2_2, fig3, summary = plotly_material(merged_material_unrated_df)
# fig.show() 
# fig2.show()
# fig2_2.show()
# fig3.show()
# display(summary)


#%%
# 失業率對比
def unrated(data):
    # 如果不是 DatetimeIndex，就轉
    if not pd.api.types.is_datetime64_any_dtype(data.index):
        if 'Date' in data.columns:
            data = data.copy()
            data['Date'] = pd.to_datetime(data['Date'])
            data = data.set_index('Date')
        else:
            raise Exception('DataFrame 必須有 Date 欄位或 DatetimeIndex')

    df = data[['^GSPC', 'UNRATE']].copy()
    df_month = df.resample('M').last()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_month.index, y=df_month['UNRATE'],
        name='美國失業率', yaxis='y1',
        mode='lines+markers', line=dict(color='blue', width=1.4)
    ))
    fig.add_trace(go.Scatter(
        x=df_month.index, y=df_month['^GSPC'],
        name='S&P500', yaxis='y2',
        mode='lines', line=dict(color='red', width=1.4)
    ))

    fig.update_layout(
        title='美國失業率 vs S&P500 指數（月資料）',
        xaxis_title='日期',
        yaxis=dict(
            title='失業率 (%)',
            titlefont=dict(color='black'),
            tickfont=dict(color='black'),
            side='left'
        ),
        yaxis2=dict(
            title='S&P500指數',
            titlefont=dict(color='black'),
            tickfont=dict(color='black'),
            overlaying='y',
            side='right'
        ),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    return fig


# fig = unrated(merged_material_unrated_df)
# fig.show()