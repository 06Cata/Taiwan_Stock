#%%
# 籌碼面分析 
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
# from backtesting import Backtest, Strategy
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


def _read_and_concat_sqlite_tables_chip():
    urls = [
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_chip_1.sqlite3",
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_chip_2.sqlite3",
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_chip_3.sqlite3",
    ]
    table_names = [
        "merged_etf_index_pepb_chip_1",
        "merged_etf_index_pepb_chip_2",
        "merged_etf_index_pepb_chip_3",
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


def _read_and_concat_sqlite_tables_chip_local():
    # paths = [
    #     "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_chip_1.sqlite3",
    #     "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_chip_2.sqlite3",
    #     "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_chip_3.sqlite3"
    # ]
    
    # 取得專案根目錄
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 定義相對於專案根目錄的路徑
    paths = [
        os.path.join(ROOT, "merged_etf_index_pepb_chip_1.sqlite3"),
        os.path.join(ROOT, "merged_etf_index_pepb_chip_2.sqlite3"),
        os.path.join(ROOT, "merged_etf_index_pepb_chip_3.sqlite3"),
    ]
    
    table_names = [
        "merged_etf_index_pepb_chip_1",
        "merged_etf_index_pepb_chip_2",
        "merged_etf_index_pepb_chip_3",
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
    return _read_and_concat_sqlite_tables_chip_local()


# %%
# 日期區間快取（根據滑桿/股票篩資料）
@st.cache_data(show_spinner=False)
def read_merged_df_2(daily_df_merge_index_pepb, stock_id, date_range):
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
    df = df[df['股票代號'] == stock_id].sort_values(by='Date')
    return df


# ===================== plotly =====================

#%%
# 三大法人日報：最新 60 日
def plot_latest60_invest_bar(daily_df_merge_index_pepb_chip, stock_id, stock_industry, stock_name):
    df = daily_df_merge_index_pepb_chip.copy()

    # 先把原始欄位轉數值，避免字串相除
    for c in ['外資含自營商陸資_買賣超', '投信_買賣超', '自營商_買賣超', '三大法人買賣超股數', 'Close']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # 轉張數（/10）
    if '外資含自營商陸資_買賣超' in df.columns:
        df['外資含自營商陸資_買賣超張數'] = df['外資含自營商陸資_買賣超'] / 10
    if '投信_買賣超' in df.columns:
        df['投信_買賣超張數'] = df['投信_買賣超'] / 10
    if '自營商_買賣超' in df.columns:
        df['自營商_買賣超張數'] = df['自營商_買賣超'] / 10
    if '三大法人買賣超股數' in df.columns:
        df['三大法人買賣超張數'] = df['三大法人買賣超股數'] / 10

    # 單檔
    if stock_id and '股票代號' in df.columns:
        df = df[df['股票代號'] == stock_id]

    # 日期處理
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values('Date', ascending=False).head(60).sort_values('Date').reset_index(drop=True)

    # ===== fig1：外資含自營商陸資 =====
    fig = go.Figure()
    if '外資含自營商陸資_買賣超張數' in df.columns:
        fig.add_trace(go.Bar(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=df['外資含自營商陸資_買賣超張數'],
            name='外資含自營商陸資_買賣超張數',
            marker_color='royalblue'
        ))
    fig.update_layout(
        barmode='group',
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 外資含自營商陸資_買賣超張數',
        xaxis_title='日期',
        yaxis_title='買賣超（張）',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
    fig.add_hline(y=0, line_width=1, line_dash='dash')

    # ===== fig2：投信 =====
    fig2 = go.Figure()
    if '投信_買賣超張數' in df.columns:
        fig2.add_trace(go.Bar(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=df['投信_買賣超張數'],
            name='投信_買賣超張數',
            marker_color='orange'
        ))
    fig2.update_layout(
        barmode='group',
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 投信_買賣超張數',
        xaxis_title='日期',
        yaxis_title='買賣超（張）',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )

    fig2.add_hline(y=0, line_width=1, line_dash='dash')

    # ===== fig3：自營商 =====
    fig3 = go.Figure()
    if '自營商_買賣超張數' in df.columns:
        fig3.add_trace(go.Bar(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=df['自營商_買賣超張數'],
            name='自營商_買賣超張數',
            marker_color='mediumturquoise'
        ))
    fig3.update_layout(
        barmode='group',
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 自營商_買賣超張數',
        xaxis_title='日期',
        yaxis_title='買賣超（張）',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
    fig3.add_hline(y=0, line_width=1, line_dash='dash')


    fig4 = go.Figure()
    if '三大法人買賣超張數' in df.columns:
        # 分正負
        pos = df['三大法人買賣超張數'].clip(lower=0)
        neg = df['三大法人買賣超張數'].clip(upper=0)

        # 五日均線
        df['三大法人買賣超張數_MA5'] = df['三大法人買賣超張數'].rolling(5, min_periods=5).mean()

        # 正紅、負綠兩個 bar trace
        fig4.add_trace(go.Bar(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=pos,
            name='三大法人買超（正）',
            marker_color='indianred',
            hovertemplate='日期=%{x}<br>買超=%{y:.0f} 張<extra></extra>'
        ))
        fig4.add_trace(go.Bar(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=neg,
            name='三大法人賣超（負）',
            marker_color='seagreen',
            hovertemplate='日期=%{x}<br>賣超=%{y:.0f} 張<extra></extra>'
        ))

        # 疊加 5D MA 折線
        fig4.add_trace(go.Scatter(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=df['三大法人買賣超張數_MA5'],
            name='三大法人 5D MA',
            mode='lines',
            line=dict(width=1.5, color='black')
        ))

    fig4.update_layout(
        barmode='relative',
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 三大法人買賣超(合併)張數',
        xaxis_title='日期',
        yaxis_title='買賣超（張）',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
    fig4.add_hline(y=0, line_width=1, line_dash='dash')

    # ===== fig5：收盤價 =====
    fig5 = go.Figure()
    if 'Close' in df.columns:
        fig5.add_trace(go.Scatter(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=df['Close'],
            name='收盤價', mode='lines+markers',
            line=dict(width=2, color='red')
        ))
    fig5.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 收盤價',
        xaxis_title='日期',
        yaxis_title='收盤價',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )

    return fig, fig2, fig3, fig4, fig5


# fig, fig2, fig3, fig4, fig5 = plot_latest60_invest_bar(daily_df_merge_index_pepb_chip, stock_id, stock_industry, stock_name)
# fig.show()
# fig2.show()
# fig3.show()
# fig4.show()
# fig5.show()



#%%
# 融資融券日報：最新 60 日

def plot_latest60_margin_bars(daily_df_merge_index_pepb_chip, stock_industry, stock_id, stock_name):
    df = daily_df_merge_index_pepb_chip.copy()
    
    if stock_id and '股票代號' in df.columns:
        df = df[df['股票代號'] == stock_id]
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values('Date')
    
    # 轉型
    for c in ['融資_資餘額', '融券_券餘額']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    
    # 計算買賣超（張數）
    df['融資_買賣超'] = df['融資_資餘額'].diff()
    df['融券_買賣超'] = df['融券_券餘額'].diff()
    
    # 只取最新 60 天
    df = df.sort_values('Date', ascending=False).head(60).sort_values('Date')

    # fig：融資_買賣超
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Date'].dt.strftime('%Y-%m-%d'),
        y=df['融資_買賣超'],
        name='融資_買賣超',
        marker_color='indianred'
    ))
    fig.update_layout(
        barmode='group',
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 融資_買賣超',
        xaxis_title='日期',
        yaxis_title='融資_買賣超（張數）',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
    # fig2：融券_買賣超
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df['Date'].dt.strftime('%Y-%m-%d'),
        y=df['融券_買賣超'],
        name='融券_買賣超',
        marker_color='seagreen'
    ))
    fig2.update_layout(
        barmode='group',
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 融券_買賣超',
        xaxis_title='日期',
        yaxis_title='融券_買賣超（張數）',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
    
    fig3 = go.Figure()
    # 淨槓桿流 = 融資_買賣超 − 融券_買賣超（融券買賣超先乘上 -1，再與融資相加）
    df['淨槓桿流'] = df['融資_買賣超'] - df['融券_買賣超']
    df['淨槓桿流_MA5'] = df['淨槓桿流'].rolling(5, min_periods=5).mean()

    # 以正負分兩個 bar trace（顏色更清楚）
    pos = df['淨槓桿流'].clip(lower=0)
    neg = df['淨槓桿流'].clip(upper=0)

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df['Date'].dt.strftime('%Y-%m-%d'), y=pos,
        name='淨槓桿流（正）', marker_color='indianred'
    ))
    fig3.add_trace(go.Bar(
        x=df['Date'].dt.strftime('%Y-%m-%d'), y=neg,
        name='淨槓桿流（負）', marker_color='seagreen'
    ))
    
    # 疊加 5D MA 折線
    if df['淨槓桿流_MA5'].notna().any():
        fig3.add_trace(go.Scatter(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=df['淨槓桿流_MA5'],
            name='淨槓桿流 5D MA', mode='lines', line=dict(width=1.5, color='black')
        ))
    fig3.update_layout(
        barmode='relative',
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 淨槓桿流（融資買賣超 − 融券買賣超）',
        xaxis_title='日期',
        yaxis_title='張數',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
    fig3.add_hline(y=0, line_width=1, line_dash='dash')

    
    fig4 = go.Figure()
    if 'Close' in df.columns:
        fig4.add_trace(go.Scatter(
            x=df['Date'].dt.strftime('%Y-%m-%d'),
            y=pd.to_numeric(df['Close'], errors='coerce'),
            name='收盤價', mode='lines+markers',
            line=dict(width=2, color='red')
        ))
    fig4.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 最新60日 收盤價',
        xaxis_title='日期',
        yaxis_title='收盤價',
        width=1000,
        height=350,
        bargap=0.2,
        font=dict(size=12),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
        )
    )
    
    return fig, fig2, fig3, fig4


# fig, fig2, fig3, fig4 = plot_latest60_margin_bars(daily_df_merge_index_pepb_chip, stock_industry, stock_id, stock_name)
# fig.show()
# fig2.show()
# fig3.show()
# fig4.show()