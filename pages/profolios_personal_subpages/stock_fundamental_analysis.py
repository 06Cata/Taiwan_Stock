#%%
# 基本面_財報分析 
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
# import yfinance as yf
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


#%% 
# swagger industry
def get_stock_code_industry_all_swagger(stock_id):
    df_to_json = requests.get(f"https://stockinfo.zeabur.app/industry/{stock_id}").json()
    stock_id = df_to_json['stock_id']
    stock_name = df_to_json['stock_name']
    cm_otc = df_to_json['cm_otc']
    stock_industry = df_to_json['stock_industry']
    related_data = df_to_json['related_data']
    return stock_id, stock_name, cm_otc, stock_industry, related_data


#%% 
# swagger company info
def get_company_info_all_swagger(stock_id):
    df_to_json = requests.get(f"https://stockinfo.zeabur.app/company-info/{stock_id}").json()
    stock_id= df_to_json['stock_id']
    stock_name = df_to_json['stock_name']
    cm_otc = df_to_json['cm_otc']
    stock_cm_otc_date = df_to_json['stock_cm_otc_date']
    stock_industry = df_to_json['stock_industry']
    stock_address = df_to_json['stock_address']
    stock_business = df_to_json['stock_business']
    stock_amount = df_to_json['stock_amount']
    stock_common_price = df_to_json['stock_common_price']
    stock_amount_common = df_to_json['stock_amount_common']
    stock_amount_special = df_to_json['stock_amount_special']
    related_data = df_to_json['related_data']
    return (
        stock_id, stock_name, cm_otc, stock_cm_otc_date,
        stock_industry, None, stock_address,  # stock_industry_sub暫留None
        stock_business, stock_amount, stock_common_price,
        stock_amount_common, stock_amount_special, related_data
    )


#%%
# 
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


def _read_and_concat_sqlite_tables_funda():
    urls = [
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_bs_ci_cfs.sqlite3",
    ]
    table_names = [
        "bs_ci_cfs",
    ]
    dfs = []
    total = len(urls)
    progress_bar = st.progress(0, text="下載資料中...")

    for idx, (url, table_name) in enumerate(zip(urls, table_names), 1):
        st.write(f"第一次會較久，共 {total+1} 份，目前下載第 {idx} 份…")
        path = download_sqlite_from_github(url)
        conn = sqlite3.connect(path)
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        dfs.append(df)
        progress_bar.progress(idx / total, text=f"已下載第 {idx} 份，共 {total} 份")
    progress_bar.empty()  # 下載結束移除進度條
    df_concat = pd.concat(dfs, ignore_index=True)
    df_concat = df_concat.sort_values(by=['股票代號', '季度排序'])
    return df_concat


def _read_and_concat_sqlite_tables_monthly_eps():
    urls = [
        "https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/merged_monthly_eps.sqlite3"
        ]
    table_names = [
        "merged_monthly_eps"
    ]
    dfs = []
    total = len(urls)
    progress_bar = st.progress(0, text="下載資料中...")

    for idx, (url, table_name) in enumerate(zip(urls, table_names), 1):
        st.write(f"第一次會較久，共 {total+1} 份，目前下載第 {idx+1} 份…")
        path = download_sqlite_from_github(url)
        conn = sqlite3.connect(path)
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        dfs.append(df)
        progress_bar.progress(idx / total, text=f"已下載第 {idx} 份，共 {total} 份")
    progress_bar.empty()  # 下載結束移除進度條
    df_monthly_eps = pd.concat(dfs, ignore_index=True)
    df_monthly_eps = df_monthly_eps.sort_values(by=['股票代號', '季度排序'])
    st.write('ok')
    return df_monthly_eps


def _read_and_concat_sqlite_tables_funda_local():
    paths = [
        "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_bs_ci_cfs.sqlite3"
    ]
    table_names = [
        "bs_ci_cfs",
    ]
    dfs = []
    for path, table_name in zip(paths, table_names):
        conn = sqlite3.connect(path)
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        dfs.append(df)
    df_concat = pd.concat(dfs, ignore_index=True)
    return df_concat



def _read_and_concat_sqlite_tables_monthly_eps_local():
    paths = [
        "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_monthly_eps.sqlite3",
    ]
    table_names = [
        "merged_monthly_eps",
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
    return _read_and_concat_sqlite_tables_funda_local()


@st.cache_data(show_spinner="載入資料中…", persist=True)
def read_and_concat_sqlite_tables_monthly_eps():
    return _read_and_concat_sqlite_tables_monthly_eps_local()


# %%
# # 日期區間快取（根據滑桿/股票篩資料）
# @st.cache_data(show_spinner=False)
# def read_merged_df_2(daily_df_merge_index_pepb, stock_id, date_range):
#     date_dict = {
#     '3年': 1095,
#     '2年6個月': 913,
#     '2年': 730,
#     '1年6個月': 548,
#     '1年': 365,
#     '6個月': 183,
#     '3個月': 92,
#     '2個月': 61,
#     '1個月': 31
#     }
#     days = date_dict.get(date_range, 730)
#     today = datetime.now()
#     date = (today - timedelta(days=days)).strftime('%Y%m%d')
#     df = daily_df_merge_index_pepb.copy()
#     df['Date'] = pd.to_datetime(df['Date'])
#     df = df[df['Date'] >= pd.to_datetime(date)]
#     df = df[df['股票代號'] == stock_id].sort_values(by='Date')
#     return df


# ===================== plotly =====================

#%%
# 011 包成def
# ocf icf fcf


def plotly_ocf_icf_fcf(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準營業活動現金流', '標準營業活動現金流_同業平均', '標準營業活動現金流_近四季平均', '標準營業活動現金流_近四季同業平均',
        '標準投資活動現金流', '標準投資活動現金流_同業平均', '標準投資活動現金流_近四季平均', '標準投資活動現金流_近四季同業平均',
        '標準籌資活動現金流', '標準籌資活動現金流_同業平均', '標準籌資活動現金流_近四季平均', '標準籌資活動現金流_近四季同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[(df_bs_ci_cfs['產業類別提取'] == stock_industry)].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['標準營業活動現金流_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        late4_ocf = f"{last['標準營業活動現金流_近四季同業平均'] / 1e8:.2f}億"
        late4_icf = f"{last['標準投資活動現金流_近四季同業平均'] / 1e8:.2f}億"
    else:
        late4_ocf = "無資料"
        late4_icf = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        return [ymin - 1e7, ymax + 1e7]

    y_range = _get_y_range(
        df_stock['標準營業活動現金流'], df_stock['標準投資活動現金流'], df_stock['標準籌資活動現金流'],
        df_industry['標準營業活動現金流_同業平均'],
        df_industry['標準投資活動現金流_同業平均'],
        df_industry['標準籌資活動現金流_同業平均'],
    )
    y_range2 = _get_y_range(
        df_stock['標準營業活動現金流_近四季平均'], df_stock['標準投資活動現金流_近四季平均'], df_stock['標準籌資活動現金流_近四季平均'],
        df_industry['標準營業活動現金流_近四季同業平均'],
        df_industry['標準投資活動現金流_近四季同業平均'],
        df_industry['標準籌資活動現金流_近四季同業平均'],
    )

    # === 7. 繪圖 ===
    # 圖1：單季
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準營業活動現金流'],
        mode='lines+markers', line=dict(color='red'),
        name='營業活動-個股',
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準營業活動現金流']],
        textposition='top center',
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準營業活動現金流_同業平均'],
        mode='lines+markers', line=dict(color='red', dash='dot'),
        name='營業活動-同業平均'
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準投資活動現金流'],
        mode='lines+markers', line=dict(color='mediumturquoise'),
        name='投資活動-個股',
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準投資活動現金流']],
        textposition='top center',
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準投資活動現金流_同業平均'],
        mode='lines+markers', line=dict(color='mediumturquoise', dash='dot'),
        name='投資活動-同業平均'
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準籌資活動現金流'],
        mode='lines+markers', line=dict(color='blue'),
        name='籌資活動-個股',
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準籌資活動現金流']],
        textposition='top center',
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準籌資活動現金流_同業平均'],
        mode='lines+markers', line=dict(color='blue', dash='dot'),
        name='籌資活動-同業平均'
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季現金流量",
        xaxis_title="年度-季度", yaxis_title="金額 (億)", yaxis=dict(range=y_range),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準營業活動現金流_近四季平均'],
        mode='lines+markers', line=dict(color='red'),
        name='營業活動-近四季平均-個股',
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準營業活動現金流_近四季平均']],
        textposition='top center',
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準營業活動現金流_近四季同業平均'],
        mode='lines+markers', line=dict(color='red', dash='dot'),
        name='營業活動-近四季平均-同業平均'
    ))
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準投資活動現金流_近四季平均'],
        mode='lines+markers', line=dict(color='mediumturquoise'),
        name='投資活動-近四季平均-個股',
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準投資活動現金流_近四季平均']],
        textposition='top center',
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準投資活動現金流_近四季同業平均'],
        mode='lines+markers', line=dict(color='mediumturquoise', dash='dot'),
        name='投資活動-近四季平均-同業平均'
    ))
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準籌資活動現金流_近四季平均'],
        mode='lines+markers', line=dict(color='blue'),
        name='籌資活動-近四季平均-個股',
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準籌資活動現金流_近四季平均']],
        textposition='top center',
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準籌資活動現金流_近四季同業平均'],
        mode='lines+markers', line=dict(color='blue', dash='dot'),
        name='籌資活動-近四季平均-同業平均'
    ))


    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均現金流量<br>\
同業近四季平均OCF {late4_ocf} 投資ICF {late4_icf}",
        xaxis_title="年度-季度", yaxis_title="金額 (億)", yaxis=dict(range=y_range2),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # === 8. 精簡 df ===
    df_cashflow = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準營業活動現金流', '標準營業活動現金流_同業平均', '標準營業活動現金流_近四季平均', '標準營業活動現金流_近四季同業平均',
        '標準投資活動現金流', '標準投資活動現金流_同業平均', '標準投資活動現金流_近四季平均', '標準投資活動現金流_近四季同業平均',
        '標準籌資活動現金流', '標準籌資活動現金流_同業平均', '標準籌資活動現金流_近四季平均', '標準籌資活動現金流_近四季同業平均'
    ]]

    return fig, fig2, df_cashflow

# fig, fig2, df_cashflow = plotly_ocf_icf_fcf(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_cashflow)


#%%
# 011-2 包成def
# ocf ni 比較 plotly_ocf_ni

def plotly_ocf_ni(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        # 圖一
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準營業活動現金流', '標準流動負債合計', '標準非流動資產合計',
        # 圖二
        '標準營業活動現金流_同業平均', '標準本期淨利淨損', '標準本期淨利淨損_同業平均', '獲利含金量%', '獲利含金量%_同業平均',
        # 圖三
        '標準營業活動現金流_近四季平均', '標準營業活動現金流_近四季同業平均',
        '標準本期淨利淨損_近四季平均', '標準本期淨利淨損_近四季同業平均',
        '獲利含金量%_近四季平均', '獲利含金量%_近四季同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['標準營業活動現金流_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        last_ocf = f"{last['標準營業活動現金流_同業平均'] / 1e8:.2f}億"
        last_ni = f"{last['標準本期淨利淨損_同業平均'] / 1e8:.2f}億"
        last_pct = f"{last['獲利含金量%_同業平均']:.2f}%"
        last4_ocf = f"{last['標準營業活動現金流_近四季同業平均'] / 1e8:.2f}億"
        last4_ni = f"{last['標準本期淨利淨損_近四季同業平均'] / 1e8:.2f}億"
        last4_pct = f"{last['獲利含金量%_近四季同業平均']:.2f}%"
    else:
        last_ocf = last_ni = last_pct = last4_ocf = last4_ni = last4_pct = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [0, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        gap = (ymax - ymin) * 0.2 if ymax > ymin else 1
        return [ymin - gap, ymax + gap]

    # === 7. 繪圖 ===
    # 圖1：單季
    y_range = _get_y_range(
        df_stock['標準營業活動現金流'],
        df_stock['標準流動負債合計'],
        df_stock['標準非流動資產合計']
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準營業活動現金流'],
        mode='lines+markers+text', line=dict(color='mediumturquoise', width=2.2),
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準營業活動現金流']],
        name='營業活動現金流'
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準流動負債合計'],
        mode='lines+markers+text', line=dict(color='tomato', width=2),
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準流動負債合計']],
        name='流動負債合計'
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準非流動資產合計'],
        mode='lines+markers+text', line=dict(color='deepskyblue', width=2),
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['標準非流動資產合計']],
        name='非流動資產合計'
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度現金流/負債/非流動資產",
        xaxis_title="年度-季度", yaxis_title="金額", yaxis=dict(range=y_range),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    # === 7. 繪圖 ===

    # 圖2：bar+折線圖 (折線OCF/NI在左、bar在右)
    y_range2 = _get_y_range(
        df_stock['標準營業活動現金流'],
        df_industry['標準營業活動現金流_同業平均'],
        df_stock['標準本期淨利淨損'],
        df_industry['標準本期淨利淨損_同業平均']
    )
    y_range2_bar = _get_y_range(
        df_stock['獲利含金量%'],
        df_industry['獲利含金量%_同業平均']
    )
    fig2 = go.Figure()
    
    # bar 含金量%
    fig2.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['獲利含金量%'],
        name='獲利含金量%-個股', marker=dict(color='mediumturquoise'), width=0.32, yaxis='y'
    ))
    fig2.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['獲利含金量%_同業平均'],
        name='獲利含金量%-同業平均', marker=dict(color='pink'), width=0.32, yaxis='y'
    ))
    
    # 折線 OCF
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準營業活動現金流'],
        mode='lines+markers+text', line=dict(color='red', width=2),
        text=[f"{v/1e8:.2f}" if not pd.isnull(v) else "" for v in df_stock['標準營業活動現金流']],
        name='OCF-個股', yaxis='y2'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準營業活動現金流_同業平均'],
        mode='lines+markers', line=dict(color='red', dash='dot', width=1.5),
        text=[f"{v/1e8:.2f}" if not pd.isnull(v) else "" for v in df_industry['標準營業活動現金流_同業平均']],
        name='OCF-同業平均', yaxis='y2'
    ))
    # 折線 NI
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準本期淨利淨損'],
        mode='lines+markers+text', line=dict(color='blue', width=2),
        text=[f"{v/1e8:.2f}" if not pd.isnull(v) else "" for v in df_stock['標準本期淨利淨損']],
        name='淨利-個股', yaxis='y2'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準本期淨利淨損_同業平均'],
        mode='lines+markers', line=dict(color='blue', dash='dot', width=1.5),
        text=[f"{v/1e8:.2f}" if not pd.isnull(v) else "" for v in df_industry['標準本期淨利淨損_同業平均']],
        name='淨利-同業平均', yaxis='y2'
    ))
    
    fig2.update_layout(
        title=f"...",
        xaxis_title="年度-季度",
        yaxis=dict(
            title="含金量%",
            range=y_range2_bar,
            side='left',
            showgrid=True
        ),
        yaxis2=dict(
            title="金額",
            range=y_range2,
            side='right',
            overlaying='y',
            showgrid=False
        ),
        barmode='group', width=900, height=450,
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.3,
            xanchor='center',
            x=0.5
        )
    )


    # 圖3：bar+折線圖近四季平均
    y_range3 = _get_y_range(
        df_stock['獲利含金量%_近四季平均'],
        df_industry['獲利含金量%_近四季同業平均'],
    )
    y_range3_y2 = _get_y_range(
        df_stock['標準營業活動現金流_近四季平均'],
        df_industry['標準營業活動現金流_近四季同業平均'],
        df_stock['標準本期淨利淨損_近四季平均'],
        df_industry['標準本期淨利淨損_近四季同業平均'],
    )

    fig3 = go.Figure()

    # Bar: 含金量%
    fig3.add_trace(go.Bar(
        x=df_stock['年度-季度'],
        y=df_stock['獲利含金量%_近四季平均'],
        name='含金量%-個股',
        marker=dict(color='mediumturquoise'),
        width=0.32,
        yaxis='y'
    ))
    fig3.add_trace(go.Bar(
        x=df_industry['年度-季度'],
        y=df_industry['獲利含金量%_近四季同業平均'],
        name='含金量%-同業平均',
        marker=dict(color='pink'),
        width=0.32,
        yaxis='y'
    ))

    # 折線: OCF
    fig3.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['標準營業活動現金流_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='red', width=2),
        text=[f"{v/1e8:.2f}" if not pd.isnull(v) else "" for v in df_stock['標準營業活動現金流_近四季平均']],
        name='OCF-個股',
        yaxis='y2'
    ))
    fig3.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['標準營業活動現金流_近四季同業平均'],
        mode='lines+markers',
        line=dict(color='red', dash='dot', width=1.5),
        text=[f"{v/1e8:.2f}" if not pd.isnull(v) else "" for v in df_industry['標準營業活動現金流_近四季同業平均']],
        name='OCF-同業平均',
        yaxis='y2'
    ))

    # 折線: 淨利
    fig3.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['標準本期淨利淨損_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='blue', width=2),
        text=[f"{v/1e8:.2f}" if not pd.isnull(v) else "" for v in df_stock['標準本期淨利淨損_近四季平均']],
        name='淨利-個股',
        yaxis='y2'
    ))
    fig3.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['標準本期淨利淨損_近四季同業平均'],
        mode='lines+markers',
        line=dict(color='blue', dash='dot', width=1.5),
        text=[f"{v/1e8:.2f}" if not pd.isnull(v) else "" for v in df_industry['標準本期淨利淨損_近四季同業平均']],
        name='淨利-同業平均',
        yaxis='y2'
    ))

    fig3.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均 含金量%/OCF/NI<br>\
同業最新近四季平均: 含金量{last4_pct}, OCF{last4_ocf}, NI{last4_ni}",
        xaxis_title="年度-季度",
        yaxis=dict(
            title="近四季平均含金量%",
            range=y_range3,
            side='left',
            showgrid=True
        ),
        yaxis2=dict(
            title="近四季平均金額",
            side='right',
            overlaying='y',
            showgrid=False,
            range=y_range3_y2
        ),
        barmode='group', width=900, height=450,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # === 8. 精簡 df ===
    df_ocf_ni = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準營業活動現金流', '標準營業活動現金流_同業平均', '標準營業活動現金流_近四季平均', '標準營業活動現金流_近四季同業平均',
        '標準本期淨利淨損', '標準本期淨利淨損_同業平均', '標準本期淨利淨損_近四季平均', '標準本期淨利淨損_近四季同業平均',
        '獲利含金量%', '獲利含金量%_同業平均', '獲利含金量%_近四季平均', '獲利含金量%_近四季同業平均'
    ]]
    

    return fig, fig2, fig3, df_ocf_ni


# fig, fig2, fig3, df_ocf_ni = plotly_ocf_ni(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# fig3.show()
# display(df_ocf_ni)


#%%
# 011-3 包成def
# 淨現金流量 net cash flow: ofc+icf+fci (直接反映一間公司錢是流出去多or流進來多)
# 自由現金流量 Free cash flow : ocf-icf (公司可以自由運用的現金
# 一間好公司自由現金流量應該要是正的，代表公司擴張，都能帶回營運的現金) 5/8要是正的
# 銀行業ok不用調

def plotly_net_free_cash_flow(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '淨現金流量(億)', '淨現金流量(億)_同業平均', '淨現金流量(億)_近四季平均', '淨現金流量(億)_近四季同業平均',
        '自由現金流量(億)', '自由現金流量(億)_同業平均', '自由現金流量(億)_近四季平均', '自由現金流量(億)_近四季同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')
    
    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()
    
    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')
    
    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['淨現金流量(億)_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )
    
    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        last_net = f"{last['淨現金流量(億)_同業平均']:.2f}億"
        last_free = f"{last['自由現金流量(億)_同業平均']:.2f}億"
        last4_net = f"{last['淨現金流量(億)_近四季同業平均']:.2f}億"
        last4_free = f"{last['自由現金流量(億)_近四季同業平均']:.2f}億"
    else:
        last_net = last_free = last4_net = last4_free = "無資料"
    
    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        gap = (ymax - ymin) * 1 if ymax > ymin else 1
        return [ymin - gap, ymax + gap]
    
    # === 7. 繪圖 ===
    # 圖1：單季
    y_range = _get_y_range(
        df_stock['淨現金流量(億)'],
        df_stock['自由現金流量(億)'],
        df_industry['淨現金流量(億)_同業平均'],
        df_industry['自由現金流量(億)_同業平均']
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['淨現金流量(億)'],
        mode='lines+markers', line=dict(color='mediumturquoise', width=2.2),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_stock['淨現金流量(億)']],
        textposition='top center', name='淨現金流量(億)-個股'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['淨現金流量(億)_同業平均'],
        mode='lines+markers', line=dict(color='mediumturquoise', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['淨現金流量(億)_同業平均']],
        textposition='top center', name='淨現金流量(億)-同業平均'
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['自由現金流量(億)'],
        mode='lines+markers', line=dict(color='red', width=2),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_stock['自由現金流量(億)']],
        textposition='top center', name='自由現金流量(億)-個股', yaxis='y2'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['自由現金流量(億)_同業平均'],
        mode='lines+markers', line=dict(color='red', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['自由現金流量(億)_同業平均']],
        textposition='top center', name='自由現金流量(億)-同業平均', yaxis='y2'
    ))
    fig.update_layout(
        title=f'{stock_id} {stock_name} 各季度 淨現金流量/自由現金流量(億) <br>\
同業最新一季平均 淨現金流量{last_net} 自由現金流量{last_free}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='淨現金流量(億)', range=y_range, side='left', showgrid=True),
        yaxis2=dict(title='自由現金流量(億)', overlaying='y', side='right', showgrid=False),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    # 圖2：近四季平均
    y_range2 = _get_y_range(
        df_stock['淨現金流量(億)_近四季平均'],
        df_stock['自由現金流量(億)_近四季平均'],
        df_industry['淨現金流量(億)_近四季同業平均'],
        df_industry['自由現金流量(億)_近四季同業平均']
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['淨現金流量(億)_近四季平均'],
        mode='lines+markers', line=dict(color='mediumturquoise', width=2.2),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_stock['淨現金流量(億)_近四季平均']],
        textposition='top center', name='淨現金流量(億)-近四季平均-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['淨現金流量(億)_近四季同業平均'],
        mode='lines+markers', line=dict(color='mediumturquoise', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['淨現金流量(億)_近四季同業平均']],
        textposition='top center', name='淨現金流量(億)-近四季平均-同業平均'
    ))
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['自由現金流量(億)_近四季平均'],
        mode='lines+markers', line=dict(color='red', width=2),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_stock['自由現金流量(億)_近四季平均']],
        textposition='top center', name='自由現金流量(億)-近四季平均-個股', yaxis='y2'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['自由現金流量(億)_近四季同業平均'],
        mode='lines+markers', line=dict(color='red', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['自由現金流量(億)_近四季同業平均']],
        textposition='top center', name='自由現金流量(億)-近四季平均-同業平均', yaxis='y2'
    ))
    fig2.update_layout(
        title=f'{stock_id} {stock_name} 近四季平均 淨現金流量/自由現金流量(億)<br>\
同業最新近四季平均 淨現金流量{last4_net} 自由現金流量{last4_free}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='淨現金流量(億)', range=y_range2, side='left', showgrid=True),
        yaxis2=dict(title='自由現金流量(億)', overlaying='y', side='right', showgrid=False),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    # === 8. 精簡 df ===
    df_out = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '淨現金流量(億)', '淨現金流量(億)_同業平均', '淨現金流量(億)_近四季平均', '淨現金流量(億)_近四季同業平均',
        '自由現金流量(億)', '自由現金流量(億)_同業平均', '自由現金流量(億)_近四季平均', '自由現金流量(億)_近四季同業平均'
    ]]
    
    return fig, fig2, df_out


# fig, fig2, df_out = plotly_net_free_cash_flow(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_out)


#%%
# 002-2 包成def
# 現金與約當現金(流動資產)、不動產廠房及設備(非流動資產)、流動負債合計、非流動負債合計、長期資金(非流動負債)趨勢
# 銀行業不看

def plotly_main_items_trend_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    """
    畫現金及約當現金、不動產廠房及設備、長期借款、流動負債合計、非流動負債合計
    五大科目及近四季平均，個股&同業都回傳
    """
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準現金及約當現金', '標準現金及約當現金_同業平均', '標準現金及約當現金_近四季平均', '標準現金及約當現金_近四季同業平均',
        '標準長期借款', '標準長期借款_同業平均', '標準長期借款_近四季平均', '標準長期借款_近四季同業平均',
        '標準流動負債合計', '標準流動負債合計_同業平均', '標準流動負債合計_近四季平均', '標準流動負債合計_近四季同業平均',
        '標準非流動負債合計', '標準非流動負債合計_同業平均', '標準非流動負債合計_近四季平均', '標準非流動負債合計_近四季同業平均',
        '標準不動產廠房及設備', '標準不動產廠房及設備_同業平均', '標準不動產廠房及設備_近四季平均', '標準不動產廠房及設備_近四季同業平均'
    ]
    for c in must_cols:
        if c not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{c}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[
        (df_bs_ci_cfs['產業類別提取'] == stock_industry) &
        (df_bs_ci_cfs['標題'].astype(str).str.endswith('金額'))
    ].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    industry_cols = [
        '年度-季度',
        '標準現金及約當現金_同業平均', '標準現金及約當現金_近四季同業平均',
        '標準長期借款_同業平均', '標準長期借款_近四季同業平均',
        '標準流動負債合計_同業平均', '標準流動負債合計_近四季同業平均',
        '標準非流動負債合計_同業平均', '標準非流動負債合計_近四季同業平均',
        '標準不動產廠房及設備_同業平均', '標準不動產廠房及設備_近四季同業平均'
    ]
    df_industry = (
        base.sort_values('年度-季度')
        .drop_duplicates(['年度-季度'], keep='last')
        [industry_cols]
        .sort_values('年度-季度')
        .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    # 這裡僅示範現金及約當現金，其他可依需要取最新一季值
    if not df_industry.empty:
        last_row = df_industry.iloc[-1]
        latest_cash = f"{last_row['標準現金及約當現金_同業平均']:.0f}" if pd.notnull(last_row['標準現金及約當現金_同業平均']) else "無資料"
        last4_cash = f"{last_row['標準現金及約當現金_近四季同業平均']:.0f}" if pd.notnull(last_row['標準現金及約當現金_近四季同業平均']) else "無資料"
    else:
        latest_cash = "無資料"
        last4_cash = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(series):
        s = series.dropna()
        if s.empty:
            return [0, 1]
        ymin = float(s.min())
        ymax = float(s.max())
        if ymin == ymax:
            return [ymin - 100, ymax + 100]
        return [ymin - 100, ymax + 100]
    
    y_merge = [
        df_stock['標準現金及約當現金'], df_stock['標準長期借款'], df_stock['標準流動負債合計'],
        df_stock['標準非流動負債合計'], df_stock['標準不動產廠房及設備'],
        df_industry['標準現金及約當現金_同業平均'], df_industry['標準長期借款_同業平均'],
        df_industry['標準流動負債合計_同業平均'], df_industry['標準非流動負債合計_同業平均'],
        df_industry['標準不動產廠房及設備_同業平均']
    ]
    y_range = _get_y_range(pd.concat(y_merge, axis=0))

    y_merge2 = [
        df_stock['標準現金及約當現金_近四季平均'], df_stock['標準長期借款_近四季平均'], df_stock['標準流動負債合計_近四季平均'],
        df_stock['標準非流動負債合計_近四季平均'], df_stock['標準不動產廠房及設備_近四季平均'],
        df_industry['標準現金及約當現金_近四季同業平均'], df_industry['標準長期借款_近四季同業平均'],
        df_industry['標準流動負債合計_近四季同業平均'], df_industry['標準非流動負債合計_近四季同業平均'],
        df_industry['標準不動產廠房及設備_近四季同業平均']
    ]
    y_range2 = _get_y_range(pd.concat(y_merge2, axis=0))

    # === 7. 繪圖 ===
    # 圖1：單季資產負債比%
    color_map = {
        '標準現金及約當現金': 'green',
        '標準長期借款': 'blue',
        '標準流動負債合計': 'orange',
        '標準非流動負債合計': 'purple',
        '標準不動產廠房及設備': 'red'
    }
    fig = go.Figure()
    for k in color_map.keys():
        fig.add_trace(go.Scatter(
            x=df_stock['年度-季度'], y=df_stock[k],
            mode='lines+markers+text', name=f"{k}-個股", line=dict(color=color_map[k], width=2.0)
        ))
    for k in color_map.keys():
        fig.add_trace(go.Scatter(
            x=df_industry['年度-季度'], y=df_industry[f"{k}_同業平均"],
            mode='lines+markers+text', name=f"{k}-同業平均", line=dict(color=color_map[k], dash='dot', width=2.0)
        ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 各季度主要資產負債科目趨勢｜同業最新一季平均現金：{latest_cash}',
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='金額', range=y_range),
        width=900, height=500,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # 圖2：近四季平均
    fig2 = go.Figure()
    for k in color_map.keys():
        fig2.add_trace(go.Scatter(
            x=df_stock['年度-季度'], y=df_stock[f"{k}_近四季平均"],
            mode='lines+markers+text', name=f"{k}-近四季平均-個股", line=dict(color=color_map[k], width=2.0)
        ))
    for k in color_map.keys():
        fig2.add_trace(go.Scatter(
            x=df_industry['年度-季度'], y=df_industry[f"{k}_近四季同業平均"],
            mode='lines+markers+text', name=f"{k}-近四季平均-同業平均", line=dict(color=color_map[k], dash='dot', width=2.0)
        ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均主要資產負債科目趨勢｜同業最新近四季平均現金：{last4_cash}',
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='金額', range=y_range2),
        width=900, height=500,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # === 8. 精簡 df ===
    keep_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準現金及約當現金', '標準現金及約當現金_同業平均', '標準現金及約當現金_近四季平均', '標準現金及約當現金_近四季同業平均',
        '標準長期借款', '標準長期借款_同業平均', '標準長期借款_近四季平均', '標準長期借款_近四季同業平均',
        '標準流動負債合計', '標準流動負債合計_同業平均', '標準流動負債合計_近四季平均', '標準流動負債合計_近四季同業平均',
        '標準非流動負債合計', '標準非流動負債合計_同業平均', '標準非流動負債合計_近四季平均', '標準非流動負債合計_近四季同業平均',
        '標準不動產廠房及設備', '標準不動產廠房及設備_同業平均', '標準不動產廠房及設備_近四季平均', '標準不動產廠房及設備_近四季同業平均'
    ]
    df_main_items_trend = df_stock[keep_cols].reset_index(drop=True)
    
    return fig, fig2, df_main_items_trend

# fig, fig2, df_main_items_trend = plotly_main_items_trend_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_main_items_trend)



# 004 包成def
# 股東權益: 股本、保留盈餘、資本公積
# 銀行業ok

def plotly_shareholders_equity_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    """
    直接用 df_bs_ci_cfs 現成股本/保留盈餘/資本公積四大欄位（含同業、近四季）畫圖，標註完全 SOP。
    """

    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準股本', '標準股本_同業平均', '標準股本_近四季平均', '標準股本_近四季同業平均',
        '標準保留盈餘', '標準保留盈餘_同業平均', '標準保留盈餘_近四季平均', '標準保留盈餘_近四季同業平均',
        '標準資本公積', '標準資本公積_同業平均', '標準資本公積_近四季平均', '標準資本公積_近四季同業平均'
    ]
    for c in must_cols:
        if c not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{c}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[
        (df_bs_ci_cfs['產業類別提取'] == stock_industry) &
        (df_bs_ci_cfs['標題'].astype(str).str.endswith('金額'))
    ].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.sort_values('年度-季度')
        .drop_duplicates(['年度-季度'], keep='last')
        [['年度-季度',
          '標準股本_同業平均', '標準股本_近四季同業平均',
          '標準保留盈餘_同業平均', '標準保留盈餘_近四季同業平均',
          '標準資本公積_同業平均', '標準資本公積_近四季同業平均']]
        .sort_values('年度-季度')
        .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last_row = df_industry.iloc[-1]
        latest_mean_str = '、'.join([
            f"股本:{last_row['標準股本_同業平均']/1e8:.2f}億" if pd.notnull(last_row['標準股本_同業平均']) else "股本:無資料",
            f"保留盈餘:{last_row['標準保留盈餘_同業平均']/1e8:.2f}億" if pd.notnull(last_row['標準保留盈餘_同業平均']) else "保留盈餘:無資料",
            f"資本公積:{last_row['標準資本公積_同業平均']/1e8:.2f}億" if pd.notnull(last_row['標準資本公積_同業平均']) else "資本公積:無資料"
        ])
        last4_avg_str = '、'.join([
            f"股本:{last_row['標準股本_近四季同業平均']/1e8:.2f}億" if pd.notnull(last_row['標準股本_近四季同業平均']) else "股本:無資料",
            f"保留盈餘:{last_row['標準保留盈餘_近四季同業平均']/1e8:.2f}億" if pd.notnull(last_row['標準保留盈餘_近四季同業平均']) else "保留盈餘:無資料",
            f"資本公積:{last_row['標準資本公積_近四季同業平均']/1e8:.2f}億" if pd.notnull(last_row['標準資本公積_近四季同業平均']) else "資本公積:無資料"
        ])
    else:
        latest_mean_str = last4_avg_str = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(series):
        s = series.dropna()
        if s.empty:
            return [0, 1]
        ymin = float(s.min())
        ymax = float(s.max())
        if ymin == ymax:
            return [ymin - 1e7, ymax + 1e7]
        return [ymin - 1e7, ymax + 1e7]
    
    y_merge = [
        df_stock['標準股本'], df_stock['標準保留盈餘'], df_stock['標準資本公積'],
        df_industry['標準股本_同業平均'], df_industry['標準保留盈餘_同業平均'], df_industry['標準資本公積_同業平均']
    ]
    y_range = _get_y_range(pd.concat(y_merge, axis=0))
    y_merge2 = [
        df_stock['標準股本_近四季平均'], df_stock['標準保留盈餘_近四季平均'], df_stock['標準資本公積_近四季平均'],
        df_industry['標準股本_近四季同業平均'], df_industry['標準保留盈餘_近四季同業平均'], df_industry['標準資本公積_近四季同業平均']
    ]
    y_range2 = _get_y_range(pd.concat(y_merge2, axis=0))

    # === 7. 繪圖 ===
    # 圖1：單季資產負債比%
    color_map = {
        '標準股本_近四季平均': 'mediumturquoise',
        '標準保留盈餘_近四季平均': 'red',
        '標準資本公積_近四季平均': 'blue'
    }
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準股本'],
        mode='lines+markers+text', name='股本-個股',
        line=dict(color='mediumturquoise', width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準股本_同業平均'],
        mode='lines+markers+text', name='股本-同業平均',
        line=dict(color='mediumturquoise', dash='dot', width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準保留盈餘'],
        mode='lines+markers+text', name='保留盈餘-個股',
        line=dict(color='red', width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準保留盈餘_同業平均'],
        mode='lines+markers+text', name='保留盈餘-同業平均',
        line=dict(color='red', dash='dot', width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準資本公積'],
        mode='lines+markers+text', name='資本公積-個股',
        line=dict(color='blue', width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準資本公積_同業平均'],
        mode='lines+markers+text', name='資本公積-同業平均',
        line=dict(color='blue', dash='dot', width=2.5)
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 股東權益結構<br>\
同業最新一季平均：{latest_mean_str}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='金額', range=y_range),
        width=1000, height=500,
        legend=dict(title='', orientation='h')
    )

    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準股本_近四季平均'],
        mode='lines+markers+text', name='股本-近四季平均-個股',
        line=dict(color='mediumturquoise', width=2.5)
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準股本_近四季同業平均'],
        mode='lines+markers+text', name='股本-近四季平均-同業平均',
        line=dict(color='mediumturquoise', dash='dot', width=2.5)
    ))
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準保留盈餘_近四季平均'],
        mode='lines+markers+text', name='保留盈餘-近四季平均-個股',
        line=dict(color='red', width=2.5)
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準保留盈餘_近四季同業平均'],
        mode='lines+markers+text', name='保留盈餘-近四季平均-同業平均',
        line=dict(color='red', dash='dot', width=2.5)
    ))
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['標準資本公積_近四季平均'],
        mode='lines+markers+text', name='資本公積-近四季平均-個股',
        line=dict(color='blue', width=2.5)
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['標準資本公積_近四季同業平均'],
        mode='lines+markers+text', name='資本公積-近四季平均-同業平均',
        line=dict(color='blue', dash='dot', width=2.5)
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均股東權益結構<br>\
同業近四季平均：{last4_avg_str}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='金額', range=y_range2),
        width=1000, height=500,
        legend=dict(title='', orientation='h')
    )

    # === 8. 精簡 df ===
    keep_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
            '標準股本_同業平均', '標準股本_近四季同業平均',
          '標準保留盈餘_同業平均', '標準保留盈餘_近四季同業平均',
          '標準資本公積_同業平均', '標準資本公積_近四季同業平均'
    ]
    df_shareholders_equity = df_stock[keep_cols].reset_index(drop=True)

    return fig, fig2, df_shareholders_equity

# fig, fig2, df_shareholders_equity = plotly_shareholders_equity_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_shareholders_equity)



#%%
# 012~014 包成def
# 現金流量關鍵
# 現金流量比率 = 營業活動淨現金流量 / 流動負債
# 現金流量允當比率 = 最近五年度營業活動淨現金流量 / 最近五年度（資本支出 + 存貨增加額 + 現金股利）
# 現金再投資比率 = （營業活動淨現金流量 - 現金股利） / （不動產、廠房及設備毛額 + 長期投資 + 其他非流動資產 + 營運資金）
# 銀行業不看


def plotly_cfr_ratio(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '現金流量比率%', '現金流量比率%_同業平均',
        '現金流量比率%_近四季平均', '現金流量比率%_近四季同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')
    
    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()
    
    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')
    
    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['現金流量比率%_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )
    
    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        last_cfr = f"{last['現金流量比率%_同業平均']:.2f}%"
        last4_cfr = f"{last['現金流量比率%_近四季同業平均']:.2f}%"
    else:
        last_cfr = last4_cfr = "無資料"
    
    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [0, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        return [ymin - 5, ymax + 5]
    
    # === 7. 繪圖 ===
    # 圖1：單季
    y_range = _get_y_range(
        df_stock['現金流量比率%'], df_industry['現金流量比率%_同業平均']
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['現金流量比率%'],
        mode='lines+markers+text', line=dict(color='mediumturquoise', width=2.5),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['現金流量比率%']],
        textposition='top center', name='現金流量比率%-個股'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['現金流量比率%_同業平均'],
        mode='lines+markers+text', line=dict(color='mediumturquoise', dash='dot', width=1.5),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['現金流量比率%_同業平均']],
        textposition='top center', name='現金流量比率%-同業平均'
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度現金流量比率%｜同業最新一季平均：{last_cfr}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='現金流量比率%', range=y_range),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    # 圖2：近四季平均
    y_range2 = _get_y_range(
        df_stock['現金流量比率%_近四季平均'], df_industry['現金流量比率%_近四季同業平均']
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['現金流量比率%_近四季平均'],
        mode='lines+markers+text', line=dict(color='blue', width=2.5),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['現金流量比率%_近四季平均']],
        textposition='top center', name='近四季平均現金流量比率%-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['現金流量比率%_近四季同業平均'],
        mode='lines+markers+text', line=dict(color='blue', dash='dot', width=1.5),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['現金流量比率%_近四季同業平均']],
        textposition='top center', name='近四季平均現金流量比率%-同業平均'
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均現金流量比率%｜同業最新近四季平均：{last4_cfr}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='現金流量比率%', range=y_range2),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    # === 8. 精簡 df ===
    df_cfr = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '現金流量比率%', '現金流量比率%_同業平均',
        '現金流量比率%_近四季平均', '現金流量比率%_近四季同業平均'
    ]]
    
    return fig, fig2, df_cfr


# fig, fig2, df_cfr = plotly_cfr_ratio(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_cfr)


#%%
# 015 包成def 
# 現金佔比趨勢
# 現金最好佔總資產10~25%，資本密集行業最好更高
# 銀行業ok

def plotly_cashncash_equivalents(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '現金佔比%', '現金佔比%_同業平均', '現金佔比%_近四季平均', '現金佔比%_近四季同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['現金佔比%_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        latest_cash = f"{last['現金佔比%_同業平均']:.2f}%"
        latest4_cash = f"{last['現金佔比%_近四季同業平均']:.2f}%"
    else:
        latest_cash = "無資料"
        latest4_cash = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        return [ymin - 5, ymax + 5]

    # === 7. 繪圖 ===
    # 圖1：單季
    y_range = _get_y_range(
        df_stock['現金佔比%'], df_industry['現金佔比%_同業平均']
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['現金佔比%'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        marker=dict(color=['red' if v < 10 else 'mediumturquoise' for v in df_stock['現金佔比%']]),
        text=df_stock['現金佔比%'].astype(str)+'%',
        textposition='top center',
        name='現金佔比%-個股'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['現金佔比%_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=2),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['現金佔比%_同業平均']],
        textposition='top center',
        name='現金佔比%-同業平均'
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度現金佔總資產比％｜同業最新一季平均：{latest_cash}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='現金佔比%', range=y_range),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖2：近四季平均
    y_range2 = _get_y_range(
        df_stock['現金佔比%_近四季平均'], df_industry['現金佔比%_近四季同業平均']
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['現金佔比%_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='orange', width=2.5),
        marker=dict(color=['red' if v < 10 else 'orange' for v in df_stock['現金佔比%_近四季平均']]),
        text=df_stock['現金佔比%_近四季平均'].astype(str)+'%',
        textposition='top center',
        name='近四季平均現金佔比%-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['現金佔比%_近四季同業平均'],
        mode='lines+markers+text',
        line=dict(color='orange', dash='dot', width=2),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['現金佔比%_近四季同業平均']],
        textposition='top center',
        name='近四季平均現金佔比%-同業平均'
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均現金佔總資產比％｜同業最新近四季平均：{latest4_cash}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季平均現金佔比%', range=y_range2),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # === 8. 精簡 df ===
    df_cashncash_equivalents = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '現金佔比%', '現金佔比%_同業平均', '現金佔比%_近四季平均', '現金佔比%_近四季同業平均'
    ]]

    return fig, fig2, df_cashncash_equivalents


# fig, fig2, df_cashncash_equivalents = plotly_cashncash_equivalents(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_cashncash_equivalents)




#%%
# 007 包成def
# 應收帳款、存貨周轉、應付帳款、總資產周轉、現金佔比


def plotly_turnover_trend(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '總資產周轉(次)', '存貨周轉(次)', '應收帳款周轉(次)', '應付帳款周轉(次)',
        '近四季累積總資產周轉(次)', '近四季累積總資產周轉(次)_同業平均',
        '近四季累積存貨周轉(次)', '近四季累積存貨周轉(次)_同業平均',
        '近四季累積應收帳款周轉(次)', '近四季累積應收帳款周轉(次)_同業平均',
        '近四季累積應付帳款周轉(次)', '近四季累積應付帳款周轉(次)_同業平均',
        '近四季存貨天數', '近四季存貨天數_同業平均',
        '近四季應收帳款天數', '近四季應收帳款天數_同業平均',
        '近四季應付帳款天數', '近四季應付帳款天數_同業平均',
        '現金周轉天數', '現金周轉天數_同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[
        (df_bs_ci_cfs['產業類別提取'] == stock_industry)
    ].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['近四季累積總資產周轉(次)_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        title_turn = f"同業近四季累積週轉(次) 存貨{last['近四季累積存貨周轉(次)_同業平均']:.2f}、應收{last['近四季累積應收帳款周轉(次)_同業平均']:.2f}、應付{last['近四季累積應付帳款周轉(次)_同業平均']:.2f}"
        title_days = f"同業近四季累積天數 存貨{last['近四季存貨天數_同業平均']:.2f}、應收{last['近四季應收帳款天數_同業平均']:.2f}、應付{last['近四季應付帳款天數_同業平均']:.2f}"
        title_cash = f"同業近四季平均現金周轉天數 {last['現金周轉天數_同業平均']:.2f}天"
    else:
        title_turn = title_days = title_cash = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(*series):
        vals = pd.concat([s.dropna() for s in series if s is not None], axis=0)
        if vals.empty: return [0, 1]
        return [float(vals.min()) - 10, float(vals.max()) + 10]

    # y_range3 = _get_y_range(pd.concat([
    #     df_stock['近四季累積存貨周轉(次)'], df_industry['近四季累積應付帳款周轉(次)_同業平均']
    # ], ignore_index=True))
    
    # === 7. 繪圖 ===
    # table
    table_data = df_stock[['年度-季度','總資產周轉(次)','存貨周轉(次)','應收帳款周轉(次)','應付帳款周轉(次)']].T.reset_index()
    table_data.columns = table_data.iloc[0]
    table_data = table_data[1:]
    table_data = table_data.loc[:, table_data.notna().any(axis=0)]
    fig_table = ff.create_table(table_data, height_constant=30)
    fig_table.update_layout(
        title=f"{stock_id} 單季營運週轉",
        width=1000, height=200,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))
    
    

    # 圖2：bar
    fig_asset = go.Figure()
    fig_asset.add_trace(go.Bar(
        x=df_stock['年度-季度'],
        y=df_stock['近四季累積總資產周轉(次)'],
        text=[f"{x:.2f}" if not pd.isnull(x) else "" for x in df_stock['近四季累積總資產周轉(次)']],
        marker_color=['red' if x <= 1 else 'mediumturquoise' for x in df_stock['近四季累積總資產周轉(次)']],
        name='近四季累積總資產周轉-個股',
        width=0.4,
    ))
    fig_asset.add_trace(go.Bar(
        x=df_industry['年度-季度'],
        y=df_industry['近四季累積總資產周轉(次)_同業平均'],
        text=[f"{x:.2f}" if not pd.isnull(x) else "" for x in df_industry['近四季累積總資產周轉(次)_同業平均']],
        marker_color=['pink' for x in df_industry['近四季累積總資產周轉(次)_同業平均']],
        name='近四季累積總資產周轉-同業平均',
        width=0.4,
    ))
    fig_asset.update_layout(
        title=f"{stock_id} {stock_name} 近四季累積總資產周轉(次)",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='總資產周轉(次)'),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))
    

    # 圖3：單季 + 近四季周轉(次)（個股線 -> 同業虛線, 依指標一組一組）
    fig_turn = go.Figure()
    # 存貨
    fig_turn.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['近四季累積存貨周轉(次)'],
        mode='lines+markers+text', line=dict(color='red', width=2),
        name='近四季累積存貨周轉-個股'
    ))
    fig_turn.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['近四季累積存貨周轉(次)_同業平均'],
        mode='lines+markers+text', line=dict(color='red', width=2, dash='dot'),
        name='近四季累積存貨周轉-同業平均'
    ))
    # 應收
    fig_turn.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['近四季累積應收帳款周轉(次)'],
        mode='lines+markers+text', line=dict(color='blue', width=2),
        name='近四季累積應收帳款周轉-個股'
    ))
    fig_turn.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['近四季累積應收帳款周轉(次)_同業平均'],
        mode='lines+markers+text', line=dict(color='blue', width=2, dash='dot'),
        name='近四季累積應收帳款周轉-同業平均'
    ))
    # 應付
    fig_turn.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['近四季累積應付帳款周轉(次)'],
        mode='lines+markers+text', line=dict(color='mediumturquoise', width=2.2),
        name='近四季累積應付帳款周轉-個股'
    ))
    fig_turn.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['近四季累積應付帳款周轉(次)_同業平均'],
        mode='lines+markers+text', line=dict(color='mediumturquoise', width=2.2, dash='dot'),
        name='近四季累積應付帳款周轉-同業平均'
    ))
    fig_turn.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季累積存貨、應收、應付帳款周轉(次) <br>{title_turn}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='周轉(次)', range=_get_y_range(
            df_stock['近四季累積存貨周轉(次)'], df_industry['近四季累積存貨周轉(次)_同業平均'],
            df_stock['近四季累積應收帳款周轉(次)'], df_industry['近四季累積應收帳款周轉(次)_同業平均'],
            df_stock['近四季累積應付帳款周轉(次)'], df_industry['近四季累積應付帳款周轉(次)_同業平均'],
        )),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # 圖4：近四季平均天數（個股線 -> 同業虛線）
    fig_days = go.Figure()
    # 存貨
    fig_days.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['近四季存貨天數'],
        mode='lines+markers+text', line=dict(color='red', width=2),
        name='近四季累積存貨天數-個股'
    ))
    fig_days.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['近四季存貨天數_同業平均'],
        mode='lines+markers+text', line=dict(color='red', width=2, dash='dot'),
        name='近四季累積存貨天數-同業平均'
    ))
    # 應收
    fig_days.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['近四季應收帳款天數'],
        mode='lines+markers+text', line=dict(color='blue', width=2),
        name='近四季累積應收帳款天數-個股'
    ))
    fig_days.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['近四季應收帳款天數_同業平均'],
        mode='lines+markers+text', line=dict(color='blue', width=2, dash='dot'),
        name='近四季累積應收帳款天數-同業平均'
    ))
    # 應付
    fig_days.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['近四季應付帳款天數'],
        mode='lines+markers+text', line=dict(color='mediumturquoise', width=2.2),
        name='近四季累積應付帳款天數-個股'
    ))
    fig_days.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['近四季應付帳款天數_同業平均'],
        mode='lines+markers+text', line=dict(color='mediumturquoise', width=2.2, dash='dot'),
        name='近四季累積應付帳款天數-同業平均'
    ))
    fig_days.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季存貨、應收、應付帳款天數<br>{title_days}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='天數', range=_get_y_range(
            df_stock['近四季存貨天數'], df_industry['近四季存貨天數_同業平均'],
            df_stock['近四季應收帳款天數'], df_industry['近四季應收帳款天數_同業平均'],
            df_stock['近四季應付帳款天數'], df_industry['近四季應付帳款天數_同業平均'],
        )),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))


    # 現金周轉天數
    fig_cash = go.Figure()
    fig_cash.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['現金周轉天數'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=3),
        marker=dict(size=8),
        text=[f"{x:.2f}" if not pd.isnull(x) else "" for x in df_stock['現金周轉天數']],
        textposition='top center',
        name='近四季平均現金周轉天數-個股'
    ))
    fig_cash.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['現金周轉天數_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2, dash='dot'),
        marker=dict(size=8),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['現金周轉天數_同業平均']],
        textposition='top center',
        name='近四季平均現金周轉天數-同業平均'
    ))
    fig_cash.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均現金周轉天數 | {title_cash}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='現金周轉天數', range=_get_y_range(df_stock['現金周轉天數'], df_industry['現金周轉天數_同業平均'])),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # === 8. 精簡 df ===
    df_turnover = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '總資產周轉(次)', '存貨周轉(次)', '應收帳款周轉(次)', '應付帳款周轉(次)',
        '近四季累積總資產周轉(次)', '近四季累積總資產周轉(次)_同業平均',
        '近四季累積存貨周轉(次)', '近四季累積存貨周轉(次)_同業平均',
        '近四季累積應收帳款周轉(次)', '近四季累積應收帳款周轉(次)_同業平均',
        '近四季累積應付帳款周轉(次)', '近四季累積應付帳款周轉(次)_同業平均',
        '近四季存貨天數', '近四季存貨天數_同業平均',
        '近四季應收帳款天數', '近四季應收帳款天數_同業平均',
        '近四季應付帳款天數', '近四季應付帳款天數_同業平均',
        '現金周轉天數', '現金周轉天數_同業平均'
        
    ]].reset_index(drop=True)

    return fig_table, fig_asset, fig_turn, fig_days, fig_cash, df_turnover



# fig_table, fig_asset, fig_turn, fig_days, fig_cash, df_turnover = plotly_turnover_trend(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig_table.show() 
# fig_asset.show()
# fig_turn.show() 
# fig_days.show()  
# fig_cash.show() 
# display(df_turnover)


#%%
# 007-2 包成def
# (若是有假公司財報，觀察應收帳款天數、應收帳款佔總資產比率、存貨天數、存貨佔總資產比率，是否急遽增加
# 營業收入、淨利成長，但OCF一直收不到現金，現金與約當現金沒成長)
# 銀行業不看

def plotly_fake_new(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '近四季平均應收帳款%', '近四季平均應收帳款%_同業平均',
        '近四季平均存貨%', '近四季平均存貨%_同業平均',
        '近四季累積營業收入', '近四季累積營業收入_同業平均',
        '近四季累積本期淨利', '近四季累積本期淨利_同業平均',
        '近四季平均現金及約當現金', '近四季平均現金及約當現金_同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    # 只要每一季度一筆同業平均
    df_industry = (
        base.dropna(subset=['近四季平均應收帳款%_同業平均'], how='all')
        .drop_duplicates(['年度-季度'], keep='last')
        .sort_values('年度-季度')
        .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    

    # === 6. y 範圍 ===
    def _get_y_range(*series):
        vals = pd.concat([s.dropna() for s in series if s is not None], axis=0)
        if vals.empty: return [0, 1]
        return [float(vals.min()) - 1e8, float(vals.max()) + 1e8]

    # === 7. 繪圖 ===
    # 圖1：單季bar+折線圖
    fig = go.Figure()
    # 應收帳款% - 個股
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['近四季平均應收帳款%'],
        marker=dict(color='blue'), name='近四季平均應收帳款%-個股', width=0.18, offset=-0.18
    ))
    # 應收帳款% - 同業
    fig.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['近四季平均應收帳款%_同業平均'],
        marker=dict(color='deepskyblue'), name='近四季平均應收帳款%-同業平均', width=0.18, offset=0.18
    ))
    # 存貨% - 個股
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['近四季平均存貨%'],
        marker=dict(color='red'), name='近四季平均存貨%-個股', width=0.18, offset=0.00
    ))
    # 存貨% - 同業
    fig.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['近四季平均存貨%_同業平均'],
        marker=dict(color='pink'), name='近四季平均存貨%-同業平均', width=0.18, offset=0.36
    ))

    # 營收 - 個股
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['近四季累積營業收入'],
        mode='lines+markers+text', line=dict(color='orange', width=2),
        name='近四季累積營業收入-個股', yaxis='y2'
    ))
    # 營收 - 同業
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['近四季累積營業收入_同業平均'],
        mode='lines+markers', line=dict(color='orange', dash='dot', width=2),
        name='近四季累積營業收入-同業平均', yaxis='y2'
    ))
    # 淨利 - 個股
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['近四季累積本期淨利'],
        mode='lines+markers+text', line=dict(color='blue', width=2),
        name='近四季累積本期淨利-個股', yaxis='y2'
    ))
    # 淨利 - 同業
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['近四季累積本期淨利_同業平均'],
        mode='lines+markers', line=dict(color='blue', dash='dot', width=2),
        name='近四季累積本期淨利-同業平均', yaxis='y2'
    ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均 應收帳款%、存貨%、營收與淨利走勢',
        barmode='group',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(
            title='近四季平均 應收帳款%、存貨%',
            side='left',
            showgrid=True,
            rangemode='tozero'
        ),
        yaxis2=dict(
            title='近四季累積營業收入、淨利',
            side='right',
            overlaying='y',
            showgrid=False,
            rangemode='tozero'
        ),
        width=900,
        height=500,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖2：近四季平均現金及約當現金
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['近四季平均現金及約當現金'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2),
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_stock['近四季平均現金及約當現金']],
        textposition='top center',
        name='近四季平均現金及約當現金-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['近四季平均現金及約當現金_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=2),
        text=[f"{v/1e8:.2f}億" if not pd.isnull(v) else "" for v in df_industry['近四季平均現金及約當現金_同業平均']],
        textposition='top center',
        name='近四季平均現金及約當現金-同業平均'
    ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均現金及約當現金',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季平均現金及約當現金', range=_get_y_range(
            df_stock['近四季平均現金及約當現金'], df_industry['近四季平均現金及約當現金_同業平均'])),
            width=900,
            height=350,
            legend=dict(
                orientation='h',          # 水平排列
                yanchor='top',            # 錨點對齊上方
                y=-0.3,                   # 向下移
                xanchor='center',         # X 軸錨點對齊中央
                x=0.5                     # 置中
            )
        )
    

    # === 8. 精簡 df ===
    df_fake_new = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '近四季平均應收帳款%', '近四季平均應收帳款%_同業平均',
        '近四季平均存貨%', '近四季平均存貨%_同業平均',
        '近四季累積營業收入', '近四季累積營業收入_同業平均',
        '近四季累積本期淨利', '近四季累積本期淨利_同業平均',
        '近四季平均現金及約當現金', '近四季平均現金及約當現金_同業平均'
    ]]

    return fig, fig2, df_fake_new


# fig, fig2, df_fake_new = plotly_fake_new(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_fake_new)


#%%
# 008 包成def
# 不動產、廠房及設備週轉率 Fixed Asset Turnover Ratio
# 銀行業ok (改成利息收入/平均不動產、廠房及設備淨額)、沒有不動產就不顯示


def plotly_fixed_asset_turnover_ready(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '不動產廠房及設備週轉(次)', '不動產廠房及設備週轉(次)_同業平均',
        '近四季累積不動產廠房及設備週轉(次)', '近四季累積不動產廠房及設備週轉(次)_同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')
    
    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['不動產廠房及設備週轉(次)_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        latest_turnover = f"{last['不動產廠房及設備週轉(次)_同業平均']:.2f}"
        late4_turnover = f"{last['近四季累積不動產廠房及設備週轉(次)_同業平均']:.2f}"
    else:
        latest_turnover = late4_turnover = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(*series):
        vals = pd.concat([s.dropna() for s in series if s is not None], axis=0)
        if vals.empty: return [0, 1]
        return [float(vals.min()) - 0.3, float(vals.max()) + 0.3]

    # === 7. 繪圖 ===
    # 圖1：單季
    y_range1 = _get_y_range(
        df_stock['不動產廠房及設備週轉(次)'], df_industry['不動產廠房及設備週轉(次)_同業平均']
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['不動產廠房及設備週轉(次)'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        marker=dict(size=8),
        text=[f"{x:.2f}" if not pd.isnull(x) else "" for x in df_stock['不動產廠房及設備週轉(次)']],
        textposition='top center',
        name='不動產廠房及設備週轉(次)-個股'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['不動產廠房及設備週轉(次)_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=2),
        text=[f"{x:.2f}" if not pd.isnull(x) else "" for x in df_industry['不動產廠房及設備週轉(次)_同業平均']],
        textposition='top center',
        name='不動產廠房及設備週轉(次)-同業平均'
    ))
    fig.update_layout(
        title=f'{stock_id} {stock_name} 各季度不動產廠房及設備週轉(次) | 同業最新一季 {latest_turnover}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='不動產廠房及設備週轉(次)', range=y_range1),
        width=900, height=400,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖2：近四季平均
    y_range2 = _get_y_range(
        df_stock['近四季累積不動產廠房及設備週轉(次)'], df_industry['近四季累積不動產廠房及設備週轉(次)_同業平均']
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['近四季累積不動產廠房及設備週轉(次)'],
        mode='lines+markers+text',
        line=dict(color='orange', width=3),
        marker=dict(size=8),
        text=[f"{x:.2f}" if not pd.isnull(x) else "" for x in df_stock['近四季累積不動產廠房及設備週轉(次)']],
        textposition='top center',
        name='近四季累積週轉-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['近四季累積不動產廠房及設備週轉(次)_同業平均'],
        mode='lines+markers+text',
        line=dict(color='orange', dash='dot', width=2),
        text=[f"{x:.2f}" if not pd.isnull(x) else "" for x in df_industry['近四季累積不動產廠房及設備週轉(次)_同業平均']],
        textposition='top center',
        name='近四季累積週轉-同業平均'
    ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季累積不動產廠房及設備週轉(次) | 同業近四季累積平均 {late4_turnover}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季累積週轉(次)', range=y_range2),
        width=900, height=400,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    

    # === 8. 精簡 df ===
    df_fixed_asset_turnover = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '不動產廠房及設備週轉(次)', '不動產廠房及設備週轉(次)_同業平均',
        '近四季累積不動產廠房及設備週轉(次)', '近四季累積不動產廠房及設備週轉(次)_同業平均'
    ]]

    return fig, fig2, df_fixed_asset_turnover


# fig, fig2, df_fixed_asset_turnover = plotly_fixed_asset_turnover_ready(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_fixed_asset_turnover)



#%%
#%%
# 005 包成def
# ROE
# 銀行業ok

def plotly_roe(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    """
    直接用 df_bs_ci_cfs 現成單季ROE% 四個欄位畫圖，並符合SOP格式。
    """
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '單季ROE%', '單季ROE%_同業平均',
        '單季ROE%_近四季平均', '單季ROE%_近四季同業平均',
        '近四季累積ROE%', '近四季累積ROE%_同業平均'
    ]
    for c in must_cols:
        if c not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{c}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[
        (df_bs_ci_cfs['產業類別提取'] == stock_industry) &
        (df_bs_ci_cfs['標題'].astype(str).str.endswith('金額'))
    ].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.sort_values('年度-季度')
        .dropna(subset=['單季ROE%_同業平均'], how='all')
        .drop_duplicates(['年度-季度'], keep='last')
        [['年度-季度', '單季ROE%_同業平均', '單季ROE%_近四季同業平均', '近四季累積ROE%_同業平均']]
        .sort_values('年度-季度')
        .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last_row = df_industry.iloc[-1]
        latest_mean_str = (
            f"{last_row['單季ROE%_同業平均']:.2f}%"
            if pd.notnull(last_row['單季ROE%_同業平均']) else "無資料"
        )
        last4_mean_str = (
            f"{last_row['單季ROE%_近四季同業平均']:.2f}%"
            if pd.notnull(last_row['單季ROE%_近四季同業平均']) else "無資料"
        )
        last4_sum_str = (
            f"{last_row['近四季累積ROE%_同業平均']:.2f}%"
            if pd.notnull(last_row['近四季累積ROE%_同業平均']) else "無資料"
        )
    else:
        latest_mean_str = last4_mean_str = last4_sum_str = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(series):
        s = series.dropna()
        if s.empty:
            return [0, 1]
        ymin = float(s.min())
        ymax = float(s.max())
        if ymin == ymax:
            return [ymin - 2, ymax + 2]
        return [ymin - 2, ymax + 2]
    
    y_range = _get_y_range(pd.concat([
        df_stock['單季ROE%'], df_industry['單季ROE%_同業平均']
    ], ignore_index=True))
    y_range2 = _get_y_range(pd.concat([
        df_stock['單季ROE%_近四季平均'], df_industry['單季ROE%_近四季同業平均']
    ], ignore_index=True))

    # === 7. 繪圖 ===

    # table
    table_data = (
        df_stock[['年度-季度', '單季ROE%']]
        .dropna()
        .set_index('年度-季度').T
    )
    table = ff.create_table(table_data.round(2), height_constant=30)
    table.update_layout(
        title=f"{stock_id} {stock_name} 單季ROE%",
        width=1000, height=200
    )

    # 圖1：單季資產負債比%
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['單季ROE%'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_stock['單季ROE%']],
        textposition='top center',
        name="單季ROE%-個股"
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['單季ROE%_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_industry['單季ROE%_同業平均']],
        textposition='top center',
        name="單季ROE%-同業平均"
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度單季ROE%｜同業最新一季平均：{latest_mean_str}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='單季ROE%', range=y_range),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['單季ROE%_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='orange', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_stock['單季ROE%_近四季平均']],
        textposition='top center',
        name="近四季平均ROE%-個股"
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['單季ROE%_近四季同業平均'],
        mode='lines+markers+text',
        line=dict(color='orange', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_industry['單季ROE%_近四季同業平均']],
        textposition='top center',
        name="近四季平均ROE%-同業平均"
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均ROE趨勢%｜同業最新近四季平均：{last4_mean_str}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季平均ROE%', range=y_range2),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))


    # 圖3：近四季累積
    if ('近四季累積ROE%' not in df_bs_ci_cfs.columns or 
        '近四季累積ROE%_同業平均' not in df_bs_ci_cfs.columns):
        raise ValueError('缺少「近四季累積ROE%」或「近四季累積ROE%_同業平均」欄位！')

    df_stock['近四季累積ROE%'] = pd.to_numeric(df_stock['近四季累積ROE%'], errors='coerce')
    df_industry['近四季累積ROE%_同業平均'] = pd.to_numeric(df_industry['近四季累積ROE%_同業平均'], errors='coerce')

    y_range3 = _get_y_range(pd.concat([
        df_stock['近四季累積ROE%'], df_industry['近四季累積ROE%_同業平均']
    ], ignore_index=True))

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['近四季累積ROE%'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_stock['近四季累積ROE%']],
        textposition='top center',
        name="近四季累積ROE%-個股"
    ))
    fig3.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['近四季累積ROE%_同業平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_industry['近四季累積ROE%_同業平均']],
        textposition='top center',
        name="近四季累積ROE%-同業平均"
    ))
    fig3.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季累積ROE趨勢%｜同業最新近四季累積：{last4_sum_str}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季累積ROE%', range=y_range3),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))


    # === 8. 精簡 df ===
    keep_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '單季ROE%', '單季ROE%_同業平均',
        '單季ROE%_近四季平均', '單季ROE%_近四季同業平均',
        '近四季累積ROE%', '近四季累積ROE%_同業平均'
    ]
    df_roe = df_stock[keep_cols].reset_index(drop=True)

    return table, fig, fig2, fig3, df_roe


# table, fig, fig2, fig3, df_roe = plotly_roe(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# table.show() 
# fig.show()
# fig2.show()
# fig3.show()
# display(df_roe)



#%%
# 006 包成def
# roa
# 銀行業ok

def plotly_roa(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    """
    直接用 df_bs_ci_cfs 現成單季ROA% 四個欄位畫圖，並符合SOP格式。
    """
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '單季ROA%', '單季ROA%_同業平均',
        '單季ROA%_近四季平均', '單季ROA%_近四季同業平均',
        '近四季累積ROA%', '近四季累積ROA%_同業平均'
    ]
    for c in must_cols:
        if c not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{c}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[
        (df_bs_ci_cfs['產業類別提取'] == stock_industry) &
        (df_bs_ci_cfs['標題'].astype(str).str.endswith('金額'))
    ].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.sort_values('年度-季度')
        .dropna(subset=['單季ROA%_同業平均'], how='all')
        .drop_duplicates(['年度-季度'], keep='last')
        [['年度-季度', '單季ROA%_同業平均', '單季ROA%_近四季同業平均', '近四季累積ROA%', '近四季累積ROA%_同業平均']]
        .sort_values('年度-季度')
        .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last_row = df_industry.iloc[-1]
        latest_mean_str = (
            f"{last_row['單季ROA%_同業平均']:.2f}%"
            if pd.notnull(last_row['單季ROA%_同業平均']) else "無資料"
        )
        last4_mean_str = (
            f"{last_row['單季ROA%_近四季同業平均']:.2f}%"
            if pd.notnull(last_row['單季ROA%_近四季同業平均']) else "無資料"
        )
        last4_sum_str = (
            f"{last_row['近四季累積ROA%_同業平均']:.2f}%"
            if pd.notnull(last_row['近四季累積ROA%_同業平均']) else "無資料"
        )
    else:
        latest_mean_str = last4_mean_str = last4_sum_str = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(series):
        s = series.dropna()
        if s.empty:
            return [0, 1]
        ymin = float(s.min())
        ymax = float(s.max())
        if ymin == ymax:
            return [ymin - 2, ymax + 2]
        return [ymin - 2, ymax + 2]
    
    y_range = _get_y_range(pd.concat([
        df_stock['單季ROA%'], df_industry['單季ROA%_同業平均']
    ], ignore_index=True))
    y_range2 = _get_y_range(pd.concat([
        df_stock['單季ROA%_近四季平均'], df_industry['單季ROA%_近四季同業平均']
    ], ignore_index=True))

    # === 7. 繪圖 ===
    # table
    table_data = (
        df_stock[['年度-季度', '單季ROA%']]
        .dropna()
        .set_index('年度-季度').T
    )
    table = ff.create_table(table_data.round(2), height_constant=30)
    table.update_layout(
        title=f"{stock_id} {stock_name} 單季ROA%",
        width=1000, height=200
    )

    # 圖1：單季資產負債比%
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['單季ROA%'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_stock['單季ROA%']],
        textposition='top center',
        name="單季ROA%-個股"
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['單季ROA%_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_industry['單季ROA%_同業平均']],
        textposition='top center',
        name="單季ROA%-同業平均"
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度單季ROA%｜同業最新一季平均：{latest_mean_str}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='單季ROA%', range=y_range),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))


    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['單季ROA%_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='orange', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_stock['單季ROA%_近四季平均']],
        textposition='top center',
        name="近四季ROA%-個股"
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['單季ROA%_近四季同業平均'],
        mode='lines+markers+text',
        line=dict(color='orange', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_industry['單季ROA%_近四季同業平均']],
        textposition='top center',
        name="近四季ROA%-同業平均"
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均ROA趨勢%｜同業最新近四季平均：{last4_mean_str}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季ROA%', range=y_range2),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    
    
    # 圖3：近四季累積
    if ('近四季累積ROA%' not in df_bs_ci_cfs.columns or 
        '近四季累積ROA%_同業平均' not in df_bs_ci_cfs.columns):
        raise ValueError('缺少「近四季累積ROA%」或「近四季累積ROA%_同業平均」欄位！')

    df_stock['近四季累積ROA%'] = pd.to_numeric(df_stock['近四季累積ROA%'], errors='coerce')
    df_industry['近四季累積ROA%_同業平均'] = pd.to_numeric(df_industry['近四季累積ROA%_同業平均'], errors='coerce')

    y_range3 = _get_y_range(pd.concat([
        df_stock['近四季累積ROA%'], df_industry['近四季累積ROA%_同業平均']
    ], ignore_index=True))

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['近四季累積ROA%'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_stock['近四季累積ROA%']],
        textposition='top center',
        name="近四季累積ROA%-個股"
    ))
    fig3.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['近四季累積ROA%_同業平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_industry['近四季累積ROA%_同業平均']],
        textposition='top center',
        name="近四季累積ROA%-同業平均"
    ))
    fig3.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季累積ROA趨勢%｜同業最新近四季累積：{last4_sum_str}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季累積ROA%', range=y_range3),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))


    # === 8. 精簡 df ===
    keep_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '單季ROA%', '單季ROA%_同業平均',
        '單季ROA%_近四季平均', '單季ROA%_近四季同業平均',
        '近四季累積ROA%', '近四季累積ROA%_同業平均'
    ]
    df_roa = df_stock[keep_cols].reset_index(drop=True)

    return table, fig, fig2, fig3, df_roa



# table, fig, fig2, fig3, df_roa = plotly_roa(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# table.show() 
# fig.show()
# fig2.show()
# fig3.show()
# display(df_roa)



#%%
# 綜合損益表
# 016 包成def
# 財報三率
# 銀行業ok、有些繼續營業單位稅前損益要改、淨收益要改


def plotly_3_rate(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '毛利率%', '毛利率%_同業平均', '毛利率%_近四季平均', '毛利率%_近四季同業平均',
        '營益率%', '營益率%_同業平均', '營益率%_近四季平均', '營益率%_近四季同業平均',
        '費用率%', '費用率%_同業平均', '費用率%_近四季平均', '費用率%_近四季同業平均',
        '淨利率%', '淨利率%_同業平均', '淨利率%_近四季平均', '淨利率%_近四季同業平均',
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['毛利率%_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        latest_gross = f"{last['毛利率%_同業平均']:.2f}%"
        latest_op = f"{last['營益率%_同業平均']:.2f}%"
        latest_exp = f"{last['費用率%_同業平均']:.2f}%"
        latest_int = f"{last['淨利率%_同業平均']:.2f}%"
    else:
        latest_gross = latest_op = latest_exp = latest_int = "無資料"
        
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        late4_gross = f"{last['毛利率%_近四季同業平均']:.2f}%"
        late4_op = f"{last['營益率%_近四季同業平均']:.2f}%"
        late4_exp = f"{last['費用率%_近四季同業平均']:.2f}%"
        late4_int = f"{last['淨利率%_近四季同業平均']:.2f}%"
    else:
        late4_gross = late4_op = late4_exp = late4_int = "無資料"


    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        gap = (ymax - ymin) * 0.08 if ymax > ymin else 1
        return [ymin - 5, ymax + 5]

    # === 7. 繪圖 ===

    # table
    lastN = min(len(df_stock), 12)
    table_data = df_stock[['年度-季度', '毛利率%', '營益率%', '費用率%', '淨利率%']].tail(lastN).T.reset_index()
    table_data.columns = table_data.iloc[0]
    table_data = table_data.iloc[1:]
    fig_table = ff.create_table(table_data, height_constant=30)
    fig_table.update_layout(title='單季財報三率', width=1000, height=200)

    # 圖1：單季 bar+scatter (含同業平均)
    y_range = _get_y_range(
        df_stock['毛利率%'], df_stock['費用率%'], df_stock['營益率%'], df_stock['淨利率%'],
        df_industry['毛利率%_同業平均'], df_industry['費用率%_同業平均'], df_industry['營益率%_同業平均'], df_industry['淨利率%_同業平均']
    )

    # 圖1： bar+scatter (含同業平均)
    y_range = _get_y_range(
        df_stock['毛利率%'], df_stock['費用率%'],
        df_stock['營益率%'], df_stock['淨利率%'],
        df_industry['毛利率%_同業平均'], df_industry['費用率%_同業平均'],
        df_industry['營益率%_同業平均'], df_industry['淨利率%_同業平均']
    )
    fig = go.Figure()
    # bar 個股
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['毛利率%'],
        name='毛利率%-個股', width=0.2, marker=dict(color='blue')
    ))
    # bar 同業
    fig.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['毛利率%_同業平均'],
        name='毛利率%-同業平均', width=0.2, marker=dict(color='red')
    ))
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['費用率%'],
        name='費用率%-個股', width=0.2, marker=dict(color='deepskyblue')
    ))
    # bar 同業
    fig.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['費用率%_同業平均'],
        name='費用率%-同業平均', width=0.2, marker=dict(color='pink')
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['營益率%'],
        mode='lines+markers', name='營益率%-個股',
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營益率%']],
        line=dict(color='mediumturquoise', width=2), yaxis='y2'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['營益率%_同業平均'],
        mode='lines+markers', name='營益率%-同業平均', line=dict(color='mediumturquoise', dash='dot', width=2), yaxis='y2',
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['營益率%_同業平均']],
        textposition='top center'
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['淨利率%'],
        mode='lines+markers', name='淨利率%-個股',
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['淨利率%']],
        line=dict(color='orange', width=2), yaxis='y2'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['淨利率%_同業平均'],
        mode='lines+markers', name='淨利率%-同業平均', line=dict(color='orange', dash='dot', width=2), yaxis='y2',
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['淨利率%_同業平均']],
        textposition='top center'
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度 財報三率、費用率<br>\
同業最新一季平均：毛利{latest_gross} 費用{latest_exp} 營益{latest_op} 淨利{latest_int}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='毛利率%、費用率%', range=y_range, side='left', showgrid=True),
        yaxis2=dict(title='營益率%、淨利率%', overlaying='y', side='right', showgrid=False),
        barmode='group',
        width=1000, height=450,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

 
    # 圖2：近四季平均 bar+scatter (含同業平均)
    y_range2 = _get_y_range(
        df_stock['毛利率%_近四季平均'], df_stock['費用率%_近四季平均'],
        df_stock['營益率%_近四季平均'], df_stock['淨利率%_近四季平均'],
        df_industry['毛利率%_近四季同業平均'], df_industry['費用率%_近四季同業平均'],
        df_industry['營益率%_近四季同業平均'], df_industry['淨利率%_近四季同業平均']
    )
    fig2 = go.Figure()
    # bar 個股
    fig2.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['毛利率%_近四季平均'],
        name='近四季平均毛利率%-個股', width=0.2, marker=dict(color='blue')
    ))
    # bar 同業
    fig2.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['毛利率%_近四季同業平均'],
        name='近四季平均毛利率%-同業平均', width=0.2, marker=dict(color='red')
    ))
    fig2.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['費用率%_近四季平均'],
        name='近四季平均費用率%-個股', width=0.2, marker=dict(color='deepskyblue')
    ))
    # bar 同業
    fig2.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['費用率%_近四季同業平均'],
        name='近四季平均費用率%-同業平均', width=0.2, marker=dict(color='pink')
    ))
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['營益率%_近四季平均'],
        mode='lines+markers', name='近四季平均營益率%-個股',
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營益率%_近四季平均']],
        line=dict(color='mediumturquoise', width=2), yaxis='y2'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['營益率%_近四季同業平均'],
        mode='lines+markers', name='近四季平均營益率%-同業平均', line=dict(color='mediumturquoise', dash='dot', width=2), yaxis='y2',
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['營益率%_近四季同業平均']],
        textposition='top center'
    ))
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['淨利率%_近四季平均'],
        mode='lines+markers', name='近四季平均淨利率%-個股',
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['淨利率%_近四季平均']],
        line=dict(color='orange', width=2), yaxis='y2'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['淨利率%_近四季同業平均'],
        mode='lines+markers', name='近四季平均淨利率%-同業平均', line=dict(color='orange', dash='dot', width=2), yaxis='y2',
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['淨利率%_近四季同業平均']],
        textposition='top center'
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均 財報三率、費用率<br>\
同業最新近四季平均 : 毛利{late4_gross} 費用{late4_exp} 營益{late4_op} 淨利{late4_int}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季平均毛利率%、費用率%', range=y_range2, side='left', showgrid=True),
        yaxis2=dict(title='近四季平均營益率%、淨利率%', overlaying='y', side='right', showgrid=False),
        barmode='group',
        width=1000, height=450,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # === 8. 精簡 df ===
    df_out = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '毛利率%', '毛利率%_同業平均', '毛利率%_近四季平均', '毛利率%_近四季同業平均',
        '營益率%', '營益率%_同業平均', '營益率%_近四季平均', '營益率%_近四季同業平均',
        '費用率%', '費用率%_同業平均', '費用率%_近四季平均', '費用率%_近四季同業平均',
        '淨利率%', '淨利率%_同業平均', '淨利率%_近四季平均', '淨利率%_近四季同業平均',
    ]]

    return fig_table, fig, fig2, df_out


# fig_table, fig, fig2, df_out = plotly_3_rate(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig_table.show()
# fig.show()
# fig2.show()
# display(df_out)


#%%
# 017 包成def
# 經營安全邊際 (越高，抵抗景氣波動能力越大)
# 銀行業不看


def plotly_operating_margin_of_safety(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '經營安全邊際%', '經營安全邊際%_同業平均',
        '經營安全邊際%_近四季平均', '經營安全邊際%_近四季同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')
    
    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()
    
    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')
    
    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['經營安全邊際%_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )
    
    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        last_val = f"{last['經營安全邊際%_同業平均']:.2f}%"
        last4_val = f"{last['經營安全邊際%_近四季同業平均']:.2f}%"
    else:
        last_val = last4_val = "無資料"
    
    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        return [ymin - 100, ymax + 100]
    
    # === 7. 繪圖 ===
    # 圖1：單季
    y_range = _get_y_range(
        df_stock['經營安全邊際%'],
        df_industry['經營安全邊際%_同業平均']
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['經營安全邊際%'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        marker_color=['red' if v < 50 else 'mediumturquoise' for v in df_stock['經營安全邊際%']],
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['經營安全邊際%']],
        textposition='top center',
        name='經營安全邊際%-個股'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['經營安全邊際%_同業平均'],
        mode='lines+markers',
        line=dict(color='mediumturquoise', dash='dot', width=1.5),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['經營安全邊際%_同業平均']],
        textposition='top center',
        name='經營安全邊際%-同業平均'
    ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 各季度經營安全邊際％｜同業最新一季平均 {last_val}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='經營安全邊際%', range=y_range),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    # 圖2：近四季平均
    y_range2 = _get_y_range(
        df_stock['經營安全邊際%_近四季平均'],
        df_industry['經營安全邊際%_近四季同業平均']
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['經營安全邊際%_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', width=2.5),
        marker_color=['red' if v < 50 else 'mediumturquoise' for v in df_stock['經營安全邊際%_近四季平均']],
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['經營安全邊際%_近四季平均']],
        textposition='top center',
        name='近四季平均經營安全邊際%-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['經營安全邊際%_近四季同業平均'],
        mode='lines+markers',
        line=dict(color='deepskyblue', dash='dot', width=1.5),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['經營安全邊際%_近四季同業平均']],
        textposition='top center',
        name='近四季平均經營安全邊際%-同業平均'
    ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均經營安全邊際%｜同業最新近四季平均 {last4_val}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季平均經營安全邊際%', range=y_range2),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    # === 8. 精簡 df ===
    df_omos = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '經營安全邊際%', '經營安全邊際%_同業平均', '經營安全邊際%_近四季平均', '經營安全邊際%_近四季同業平均'
    ]]

    return fig, fig2, df_omos


# fig, fig2, df_omos = plotly_operating_margin_of_safety(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_omos)


#%%
# 018 包成def
# 營收、盈餘、營益率比較
# 銀行業ok、有些繼續營業單位稅前損益要改、淨收益要改

def plotly_year_revenue(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準本期淨利淨損', '標準本期淨利淨損_同業平均', '標準本期淨利淨損_近四季平均', '標準本期淨利淨損_近四季同業平均',
        '標準營業收入合計', '標準營業收入合計_同業平均', '標準營業收入合計_近四季平均', '標準營業收入合計_近四季同業平均',
        '營益率%', '營益率%_同業平均', '營益率%_近四季平均', '營益率%_近四季同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['標準營業收入合計_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        last_revenue = f"{last['標準營業收入合計_同業平均'] / 1e8:.2f}億"
        last_ni = f"{last['標準本期淨利淨損_同業平均'] / 1e8:.2f}億"
        last_opm = f"{last['營益率%_同業平均']:.2f}%"
        last4_revenue = f"{last['標準營業收入合計_近四季同業平均'] / 1e8:.2f}億"
        last4_ni = f"{last['標準本期淨利淨損_近四季同業平均'] / 1e8:.2f}億"
        last4_opm = f"{last['營益率%_近四季同業平均']:.2f}%"
    else:
        last_revenue = last_ni = last_opm = last4_revenue = last4_ni = last4_opm = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        gap = (ymax - ymin) * 0.1 if ymax > ymin else 1
        return [ymin - gap, ymax + gap]

    # === 7. 繪圖 ===
    # 圖1：單季 (營收 稅後淨利用bar，營益率用scatter)
    y_range = _get_y_range(
        df_stock['標準營業收入合計'], df_stock['標準本期淨利淨損'],
        df_industry['標準營業收入合計_同業平均'], df_industry['標準本期淨利淨損_同業平均']
    )
    y_range_opm = _get_y_range(
        df_stock['營益率%'], df_industry['營益率%_同業平均']
    )

    import plotly.graph_objs as go
    fig = go.Figure()
    # 營收
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['標準營業收入合計'],
        name='營收-個股', width=0.21, marker=dict(color='blue')
    ))
    fig.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['標準營業收入合計_同業平均'],
        name='營收-同業平均', width=0.21, marker=dict(color='red')
    ))
    # 稅後淨利
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['標準本期淨利淨損'],
        name='稅後淨利-個股', width=0.21, marker=dict(color='deepskyblue')
    ))
    fig.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['標準本期淨利淨損_同業平均'],
        name='稅後淨利-同業平均', width=0.21, marker=dict(color='pink')
    ))
    # 營益率（右軸）
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['營益率%'],
        mode='lines+markers+text', name='營益率%-個股',
        line=dict(color='mediumturquoise', width=1.4),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營益率%']],
        textposition='top center',
        yaxis='y2'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['營益率%_同業平均'],
        mode='lines+markers', name='營益率%-同業平均',
        line=dict(color='mediumturquoise', dash='dot', width=1.4),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['營益率%_同業平均']],
        textposition='top center',
        yaxis='y2'
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度 營收/稅後淨利/營益率<br>\
同業最新一季平均: 營收{last_revenue} 稅後淨利{last_ni} 營益率{last_opm}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='金額', range=y_range, side='left', showgrid=True),
        yaxis2=dict(title='營益率%', overlaying='y', side='right', range=y_range_opm, showgrid=False),
        barmode='group', width=1000, height=450,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖2：近四季平均
    y_range2 = _get_y_range(
        df_stock['標準營業收入合計_近四季平均'], df_stock['標準本期淨利淨損_近四季平均'],
        df_industry['標準營業收入合計_近四季同業平均'], df_industry['標準本期淨利淨損_近四季同業平均']
    )
    y_range2_opm = _get_y_range(
        df_stock['營益率%_近四季平均'], df_industry['營益率%_近四季同業平均']
    )
    fig2 = go.Figure()
    # 營收
    fig2.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['標準營業收入合計_近四季平均'],
        name='近四季平均營收-個股', width=0.21, marker=dict(color='blue')
    ))
    fig2.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['標準營業收入合計_近四季同業平均'],
        name='近四季平均營收-同業平均', width=0.21, marker=dict(color='red')
    ))
    # 稅後淨利
    fig2.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['標準本期淨利淨損_近四季平均'],
        name='近四季平均稅後淨利-個股', width=0.21, marker=dict(color='deepskyblue')
    ))
    fig2.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['標準本期淨利淨損_近四季同業平均'],
        name='近四季平均稅後淨利-同業平均', width=0.21, marker=dict(color='pink')
    ))
    # 營益率（右軸）
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['營益率%_近四季平均'],
        mode='lines+markers+text', name='近四季平均營益率%-個股',
        line=dict(color='mediumturquoise', width=2),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營益率%_近四季平均']],
        textposition='top center',
        yaxis='y2'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['營益率%_近四季同業平均'],
        mode='lines+markers', name='近四季平均營益率%-同業平均',
        line=dict(color='mediumturquoise', dash='dot', width=1.8),
        text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_industry['營益率%_近四季同業平均']],
        textposition='top center',
        yaxis='y2'
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均 營收/稅後淨利/營益率<br>\
同業最新近四季平均: 營收{last4_revenue} 稅後淨利{last4_ni} 營益率{last4_opm}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='金額', range=y_range2, side='left', showgrid=True),
        yaxis2=dict(title='營益率%', overlaying='y', side='right', range=y_range2_opm, showgrid=False),
        barmode='group', width=1000, height=450,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # === 8. 精簡 df ===
    df_year_revenue = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '標準營業收入合計', '標準營業收入合計_同業平均', '標準營業收入合計_近四季平均', '標準營業收入合計_近四季同業平均',
        '標準本期淨利淨損', '標準本期淨利淨損_同業平均', '標準本期淨利淨損_近四季平均', '標準本期淨利淨損_近四季同業平均',
        '營益率%', '營益率%_同業平均', '營益率%_近四季平均', '營益率%_近四季同業平均'
    ]]

    return fig, fig2, df_year_revenue


# fig, fig2, df_year_revenue = plotly_year_revenue(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_year_revenue)


#%%
# 019 包成def
# 營收成長率 Revenue Growth Rate
# 季
# ocf成長率>營收成長率、營益率成長率>營收成長率、稅後淨利成長率>營收成長率
# 存貨成長率<(營收成長率/2)
# bs -> cfs -> is
# 銀行業ok

def plotly_growth_rates(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        # 圖1 2
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '營業收入成長率%', '營業收入成長率%_同業平均', '營業收入成長率%_近四季平均', '營業收入成長率%_近四季同業平均', 
        '營業利益成長率%', '營業利益成長率%_同業平均', '營業利益成長率%_近四季平均', '營業利益成長率%_近四季同業平均',
        '標準營業活動現金流成長率%', '標準營業活動現金流成長率%_同業平均', '標準營業活動現金流成長率%_近四季平均', '標準營業活動現金流成長率%_近四季同業平均',
        '淨利成長率%', '淨利成長率%_同業平均', '淨利成長率%_近四季平均', '淨利成長率%_近四季同業平均',
        # 圖3 4
        '存貨成長率%', '存貨成長率%_同業平均', '存貨成長率%_近四季平均', '存貨成長率%_近四季同業平均',
        '營業收入成長率%_50%','營業收入成長率%_50%_同業平均','營業收入成長率%_50%_近四季平均', '營業收入成長率%_50%_近四季同業平均',
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['營業收入成長率%_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
   

    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        gap = (ymax - ymin) * 0.08 if ymax > ymin else 1
        return [ymin - 100, ymax + 100]

    def _get_y_range_2(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        gap = (ymax - ymin) * 0.08 if ymax > ymin else 1
        return [ymin - 10, ymax + 10]

    # === 7. 繪圖 ===

    # 圖1：單季成長率
    y_range1 = _get_y_range(
        df_stock['營業收入成長率%'], df_stock['營業利益成長率%'], df_stock['標準營業活動現金流成長率%'], df_stock['淨利成長率%']
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['營業收入成長率%'], mode='lines+markers', name='營業收入成長率%', line=dict(color='blue'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營業收入成長率%']]))
    fig.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['營業利益成長率%'], mode='lines+markers', name='營業利益成長率%', line=dict(color='orange'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營業利益成長率%']]))
    fig.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['標準營業活動現金流成長率%'], mode='lines+markers', name='營業活動現金流成長率%', line=dict(color='green'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['標準營業活動現金流成長率%']]))
    fig.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['淨利成長率%'], mode='lines+markers', name='淨利成長率%', line=dict(color='red'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['淨利成長率%']]))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度成長率",
        xaxis=dict(title='年度-季度'), yaxis=dict(title='單季成長率%', range=y_range1), width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖1_2：單季成長率
    y_range1_2 = _get_y_range(
        df_industry['營業收入成長率%_同業平均'], df_industry['營業利益成長率%_同業平均'], df_industry['標準營業活動現金流成長率%_同業平均'], df_industry['淨利成長率%_同業平均']
    )
    fig1_2 = go.Figure()
    # 同業平均
    fig1_2.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['營業收入成長率%_同業平均'], mode='lines+markers', name='營業收入成長率%-同業平均', line=dict(color='blue', dash='dot')))
    fig1_2.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['營業利益成長率%_同業平均'], mode='lines+markers', name='營業利益成長率%-同業平均', line=dict(color='orange', dash='dot')))
    fig1_2.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['標準營業活動現金流成長率%_同業平均'], mode='lines+markers', name='營業活動現金流成長率%-同業平均', line=dict(color='green', dash='dot')))
    fig1_2.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['淨利成長率%_同業平均'], mode='lines+markers', name='淨利成長率%-同業平均', line=dict(color='red', dash='dot')))
    fig1_2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 同業各季度平均成長率",
        xaxis=dict(title='年度-季度'), yaxis=dict(title='單季成長率%', range=y_range1_2), width=900, height=350, 
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    
    # 圖2：近四季平均成長率
    y_range2 = _get_y_range(
        df_stock['營業收入成長率%_近四季平均'], df_stock['營業利益成長率%_近四季平均'], df_stock['標準營業活動現金流成長率%_近四季平均'], df_stock['淨利成長率%_近四季平均'],
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['營業收入成長率%_近四季平均'], mode='lines+markers', name='營業收入成長率%-近四季平均', line=dict(color='blue'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營業收入成長率%_近四季平均']]))
    fig2.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['營業利益成長率%_近四季平均'], mode='lines+markers', name='營業利益成長率%-近四季平均', line=dict(color='orange'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營業利益成長率%_近四季平均']]))
    fig2.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['標準營業活動現金流成長率%_近四季平均'], mode='lines+markers', name='營業活動現金流成長率%-近四季平均', line=dict(color='green'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['標準營業活動現金流成長率%_近四季平均']]))
    fig2.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['淨利成長率%_近四季平均'], mode='lines+markers', name='淨利成長率%-近四季平均', line=dict(color='red'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['淨利成長率%_近四季平均']]))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均成長率",
        xaxis=dict(title='年度-季度'), yaxis=dict(title='近四季平均成長率%', range=y_range2), width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    

    # 圖2_2：近四季平均成長率
    y_range2_2 = _get_y_range(
        df_industry['營業收入成長率%_近四季同業平均'], df_industry['營業利益成長率%_近四季同業平均'], df_industry['標準營業活動現金流成長率%_近四季同業平均'], df_industry['淨利成長率%_近四季同業平均'],
    )
    fig2_2 = go.Figure()
    # 同業平均
    fig2_2.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['營業收入成長率%_近四季同業平均'], mode='lines+markers', name='營業收入成長率%-近四季同業平均', line=dict(color='blue', dash='dot')))
    fig2_2.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['營業利益成長率%_近四季同業平均'], mode='lines+markers', name='營業利益成長率%-近四季同業平均', line=dict(color='orange', dash='dot')))
    fig2_2.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['標準營業活動現金流成長率%_近四季同業平均'], mode='lines+markers', name='營業活動現金流成長率%-近四季同業平均', line=dict(color='green', dash='dot')))
    fig2_2.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['淨利成長率%_近四季同業平均'], mode='lines+markers', name='淨利成長率%-近四季同業平均', line=dict(color='red', dash='dot')))
    fig2_2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 同業近四季平均成長率",
        xaxis=dict(title='年度-季度'), yaxis=dict(title='近四季平均成長率%', range=y_range2_2), width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖3：單季-存貨/營收成長率
    y_range3 = _get_y_range_2(
        df_stock['存貨成長率%'], df_stock['營業收入成長率%_50%'],
        df_industry['存貨成長率%_同業平均'], df_industry['營業收入成長率%_50%_同業平均']
    )
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['存貨成長率%'], mode='lines+markers', name='存貨成長率%', line=dict(color='purple'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['存貨成長率%']]))
    fig3.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['存貨成長率%_同業平均'], mode='lines+markers', name='存貨成長率%-同業平均', line=dict(color='purple', dash='dot')))
    fig3.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['營業收入成長率%_50%'], mode='lines+markers', name='50% 營收成長率', line=dict(color='orange'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營業收入成長率%_50%']]))
    fig3.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['營業收入成長率%_50%_同業平均'], mode='lines+markers', name='50% 營收成長率-同業平均', line=dict(color='orange', dash='dot')))
    fig3.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 存貨/營收成長率",
        xaxis=dict(title='年度-季度'), yaxis=dict(title='單季成長率%', range=y_range3), width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖4：近四季平均-存貨/營收成長率
    y_range4 = _get_y_range_2(
        df_stock['存貨成長率%_近四季平均'], df_stock['營業收入成長率%_50%_近四季平均'],
        df_industry['存貨成長率%_近四季同業平均'], df_industry['營業收入成長率%_50%_近四季同業平均']
    )
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['存貨成長率%_近四季平均'], mode='lines+markers', name='存貨成長率%-近四季平均', line=dict(color='purple'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['存貨成長率%_近四季平均']]))
    fig4.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['存貨成長率%_近四季同業平均'], mode='lines+markers', name='存貨成長率%-近四季同業平均', line=dict(color='purple', dash='dot')))
    fig4.add_trace(go.Scatter(x=df_stock['年度-季度'], y=df_stock['營業收入成長率%_50%_近四季平均'], mode='lines+markers', name='50% 營收成長率-近四季平均', line=dict(color='orange'), text=[f"{v:.2f}%" if not pd.isnull(v) else "" for v in df_stock['營業收入成長率%_50%_近四季平均']]))
    fig4.add_trace(go.Scatter(x=df_industry['年度-季度'], y=df_industry['營業收入成長率%_50%_近四季同業平均'], mode='lines+markers', name='50% 營收成長率-近四季同業平均', line=dict(color='orange', dash='dot')))
    fig4.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 同業近四季平均存貨/營收成長率",
        xaxis=dict(title='年度-季度'), yaxis=dict(title='近四季平均成長率%', range=y_range4), width=900, height=350, 
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # === 8. 精簡 df ===
    df_growth_rates = df_stock[must_cols]

    return fig, fig1_2, fig2, fig2_2, fig3, fig4, df_growth_rates



# fig, fig1_2, fig2, fig2_2, fig3, fig4, df_growth_rates = plotly_growth_rates(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig1_2.show()
# fig2.show()
# fig2_2.show()
# fig3.show()
# fig4.show()
# display(df_growth_rates)



#%%
# 020 包成def
# 業內、業外
# 銀行業不看

def plotly_non_operating_earnings(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '本業比率', '本業比率_同業平均', '本業比率_近四季平均', '本業比率_近四季同業平均',
        '業外比率', '業外比率_同業平均', '業外比率_近四季平均', '業外比率_近四季同業平均',
        '業外貢獻比', '業外貢獻比_同業平均', '業外貢獻比_近四季平均', '業外貢獻比_近四季同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[df_bs_ci_cfs['產業類別提取'] == stock_industry].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['本業比率_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        latest_op = f"{last['本業比率_同業平均']:.2f}"
        latest_nonop = f"{last['業外比率_同業平均']:.2f}"
        latest_contrib = f"{last['業外貢獻比_同業平均']:.2f}"
    else:
        latest_op = latest_nonop = latest_contrib = "無資料"
        
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        late4_op = f"{last['本業比率_近四季同業平均']:.2f}"
        late4_nonop = f"{last['業外比率_近四季同業平均']:.2f}"
        late4_contrib = f"{last['業外貢獻比_近四季同業平均']:.2f}"
    else:
        late4_op = late4_nonop = late4_contrib = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [-1, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        return [ymin - 1, ymax + 1]
    
    # === 7. 繪圖 ===

    # 圖1：單季 (bar 本業比率 業外比率 scatter 業外貢獻比）
    # y_range = _get_y_range(
    #     df_stock['本業比率'], df_stock['業外比率'], df_stock['業外貢獻比'],
    #     df_industry['本業比率_同業平均'], df_industry['業外比率_同業平均'], df_industry['業外貢獻比_同業平均']
    # )
    
    fig = go.Figure()
    
    # bar 個股
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['本業比率'],
        name='本業比率-個股', width=0.2, marker=dict(color='blue'),
        # offsetgroup='A',  # 同一 offsetgroup 會疊一起
        # base=0
    ))
    fig.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['本業比率_同業平均'],
        name='本業比率-同業平均', width=0.2, marker=dict(color='red'),
        # offsetgroup='B',
        # base=0
    ))
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['業外比率'],
        name='業外比率-個股', width=0.2, marker=dict(color='deepskyblue'),
        # offsetgroup='A',
        # base=df_stock['本業比率']  
    ))
    fig.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['業外比率_同業平均'],
        name='業外比率-同業平均', width=0.2, marker=dict(color='pink'),
        # offsetgroup='B',
        # base=df_industry['本業比率_同業平均']
    ))
    # scatter
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['業外貢獻比'],
        mode='lines+markers+text', name='業外貢獻比-個股',
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_stock['業外貢獻比']],
        line=dict(color='mediumturquoise', width=2), yaxis='y2'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['業外貢獻比_同業平均'],
        mode='lines+markers', name='業外貢獻比-同業平均',
        line=dict(color='mediumturquoise', dash='dot', width=2), yaxis='y2',
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['業外貢獻比_同業平均']],
        textposition='top center'
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 各季度本業/業外/業外貢獻比<br>\
同業最新一季平均：本業{latest_op} 業外{latest_nonop}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='本業/業外比率', side='left', showgrid=True),
        yaxis2=dict(title='業外貢獻比', overlaying='y', side='right', showgrid=False),
        barmode='group',
        width=1000, height=450,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖2：近四季平均
    y_range2 = _get_y_range(
        df_stock['本業比率_近四季平均'], df_stock['業外比率_近四季平均'], df_stock['業外貢獻比_近四季平均'],
        df_industry['本業比率_近四季同業平均'], df_industry['業外比率_近四季同業平均'], df_industry['業外貢獻比_近四季同業平均']
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['本業比率_近四季平均'],
        name='近四季平均本業比率-個股', width=0.2, marker=dict(color='blue')
    ))
    fig2.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['本業比率_近四季同業平均'],
        name='近四季平均本業比率-同業平均', width=0.2, marker=dict(color='red')
    ))
    fig2.add_trace(go.Bar(
        x=df_stock['年度-季度'], y=df_stock['業外比率_近四季平均'],
        name='近四季平均業外比率-個股', width=0.2, marker=dict(color='deepskyblue')
    ))
    fig2.add_trace(go.Bar(
        x=df_industry['年度-季度'], y=df_industry['業外比率_近四季同業平均'],
        name='近四季平均業外比率-同業平均', width=0.2, marker=dict(color='pink')
    ))
    # scatter
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'], y=df_stock['業外貢獻比_近四季平均'],
        mode='lines+markers+text', name='近四季平均業外貢獻比-個股',
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_stock['業外貢獻比_近四季平均']],
        line=dict(color='mediumturquoise', width=2), yaxis='y2'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'], y=df_industry['業外貢獻比_近四季同業平均'],
        mode='lines+markers', name='近四季平均業外貢獻比-同業平均',
        line=dict(color='mediumturquoise', dash='dot', width=2), yaxis='y2',
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['業外貢獻比_近四季同業平均']],
        textposition='top center'
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均本業/業外/業外貢獻比<br>\
同業最新近四季平均：本業{late4_op} 業外{late4_nonop}",
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='本業/業外比率', side='left', showgrid=True),
        yaxis2=dict(title='業外貢獻比', overlaying='y', side='right', showgrid=False),
        barmode='group',
        width=1000, height=450,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # === 8. 精簡 df ===
    df_non_operating_earnings = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '本業比率', '本業比率_同業平均', '本業比率_近四季平均', '本業比率_近四季同業平均',
        '業外比率', '業外比率_同業平均', '業外比率_近四季平均', '業外比率_近四季同業平均',
        '業外貢獻比', '業外貢獻比_同業平均', '業外貢獻比_近四季平均', '業外貢獻比_近四季同業平均'
    ]]

    return fig, fig2, df_non_operating_earnings


# fig, fig2, df_non_operating_earnings = plotly_non_operating_earnings(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_non_operating_earnings)



#%%
# 010 包成def
# 賦稅優勢
# 銀行業ok、有些繼續營業單位稅前損益要改 


def plotly_tax_advantage(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '賦稅優勢', '賦稅優勢_同業平均', '近四季平均賦稅優勢', '近四季平均賦稅優勢_同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')
    
    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[(df_bs_ci_cfs['產業類別提取'] == stock_industry)].copy()
    
    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')
    
    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['賦稅優勢_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )
    
    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        latest_avg = f"{last['賦稅優勢_同業平均']:.2f}"
        late4_avg = f"{last['近四季平均賦稅優勢_同業平均']:.2f}"
    else:
        latest_avg = "無資料"
        late4_avg = "無資料"
    
    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [0, 1]
        ymin = float(vals.min())
        ymax = float(vals.max())
        return [ymin - 0.5, ymax + 0.5]
    
    y_range = _get_y_range(
        df_stock['賦稅優勢'],
        df_industry['賦稅優勢_同業平均']
    )
    y_range2 = _get_y_range(
        df_stock['近四季平均賦稅優勢'],
        df_industry['近四季平均賦稅優勢_同業平均']
    )
    
    # === 7. 繪圖 ===
    # 圖1：單季
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['賦稅優勢'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_stock['賦稅優勢']],
        textposition='top center',
        name='賦稅優勢-個股'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['賦稅優勢_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['賦稅優勢_同業平均']],
        textposition='top center',
        name='賦稅優勢-同業平均'
    ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 各季度賦稅優勢 | 同業最新一季 {latest_avg}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='賦稅優勢', range=y_range),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    
    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['近四季平均賦稅優勢'],
        mode='lines+markers+text',
        line=dict(color='orange', width=2.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_stock['近四季平均賦稅優勢']],
        textposition='top center',
        name='近四季平均賦稅優勢-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['近四季平均賦稅優勢_同業平均'],
        mode='lines+markers+text',
        line=dict(color='orange', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['近四季平均賦稅優勢_同業平均']],
        textposition='top center',
        name='近四季平均賦稅優勢-同業平均'
    ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均賦稅優勢 | 同業最新近四季平均 {late4_avg}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='近四季平均賦稅優勢', range=y_range2),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )
    
    # === 8. 精簡 df ===
    df_tax = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '賦稅優勢', '賦稅優勢_同業平均', '近四季平均賦稅優勢', '近四季平均賦稅優勢_同業平均'
    ]]
    return fig, fig2, df_tax



# fig, fig2, df_tax = plotly_tax_advantage(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_tax)


#%%
# 001 包成def OK
# 資產負債比率 Debt to Asset Ratio

def plotly_debt_to_asset_ratio_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    """
    直接使用 df_bs_ci_cfs 的四個欄位：
      - 資產負債比%
      - 資產負債比%_同業平均
      - 資產負債比%_近四季平均
      - 資產負債比%_近四季同業平均
    產出兩張圖（單季與近四季平均），以及回傳個股/同業摘要df。
    """

    # === 1. 取要的欄位 ===
    must_cols = ['標題','股票代號','產業類別提取','年度-季度',
                 '資產負債比%','資產負債比%_同業平均',
                 '資產負債比%_近四季平均','資產負債比%_近四季同業平均']
    for c in must_cols:
        if c not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{c}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[
        (df_bs_ci_cfs['產業類別提取'] == stock_industry) &
        (df_bs_ci_cfs['標題'].astype(str).str.endswith('金額'))
    ].copy()

    # === 3. 個股資料 ===
    df_stock = base[(base['股票代號'].astype(str) == str(stock_id))].copy()
    df_stock = df_stock.sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.sort_values('年度-季度')
            .dropna(subset=['資產負債比%_同業平均'], how='all')
            .drop_duplicates(subset=['年度-季度'], keep='last')
            [['年度-季度','資產負債比%_同業平均','資產負債比%_近四季同業平均']]
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last_row = df_industry.iloc[-1]
        latest_industry_mean_str = (
            f"{last_row['資產負債比%_同業平均']:.2f}%" 
            if pd.notnull(last_row['資產負債比%_同業平均']) else "無資料"
        )
        last4_avg_str = (
            f"{last_row['資產負債比%_近四季同業平均']:.2f}%" 
            if pd.notnull(last_row['資產負債比%_近四季同業平均']) else "無資料"
        )
    else:
        latest_industry_mean_str = "無資料"
        last4_avg_str = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(series):
        """自動回傳該 series 的 y 軸範圍，min-3 ~ max+3"""
        s = series.dropna()
        if s.empty:
            return [0, 1]
        ymin = float(s.min())
        ymax = float(s.max())
        if ymin == ymax:
            # 單一值時給一點緩衝
            return [ymin - 6, ymax + 6]
        return [ymin - 6, ymax + 6]

    y_range  = _get_y_range(pd.concat([
        df_stock['資產負債比%'],
        df_industry['資產負債比%_同業平均']
    ], ignore_index=True))

    y_range2 = _get_y_range(pd.concat([
        df_stock['資產負債比%_近四季平均'],
        df_industry['資產負債比%_近四季同業平均']
    ], ignore_index=True))

    # === 7. 繪圖 ===
    # 圖1：單季資產負債比%
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['資產負債比%'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        marker=dict(
            color=['red' if (pd.notnull(v) and v > 55) else 'mediumturquoise' 
                   for v in df_stock['資產負債比%']],
            size=8
        ),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_stock['資產負債比%']],
        textposition='top center',
        name="資產負債比%-個股"
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['資產負債比%_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_industry['資產負債比%_同業平均']],
        textposition='top center',
        name="資產負債比%-同業平均"
    ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 各季度資產負債比率％｜同業最新一季平均：{latest_industry_mean_str}',
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='資產負債比%', range=y_range),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['資產負債比%_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', width=2.5),
        marker=dict(
            color=['red' if (pd.notnull(v) and v > 55) else 'deepskyblue'
                   for v in df_stock['資產負債比%_近四季平均']],
            size=8
        ),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_stock['資產負債比%_近四季平均']],
        textposition='top center',
        name="近四季平均資產負債比%-個股"
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['資產負債比%_近四季同業平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}%" if pd.notnull(v) else "" for v in df_industry['資產負債比%_近四季同業平均']],
        textposition='top center',
        name="近四季平均資產負債比%-同業平均"
    ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均資產負債比率％｜同業最新近四季平均：{last4_avg_str}',
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='近四季平均資產負債比%', range=y_range2),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # === 8. 精簡 df ===
    df_debt_to_asset_ratio = df_stock[['標題','股票代號','產業類別提取','年度-季度',
                               '資產負債比%','資產負債比%_同業平均', '資產負債比%_近四季平均', '資產負債比%_近四季同業平均']].reset_index(drop=True)

    return fig, fig2, df_debt_to_asset_ratio


# fig, fig2, df_debt_to_asset_ratio = plotly_debt_to_asset_ratio_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show() 
# fig2.show()
# display(df_debt_to_asset_ratio)



#%%
# 002 包成def OK
# 長期資金佔不動產、廠房及設備比 Ratio of liabilities to assets
# 銀行業不看
    
def plotly_long_term_capital_to_ppe_ratio_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    """
    直接用 df_bs_ci_cfs 裡四個現成欄位畫「長期資金佔不動產、廠房及設備比(倍)」及其近四季平均。
    """

    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '長期資金佔不動產廠房及設備比(倍)',
        '長期資金佔不動產廠房及設備比(倍)_同業平均',
        '長期資金佔不動產廠房及設備比(倍)_近四季平均',
        '長期資金佔不動產廠房及設備比(倍)_近四季同業平均'
    ]
    for c in must_cols:
        if c not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{c}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[
        (df_bs_ci_cfs['產業類別提取'] == stock_industry) &
        (df_bs_ci_cfs['標題'].astype(str).str.endswith('金額'))
    ].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.sort_values('年度-季度')
            .dropna(subset=['長期資金佔不動產廠房及設備比(倍)_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            [['年度-季度', '長期資金佔不動產廠房及設備比(倍)_同業平均', '長期資金佔不動產廠房及設備比(倍)_近四季同業平均']]
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last_row = df_industry.iloc[-1]
        latest_industry_mean_str = (
            f"{last_row['長期資金佔不動產廠房及設備比(倍)_同業平均']:.2f}"
            if pd.notnull(last_row['長期資金佔不動產廠房及設備比(倍)_同業平均']) else "無資料"
        )
        last4_avg_str = (
            f"{last_row['長期資金佔不動產廠房及設備比(倍)_近四季同業平均']:.2f}"
            if pd.notnull(last_row['長期資金佔不動產廠房及設備比(倍)_近四季同業平均']) else "無資料"
        )
    else:
        latest_industry_mean_str = "無資料"
        last4_avg_str = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(series):
        s = series.dropna()
        if s.empty:
            return [0, 1]
        ymin = float(s.min())
        ymax = float(s.max())
        if ymin == ymax:
            return [ymin - 3, ymax + 3]
        return [ymin - 3, ymax + 3]
        
    y_range = _get_y_range(pd.concat([
        df_stock['長期資金佔不動產廠房及設備比(倍)'],
        df_industry['長期資金佔不動產廠房及設備比(倍)_同業平均']
    ], ignore_index=True))
    y_range2 = _get_y_range(pd.concat([
        df_stock['長期資金佔不動產廠房及設備比(倍)_近四季平均'],
        df_industry['長期資金佔不動產廠房及設備比(倍)_近四季同業平均']
    ], ignore_index=True))

    # === 7. 繪圖 ===
    # 圖1：單季資產負債比%
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['長期資金佔不動產廠房及設備比(倍)'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        marker=dict(
            color=['red' if (pd.notnull(v) and v < 1.1) else 'mediumturquoise'
                   for v in df_stock['長期資金佔不動產廠房及設備比(倍)']],
            size=8
        ),
        text=[f"{v:.2f}" if pd.notnull(v) else "" for v in df_stock['長期資金佔不動產廠房及設備比(倍)']],
        textposition='top center',
        name="個股"
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['長期資金佔不動產廠房及設備比(倍)_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}" if pd.notnull(v) else "" for v in df_industry['長期資金佔不動產廠房及設備比(倍)_同業平均']],
        textposition='top center',
        name="同業平均"
    ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 各季度長期資金佔不動產、廠房及設備比｜同業最新一季平均：{latest_industry_mean_str}',
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='長期資金佔不動產廠房及設備比(倍)', range=y_range),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['長期資金佔不動產廠房及設備比(倍)_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', width=2.5),
        marker=dict(
            color=['red' if (pd.notnull(v) and v < 1.1) else 'deepskyblue'
                   for v in df_stock['長期資金佔不動產廠房及設備比(倍)_近四季平均']],
            size=8
        ),
        text=[f"{v:.2f}" if pd.notnull(v) else "" for v in df_stock['長期資金佔不動產廠房及設備比(倍)_近四季平均']],
        textposition='top center',
        name="近四季平均-個股"
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['長期資金佔不動產廠房及設備比(倍)_近四季同業平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}" if pd.notnull(v) else "" for v in df_industry['長期資金佔不動產廠房及設備比(倍)_近四季同業平均']],
        textposition='top center',
        name="近四季平均-同業平均"
    ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均長期資金佔不動產、廠房及設備比｜同業最新近四季平均：{last4_avg_str}',
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='長期資金佔不動產廠房及設備比(倍)_近四季平均', range=y_range2),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # === 8. 精簡 df ===
    df_long_term_capital_to_ppe_ratio = df_stock[['標題','股票代號','產業類別提取','年度-季度',
                               '長期資金佔不動產廠房及設備比(倍)','長期資金佔不動產廠房及設備比(倍)_近四季平均',
                               '長期資金佔不動產廠房及設備比(倍)_近四季平均','長期資金佔不動產廠房及設備比(倍)_近四季同業平均'
                               ]].reset_index(drop=True)
    

    return fig, fig2, df_long_term_capital_to_ppe_ratio


# fig, fig2, df_long_term_capital_to_ppe_ratio = plotly_long_term_capital_to_ppe_ratio_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show() 
# fig2.show()
# display(df_long_term_capital_to_ppe_ratio)



#%%
# 003 包成def
# * 資產總額 ＝ 負債總額 ＋ 權益總額
# * 一般產業約1.5～3，金融業、壽險業高達10也可能
# 權益乘數(財務槓桿) = 總資產 / 股東 權益總額

# * 股東 權益總額 = 資產總額 - 負債總額
# * 大多數產業 0.5～1.5，太高要小心，金融業例外
# 總負債/股東權益比 Total Debt/Equity Ratio = 總負債 / 股東 權益總額
# 銀行業ok 

def plotly_equity_multiplier_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    """
    直接用 df_bs_ci_cfs 裡權益乘數(倍)現成四欄畫圖（單季與近四季平均）。
    """

    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '權益乘數(倍)', '權益乘數(倍)_同業平均',
        '權益乘數(倍)_近四季平均', '權益乘數(倍)_近四季同業平均'
    ]
    for c in must_cols:
        if c not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{c}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[
        (df_bs_ci_cfs['產業類別提取'] == stock_industry) &
        (df_bs_ci_cfs['標題'].astype(str).str.endswith('金額'))
    ].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.sort_values('年度-季度')
        .dropna(subset=['權益乘數(倍)_同業平均'], how='all')
        .drop_duplicates(['年度-季度'], keep='last')
        [['年度-季度', '權益乘數(倍)_同業平均', '權益乘數(倍)_近四季同業平均']]
        .sort_values('年度-季度')
        .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last_row = df_industry.iloc[-1]
        latest_em = (
            f"{last_row['權益乘數(倍)_同業平均']:.2f}"
            if pd.notnull(last_row['權益乘數(倍)_同業平均']) else "無資料"
        )
        last4_em = (
            f"{last_row['權益乘數(倍)_近四季同業平均']:.2f}"
            if pd.notnull(last_row['權益乘數(倍)_近四季同業平均']) else "無資料"
        )
    else:
        latest_em = "無資料"
        last4_em = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(series):
        s = series.dropna()
        if s.empty:
            return [0, 1]
        ymin = float(s.min())
        ymax = float(s.max())
        if ymin == ymax:
            return [ymin - 0.2, ymax + 0.2]
        return [ymin - 0.2, ymax + 0.2]

    y_range = _get_y_range(pd.concat([
        df_stock['權益乘數(倍)'],
        df_industry['權益乘數(倍)_同業平均']
    ], ignore_index=True))

    y_range2 = _get_y_range(pd.concat([
        df_stock['權益乘數(倍)_近四季平均'],
        df_industry['權益乘數(倍)_近四季同業平均']
    ], ignore_index=True))

    # === 7. 繪圖 ===
    # 圖1：單季資產負債比%
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['權益乘數(倍)'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.5),
        marker=dict(
            color=['red' if (pd.notnull(v) and v > 3) else 'mediumturquoise'
                   for v in df_stock['權益乘數(倍)']],
            size=8
        ),
        text=[f"{v:.2f}" if pd.notnull(v) else "" for v in df_stock['權益乘數(倍)']],
        textposition='top center',
        name="權益乘數(倍)-個股"
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['權益乘數(倍)_同業平均'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}" if pd.notnull(v) else "" for v in df_industry['權益乘數(倍)_同業平均']],
        textposition='top center',
        name="權益乘數(倍)-同業平均"
    ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 各季度權益乘數(財務槓桿)｜同業最新一季平均：{latest_em}',
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='權益乘數(倍)', range=y_range),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        ))


    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['權益乘數(倍)_近四季平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', width=2.5),
        marker=dict(
            color=['red' if (pd.notnull(v) and v > 3) else 'deepskyblue'
                   for v in df_stock['權益乘數(倍)_近四季平均']],
            size=8
        ),
        text=[f"{v:.2f}" if pd.notnull(v) else "" for v in df_stock['權益乘數(倍)_近四季平均']],
        textposition='top center',
        name="近四季平均權益乘數(倍)-個股"
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['權益乘數(倍)_近四季同業平均'],
        mode='lines+markers+text',
        line=dict(color='deepskyblue', dash='dot', width=2.5),
        marker=dict(size=8),
        text=[f"{v:.2f}" if pd.notnull(v) else "" for v in df_industry['權益乘數(倍)_近四季同業平均']],
        textposition='top center',
        name="近四季平均權益乘數(倍)-同業平均"
    ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均權益乘數(財務槓桿)｜同業最新近四季平均：{last4_em}',
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='權益乘數(倍)_近四季平均', range=y_range2),
        width=900, height=350,
        legend=dict(
        orientation='h',          # 水平排列
        yanchor='top',            # 錨點對齊上方
        y=-0.3,                   # 向下移
        xanchor='center',         # X 軸錨點對齊中央
        x=0.5                     # 置中
    ))

    # === 8. 精簡 df ===
    keep_cols = [
        '標題','股票代號','產業類別提取','年度-季度',
        '權益乘數(倍)', '權益乘數(倍)_同業平均',
        '權益乘數(倍)_近四季平均', '權益乘數(倍)_近四季同業平均'
    ]
    df_equity_multiplier = df_stock[keep_cols].reset_index(drop=True)
    

    return fig, fig2, df_equity_multiplier


# fig, fig2, df_equity_multiplier = plotly_equity_multiplier_from_table(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_equity_multiplier)



#%%
# 009 包成def
# 償債能力 debt-paying ability 
# 流動比率 current ratio = 流動資產 / 流動負債 
# 速動比率 quick ratio = （流動資產 - 存貨 - 預付費用）/ 流動負債 
# 銀行業不看

def plotly_debt_paying_ability(df_bs_ci_cfs, stock_industry, stock_id, stock_name):
    # === 1. 取要的欄位 ===
    must_cols = [
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '流動比率', '流動比率_同業平均', '近四季平均流動比率', '近四季平均流動比率_同業平均',
        '速動比率', '速動比率_同業平均', '近四季平均速動比率', '近四季平均速動比率_同業平均'
    ]
    for col in must_cols:
        if col not in df_bs_ci_cfs.columns:
            raise ValueError(f'缺少必要欄位：{col}')

    # === 2. 鎖定該產業，防呆 ===
    base = df_bs_ci_cfs[(df_bs_ci_cfs['產業類別提取'] == stock_industry)].copy()

    # === 3. 個股資料 ===
    df_stock = base[base['股票代號'].astype(str) == str(stock_id)].sort_values('年度-季度')

    # === 4. 同業平均（每季唯一一筆，同季用第一個非空值) ===
    df_industry = (
        base.dropna(subset=['流動比率_同業平均'], how='all')
            .drop_duplicates(['年度-季度'], keep='last')
            .sort_values('年度-季度')
            .reset_index(drop=True)
    )

    # === 5. 取title用 ===
    if not df_industry.empty:
        last = df_industry.iloc[-1]
        latest_current = f"{last['流動比率_同業平均']:.2f}"
        latest_quick = f"{last['速動比率_同業平均']:.2f}"
        late4_current = f"{last['近四季平均流動比率_同業平均']:.2f}"
        late4_quick = f"{last['近四季平均速動比率_同業平均']:.2f}"
    else:
        latest_current = "無資料"
        latest_quick = "無資料"
        late4_current = "無資料"
        late4_quick = "無資料"

    # === 6. y 範圍 ===
    def _get_y_range(*series_list):
        vals = pd.concat([s.dropna() for s in series_list if s is not None], axis=0)
        if vals.empty:
            return [0, 1]
        ymin, ymax = float(vals.min()), float(vals.max())
        return [ymin - 0.5, ymax + 0.5]

    y_range = _get_y_range(
        df_stock['流動比率'], df_stock['速動比率'],
        df_industry['流動比率_同業平均'], df_industry['速動比率_同業平均']
    )
    y_range2 = _get_y_range(
        df_stock['近四季平均流動比率'], df_stock['近四季平均速動比率'],
        df_industry['近四季平均流動比率_同業平均'], df_industry['近四季平均速動比率_同業平均']
    )

    # === 7. 繪圖 ===
    # 圖1：單季
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['流動比率'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.2),
        text=df_stock['流動比率'],
        textposition='top center',
        name='流動比率-個股'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['流動比率_同業平均'],
        mode='lines+markers',
        line=dict(color='mediumturquoise', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['流動比率_同業平均']],
        name='流動比率-同業平均'
    ))
    fig.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['速動比率'],
        mode='lines+markers+text',
        line=dict(color='blue', width=2),
        text=df_stock['速動比率'],
        textposition='top center',
        name='速動比率-個股'
    ))
    fig.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['速動比率_同業平均'],
        mode='lines+markers',
        line=dict(color='blue', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['速動比率_同業平均']],
        name='速動比率-同業平均'
    ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 各季度流動比率/速動比率 | 同業最新一季平均 流動比{latest_current} 速動比{latest_quick}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='比率', range=y_range),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # 圖2：近四季平均
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['近四季平均流動比率'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2.2),
        text=df_stock['近四季平均流動比率'],
        textposition='top center',
        name='近四季平均流動比率-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['近四季平均流動比率_同業平均'],
        mode='lines+markers',
        line=dict(color='mediumturquoise', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['近四季平均流動比率_同業平均']],
        name='近四季平均流動比率-同業平均'
    ))
    fig2.add_trace(go.Scatter(
        x=df_stock['年度-季度'],
        y=df_stock['近四季平均速動比率'],
        mode='lines+markers+text',
        line=dict(color='blue', width=2),
        text=df_stock['近四季平均速動比率'],
        textposition='top center',
        name='近四季平均速動比率-個股'
    ))
    fig2.add_trace(go.Scatter(
        x=df_industry['年度-季度'],
        y=df_industry['近四季平均速動比率_同業平均'],
        mode='lines+markers',
        line=dict(color='blue', dash='dot', width=1.5),
        text=[f"{v:.2f}" if not pd.isnull(v) else "" for v in df_industry['近四季平均速動比率_同業平均']],
        name='近四季平均速動比率-同業平均'
    ))
    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 近四季平均流動/速動比 | 同業最新近四季平均 流動比{late4_current} 速動比{late4_quick}',
        xaxis=dict(title='年度-季度'),
        yaxis=dict(title='比率', range=y_range2),
        width=900, height=350,
        legend=dict(
            orientation='h',          # 水平排列
            yanchor='top',            # 錨點對齊上方
            y=-0.3,                   # 向下移
            xanchor='center',         # X 軸錨點對齊中央
            x=0.5                     # 置中
        )
    )

    # === 8. 精簡 df ===
    df_liquidity = df_stock[[
        '標題', '股票代號', '產業類別提取', '年度-季度',
        '流動比率', '流動比率_同業平均', '近四季平均流動比率', '近四季平均流動比率_同業平均',
        '速動比率', '速動比率_同業平均', '近四季平均速動比率', '近四季平均速動比率_同業平均'
    ]]

    return fig, fig2, df_liquidity



# fig, fig2, df_liquidity = plotly_debt_paying_ability(df_bs_ci_cfs, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# display(df_liquidity)


#%%
# 月報寫法，有最新一季預測的EPS
# 021-1 包成def
# EPS Earning Per Share 每股盈餘
# 每股盈餘EPS = (本期稅後淨利 – 特別股股利) ÷ 加權平均流通在外的普通股股數
# 每股盈餘EPS = 稅後淨利/在外流通股數


def plotly_eps_monthly(df_monthly_eps, stock_industry, stock_id, stock_name):
    """
    用月報 df_monthly_eps 畫 EPS 四種圖（table、單季、同業、近四季平均、近四季累積），
    支援預估EPS。
    """
    
    must_cols = [
        '股票代號', '產業類別提取', '年度-季度',
        '標準基本每股盈餘', '去年同期EPS',
        '標準基本每股盈餘_同業平均',
        '標準基本每股盈餘_近四季平均', '標準基本每股盈餘_近四季同業平均',
        '近四季累積標準基本每股盈餘', '近四季累積標準基本每股盈餘_同業平均'
    ]
    for c in must_cols:
        if c not in df_monthly_eps.columns:
            raise ValueError(f'缺少必要欄位：{c}')

    # === 1. 鎖定該產業、個股 ===
    base = df_monthly_eps[
        (df_monthly_eps['產業類別提取'] == stock_industry)
    ].copy()

    # 去重，確保每季只有一筆（保留最後一筆）
    df_stock = (
        base[base['股票代號'].astype(str) == str(stock_id)]
        .sort_values('年度-季度')
        .drop_duplicates('年度-季度', keep='last')
    )

    # === 2. 同業平均（每季唯一一筆） ===
    df_industry = (
        base.sort_values('年度-季度')
        .dropna(subset=['標準基本每股盈餘_同業平均'], how='all')
        .drop_duplicates(['年度-季度'], keep='last')
        [['年度-季度', '標準基本每股盈餘_同業平均',
          '標準基本每股盈餘_近四季同業平均',
          '近四季累積標準基本每股盈餘_同業平均']]
        .sort_values('年度-季度')
        .reset_index(drop=True)
    )

    # === 3. 最新資訊 ===
    def safe2(v): return f"{v:.2f}" if pd.notnull(v) else "無資料"
    latest_eps = safe2(df_stock['標準基本每股盈餘'].iloc[-1]) if not df_stock.empty else "無資料"
    latest_eps_ind = safe2(df_industry['標準基本每股盈餘_同業平均'].iloc[-1]) if not df_industry.empty else "無資料"
    last4_eps = safe2(df_stock['標準基本每股盈餘_近四季平均'].iloc[-1]) if not df_stock.empty else "無資料"
    last4_eps_ind = safe2(df_industry['標準基本每股盈餘_近四季同業平均'].iloc[-1]) if not df_industry.empty else "無資料"
    acc4_eps = safe2(df_stock['近四季累積標準基本每股盈餘'].iloc[-1]) if not df_stock.empty else "無資料"
    acc4_eps_ind = safe2(df_industry['近四季累積標準基本每股盈餘_同業平均'].iloc[-1]) if not df_industry.empty else "無資料"

    def _get_y_range(*series):
        s = pd.concat(series, ignore_index=True).dropna()
        if s.empty:
            return [0, 1]
        ymin, ymax = float(s.min()), float(s.max())
        if ymin == ymax:
            return [ymin - 0.5, ymax + 0.5]
        return [ymin - 0.1 * abs(ymin), ymax + 0.1 * abs(ymax)]

    # === 4. table
    table_data = (
        df_stock[['年度-季度', '標準基本每股盈餘']]
        .dropna()
        .set_index('年度-季度').T
    )
    table = ff.create_table(table_data.round(2), height_constant=30)
    table.update_layout(
        title=f"{stock_id} {stock_name} 每股盈餘(EPS)",
        width=1000, height=200
    )

    # 圖1：單季EPS vs 去年同期EPS
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'],
        y=df_stock['標準基本每股盈餘'],
        name='每股盈餘',
        marker=dict(color='mediumturquoise'),
        text=[safe2(v) for v in df_stock['標準基本每股盈餘']],
        textposition='outside'
    ))
    fig.add_trace(go.Bar(
        x=df_stock['年度-季度'],
        y=df_stock['去年同期EPS'],
        name='去年同期每股盈餘',
        marker=dict(color='pink'),
        text=[safe2(v) for v in df_stock['去年同期EPS']],
        textposition='outside'
    ))
    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 前5年各季度、去年同期每股盈餘，最新一季為月報估值",
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='每股盈餘', range=_get_y_range(df_stock['標準基本每股盈餘'], df_stock['去年同期EPS'])),
        width=1000, height=450,
        barmode='group',
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )

    # 圖2：單季EPS vs 同業平均
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_stock['年度-季度'],
        y=df_stock['標準基本每股盈餘'],
        name='每股盈餘',
        marker=dict(color='mediumturquoise'),
        text=[safe2(v) for v in df_stock['標準基本每股盈餘']],
        textposition='outside'
    ))
    fig2.add_trace(go.Bar(
        x=df_industry['年度-季度'],
        y=df_industry['標準基本每股盈餘_同業平均'],
        name='每股盈餘-同業平均',
        marker=dict(color='deepskyblue'),
        text=[safe2(v) for v in df_industry['標準基本每股盈餘_同業平均']],
        textposition='outside'
    ))
    fig2.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 單季EPS與同業平均<br>\
最新一季EPS:{latest_eps} 同業平均:{latest_eps_ind}，最新一季為月報估值",
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='每股盈餘', range=_get_y_range(df_stock['標準基本每股盈餘'], df_industry['標準基本每股盈餘_同業平均'])),
        width=1000, height=450,
        barmode='group',
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
        

    # 圖3：近四季平均EPS vs 同業
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_stock['年度-季度'],
        y=df_stock['標準基本每股盈餘_近四季平均'],
        name='近四季平均EPS',
        marker=dict(color='orange'),
        text=[safe2(v) for v in df_stock['標準基本每股盈餘_近四季平均']],
        textposition='outside'
    ))
    fig3.add_trace(go.Bar(
        x=df_industry['年度-季度'],
        y=df_industry['標準基本每股盈餘_近四季同業平均'],
        name='近四季平均EPS-同業平均',
        marker=dict(color='deepskyblue'),
        text=[safe2(v) for v in df_industry['標準基本每股盈餘_近四季同業平均']],
        textposition='outside'
    ))
    fig3.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季平均EPS與同業平均<br>\
近四季平均EPS:{last4_eps} 同業平均:{last4_eps_ind}，最新一季為月報估值",
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='近四季平均每股盈餘', range=_get_y_range(df_stock['標準基本每股盈餘_近四季平均'], df_industry['標準基本每股盈餘_近四季同業平均'])),
        width=1000, height=450,
        barmode='group',
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )

    # 圖4：近四季累積EPS vs 同業
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=df_stock['年度-季度'],
        y=df_stock['近四季累積標準基本每股盈餘'],
        name='近四季累積EPS',
        marker=dict(color='indianred'),
        text=[safe2(v) for v in df_stock['近四季累積標準基本每股盈餘']],
        textposition='outside'
    ))
    fig4.add_trace(go.Bar(
        x=df_industry['年度-季度'],
        y=df_industry['近四季累積標準基本每股盈餘_同業平均'],
        name='近四季累積EPS-同業平均',
        marker=dict(color='deepskyblue'),
        text=[safe2(v) for v in df_industry['近四季累積標準基本每股盈餘_同業平均']],
        textposition='outside'
    ))
    fig4.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 近四季累積EPS與同業平均<br>\
近四季累積EPS:{acc4_eps} 同業平均:{acc4_eps_ind}，最新一季為月報估值",
        xaxis=dict(title='年份-季度'),
        yaxis=dict(title='近四季累積每股盈餘', range=_get_y_range(df_stock['近四季累積標準基本每股盈餘'], df_industry['近四季累積標準基本每股盈餘_同業平均'])),
        width=1000, height=450,
        barmode='group',
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )

    # 精簡 df
    keep_cols = must_cols
    df_eps = df_stock[keep_cols].reset_index(drop=True)

    return table, fig, fig2, fig3, fig4, df_eps



# table, fig, fig2, fig3, fig4, df_eps = plotly_eps_monthly(df_monthly_eps, stock_industry, stock_id, stock_name)
# table.show()
# fig.show()
# fig2.show()
# fig3.show()
# fig4.show()
# display(df_eps)


#%%
# 021-2 包成def
# 月報＋EPS
# EPS Earning Per Share 每股盈餘
# 每股盈餘EPS = (本期稅後淨利 – 特別股股利) ÷ 加權平均流通在外的普通股股數
# 每股盈餘EPS = 稅後淨利/在外流通股數

def monthly_eps(df_monthly_eps, stock_industry, stock_id, stock_name):
    df_prediction2 = df_monthly_eps[df_monthly_eps['股票代號'] == stock_id]

    # 取最新的 年度、月份
    latest_year = df_prediction2['年度'].max()
    latest_month = df_prediction2[df_prediction2['年度']==latest_year]['月份'].max()
    # print(latest_year)
    # print(latest_month)

    # 找目前季度
    def month_to_quarter(month):
            if month in [1,2,3]:
                return 'Q1'
            elif month in [4,5,6]:
                return 'Q2'
            elif month in [7,8,9]:
                return 'Q3'
            else:
                return 'Q4'
    latest_quarter = month_to_quarter(latest_month)
    # print(latest_quarter)
        
    # 用月來判斷要累加哪些月份
    def get_current_quarter_months(month):
        if month in [1,2,3]:
            return list(range(1, month+1))
        elif month in [4,5,6]:
            return list(range(4, month+1))
        elif month in [7,8,9]:
            return list(range(7, month+1))
        else:
            return list(range(10, month+1))
    current_months = get_current_quarter_months(latest_month)
    # print(current_months)

    # 本季度、去年同期 要抓的「月」
    df_now = df_prediction2[(df_prediction2['年度'] == latest_year) & (df_prediction2['月份'].isin(current_months))]
    df_last_year = df_prediction2[(df_prediction2['年度'] == latest_year-1) & (df_prediction2['月份'].isin(current_months))]

    # 本季度累積營收
    sum_now = df_now['當月營收'].sum()
    sum_last_year = df_last_year['當月營收'].sum()
    # print(sum_now)
    # print(sum_last_year)

    # 拿出去年同期EPS
    last_year_Q季度 = f"{latest_year-1}{latest_quarter}"
    last_year_eps = df_prediction2.loc[df_prediction2['去年年度-季度'] == last_year_Q季度, '去年同期EPS'].values
    # print(last_year_Q季度)
    last_year_eps = last_year_eps[0]
    # print(last_year_eps)
        
    # 推估今年 EPS
    if sum_last_year > 0 and not np.isnan(last_year_eps):
        predicted_eps = round((sum_now / sum_last_year) * last_year_eps, 2)
    else:
        predicted_eps = None
    # print(predicted_eps)

    # 
    fig = go.Figure()

    fig.add_trace(go.Bar(x=df_prediction2['年月'], 
                        y=df_prediction2['當月營收'], 
                        name='當月營收', width=0.41, 
                        marker=dict(color='blue')))

    fig.add_trace(go.Bar(x=df_prediction2['年月'], 
                        y=df_prediction2['去年當月營收'], 
                        name='去年當月營收', width=0.41, 
                        marker=dict(color='mediumturquoise')))

    fig.add_trace(go.Scatter(
                    x=df_prediction2['年月'],
                    y=df_prediction2['去年同月 增減(%)'],
                    mode='lines+markers+text',
                    line=dict(color='red', width=1.8),
                    textposition='top center',
                    name='去年同月 增減(%)',
                    yaxis='y3'   
                ))

    # 
    y_range = [df_prediction2['當月營收'].min()-50000, df_prediction2['當月營收'].max()+50000]
    y_range2 = [df_prediction2['去年同月 增減(%)'].min()-10, df_prediction2['去年同月 增減(%)'].max()+10]


    last_3_rows = df_prediction2['去年同月 增減(%)'].tail(3)
    negative_count = last_3_rows[last_3_rows < 0].count()


    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 當月營收、去年同月營收，近三季有{negative_count}季同月增減(%)是負的',
        xaxis=dict(title='年月'),
        yaxis=dict(title='當月營收', range=y_range),
        yaxis2=dict(title='去年當月營收', range=y_range),  
        yaxis3=dict(title='去年同月 增減(%)', overlaying='y', side='right', range=y_range2),
        width=1000,
        height=450,
        barmode='group',
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
    # 
    # print(f"""
    # ==== 預估EPS計算 ====

    # 1. 最新資料區間：{latest_year}年{latest_month}月
    # 2. 本季度已發布月數：{current_months}
    # - 本季度累積營收：{sum_now:,.0f}
    # - 去年同期累積營收：{sum_last_year:,.0f}
    # 3. 去年同期EPS（{last_year_Q季度}）：{last_year_eps}

    # 公式：
    #     推估EPS = (本季度累積營收 / 去年同期累積營收) × 去年同期EPS
    #             = ({sum_now} / {sum_last_year}) × {last_year_eps}
    #             = {predicted_eps}

    # 根據 {latest_year} 年第 {latest_quarter} 已發布月份（{', '.join(map(str, current_months))} 月）營收，相較於去年同期（{latest_year-1} 年同月），
    # 推估本季EPS約為 {predicted_eps}
    # """)


    return fig, latest_year, latest_month, latest_quarter, current_months, sum_now, sum_last_year, last_year_Q季度, last_year_eps,\
            sum_now, sum_last_year, last_year_eps, predicted_eps, df_prediction2
            
            
            
# fig, latest_year, latest_month, latest_quarter, current_months, sum_now, sum_last_year, last_year_Q季度, last_year_eps,\
#             sum_now, sum_last_year, last_year_eps, predicted_eps, df_prediction2 = monthly_eps(df_monthly_eps, stock_industry, stock_id, stock_name)


# print(f"""
# ==== 預估EPS計算 ====

# 1. 最新資料區間：{latest_year}年{latest_month}月
# 2. 本季度已發布月數：{current_months}
# - 本季度累積營收：{sum_now:,.0f}
# - 去年同期累積營收：{sum_last_year:,.0f}
# 3. 去年同期EPS（{last_year_Q季度}）：{last_year_eps}

# 公式：
#     推估EPS = (本季度累積營收 / 去年同期累積營收) × 去年同期EPS
#             = ({sum_now} / {sum_last_year}) × {last_year_eps}
#             = {predicted_eps}

# 根據 {latest_year} 年第 {latest_quarter} 已發布月份（{', '.join(map(str, current_months))} 月）營收，相較於去年同期（{latest_year-1} 年同月），
# 推估本季EPS約為 {predicted_eps}
# """)
    
# fig.show()