#%%
# 基本面_價值分析 
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
# merge daily_index_pepb_value monthly_pes
def merge_daily_index_pepb_value(daily_df_merge_index_pepb_value, df_monthly_eps):
    #
    print('daily_df_merge_index_pepb_value')
    print(daily_df_merge_index_pepb_value.shape) 
    daily_df_merge_index_pepb_value = daily_df_merge_index_pepb_value.drop_duplicates()
    print(daily_df_merge_index_pepb_value.shape)
    print()
    print('df_monthly_eps')
    print(df_monthly_eps.shape) 
    df_monthly_eps = df_monthly_eps.drop_duplicates()
    print(df_monthly_eps.shape)
    print()
    
    
    daily_df_merge_index_pepb_value['Date'] = pd.to_datetime(daily_df_merge_index_pepb_value['Date'])
    daily_df_merge_index_pepb_value['年度'] = daily_df_merge_index_pepb_value['Date'].dt.year - 1911
    daily_df_merge_index_pepb_value['季度'] = ((daily_df_merge_index_pepb_value['Date'].dt.month - 1) // 3 + 1)
    daily_df_merge_index_pepb_value['年度-季度'] = (
        daily_df_merge_index_pepb_value['年度'].astype(str) + 'Q' + daily_df_merge_index_pepb_value['季度'].astype(str)
    )
    
    # 
    # merge_df = pd.merge(daily_df_merge_index_pepb_value, df_monthly_eps[['年度-季度', '股票代號', '近四季累積標準基本每股盈餘', '近四季稅後淨利年增率']], on=['年度-季度', '股票代號'], how='left')
    cols_needed = ['股票代號','年度-季度','近四季累積標準基本每股盈餘', '標準本期淨利淨損', '近四季稅後淨利年增率', '近四季累積本期淨利', '去年同期近四季累積淨利淨損']
    df_monthly_eps_q = (
        df_monthly_eps[cols_needed]
        .sort_values(['股票代號','年度-季度'])   # 如果有日期欄，改成包含日期的排序
        .drop_duplicates(['股票代號','年度-季度'], keep='last')  # 關鍵：每股每季唯一
    )

    merge_df = pd.merge(
        daily_df_merge_index_pepb_value,
        df_monthly_eps_q,
        on=['年度-季度','股票代號'],
        how='left',
        validate='many_to_one'
    )
    
    
    merge_df['cheap_pe'] = merge_df['cheap_pe'].fillna(np.nan) 
    merge_df['cheap_price'] = np.where(
        merge_df['近四季累積標準基本每股盈餘'].isna() | merge_df['cheap_pe'].isna(),
        np.nan,
        round(merge_df['cheap_pe'] * merge_df['近四季累積標準基本每股盈餘'], 2)
    )

    merge_df['low_pe'] = merge_df['low_pe'].fillna(np.nan) 
    merge_df['low_price'] = np.where(
        merge_df['近四季累積標準基本每股盈餘'].isna() | merge_df['low_pe'].isna(),
        np.nan,
        round(merge_df['low_pe'] * merge_df['近四季累積標準基本每股盈餘'], 2)
    )

    merge_df['reasonable_pe'] = merge_df['reasonable_pe'].fillna(np.nan) 
    merge_df['reasonable_price'] = np.where(
        merge_df['近四季累積標準基本每股盈餘'].isna() | merge_df['reasonable_pe'].isna(),
        np.nan,
        round(merge_df['reasonable_pe'] * merge_df['近四季累積標準基本每股盈餘'], 2)
    )

    merge_df['high_pe'] = merge_df['high_pe'].fillna(np.nan) 
    merge_df['high_price'] = np.where(
        merge_df['近四季累積標準基本每股盈餘'].isna() | merge_df['high_pe'].isna(),
        np.nan,
        round(merge_df['high_pe'] * merge_df['近四季累積標準基本每股盈餘'], 2)
    )

    merge_df['expensive_pe'] = merge_df['expensive_pe'].fillna(np.nan) 
    merge_df['expensive_price'] = np.where(
        merge_df['近四季累積標準基本每股盈餘'].isna() | merge_df['expensive_pe'].isna(),
        np.nan,
        round(merge_df['expensive_pe'] * merge_df['近四季累積標準基本每股盈餘'], 2)
    )

    merge_df['pe'] = round(merge_df['Close'] / merge_df['近四季累積標準基本每股盈餘'], 2)

    print(merge_df.shape)

    return merge_df

#%%
# Streamlit 讀取 index+etf+daily_price+pe_pb+value 整理
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


def _read_and_concat_sqlite_tables_value():
    urls = [
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_value_1.sqlite3",
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_value_2.sqlite3",
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_value_3.sqlite3",
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_value_4.sqlite3",
        ]
    table_names = [
        "merged_etf_index_pepb_value_1",
        "merged_etf_index_pepb_value_2",
        "merged_etf_index_pepb_value_3",
        "merged_etf_index_pepb_value_4"
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
        st.write(f"第一次會較久，共 5 份，目前下載第 5 份…")
        path = download_sqlite_from_github(url)
        conn = sqlite3.connect(path)
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        dfs.append(df)
        progress_bar.progress(idx / total, text=f"已下載第 {idx} 份，共 {total} 份")
    progress_bar.empty()  # 下載結束移除進度條
    df_monthly_eps = pd.concat(dfs, ignore_index=True)
    st.write('ok')
    return df_monthly_eps


def _read_and_concat_sqlite_tables_value_local():
    # paths = [
    #     "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_value_1.sqlite3",
    #     "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_value_2.sqlite3",
    #     "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_value_3.sqlite3",
    #     "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_value_4.sqlite3",
    # ]
    
    # 取得專案根目錄
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 定義相對於專案根目錄的路徑
    paths = [
        os.path.join(ROOT, "merged_etf_index_pepb_value_1.sqlite3"),
        os.path.join(ROOT, "merged_etf_index_pepb_value_2.sqlite3"),
        os.path.join(ROOT, "merged_etf_index_pepb_value_3.sqlite3"),
        os.path.join(ROOT, "merged_etf_index_pepb_value_4.sqlite3"),
    ]
    
    table_names = [
        "merged_etf_index_pepb_value_1",
        "merged_etf_index_pepb_value_2",
        "merged_etf_index_pepb_value_3",
        "merged_etf_index_pepb_value_4"
    ]
    dfs = []
    for path, table_name in zip(paths, table_names):
        conn = sqlite3.connect(path)
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        dfs.append(df)
    df_concat = pd.concat(dfs, ignore_index=True)
    df_concat['Date'] = pd.to_datetime(df_concat['Date'], errors='coerce')
    return df_concat


def _read_and_concat_sqlite_tables_monthly_eps_local():
    # paths = [
    #     "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_monthly_eps.sqlite3",
    # ]
    
    # 取得專案根目錄
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 定義相對於專案根目錄的路徑
    paths = [
        os.path.join(ROOT, "merged_monthly_eps.sqlite3"),
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
    return _read_and_concat_sqlite_tables_value_local()


@st.cache_data(show_spinner="載入資料中…", persist=True)
def read_and_concat_sqlite_tables_monthly_eps():
    return _read_and_concat_sqlite_tables_monthly_eps_local()


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
# 繪圖
# 殖利率 

def plotly_yield(merged_df_date,stock_industry, stock_name, stock_id):
    
    merged_df_2_date = merged_df_date[merged_df_date['股票代號']==stock_id]
    
    fig = go.Figure()

    merged_df_2_date['Date'] = pd.to_datetime(merged_df_2_date['Date'], format='%Y%m%d')
    merged_df_2_date['殖利率(%)'] = pd.to_numeric(merged_df_2_date['殖利率(%)'])
    merged_df_2_date['本益比'] = pd.to_numeric(merged_df_2_date['本益比'], errors='coerce')


    # '----' -> NaN
    merged_df_2_date.replace('----', pd.NA, inplace=True)

    # 
    merged_df_2_date['Close'] = pd.to_numeric(merged_df_2_date['Close'], errors='coerce')

    # 
    # merged_df_2_date.dropna(inplace=True)

    # 
    if merged_df_2_date.empty:
        print("DataFrame is empty. No data to plot.")
        return fig
    
    # 
    fig.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['Close'],
                            mode='lines',
                            line=dict(color='red', width=1.4),
                            name='收盤價',
                            yaxis='y'))

    # 
    fig.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['殖利率(%)'],
                            mode='lines', 
                            line=dict(color='blue', width=1.2),
                            name='殖利率(%)',
                            yaxis='y2'))


    # 
    if len(merged_df_2_date) > 0:
        stock_id = merged_df_2_date['股票代號'].iloc[0]
    else:
        stock_id = "Unknown"

    y_range = [merged_df_2_date['Close'].min()-10, merged_df_2_date['Close'].max()+10]
    y_range2 = [merged_df_2_date['殖利率(%)'].min()-1, merged_df_2_date['殖利率(%)'].max()+1]

    fig.update_layout(title=f'{stock_industry} {stock_id} {stock_name} 收盤價、殖利率',
                        xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
                        yaxis=dict(title='收盤價', range=y_range),
                        yaxis2=dict(title='殖利率(%)', overlaying='y', side='right', range=y_range2), 
                        width=900, height=350,
                        legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
                        xanchor='center',
                        x=0.5,
                        font=dict(size=13)   # 如覺得字太大可再調小
                        )
                    )
                            
    return fig

# fig = plotly_yield(merged_df_date, stock_industry, stock_name, stock_id)
# fig.show()


#%%
# 股價淨值比

#%%
# 股價淨值比

def plotly_pb(merged_df_date, stock_industry, stock_name, stock_id):
    
    merged_df_2_date = merged_df_date[merged_df_date['股票代號']==stock_id]
    
    fig = go.Figure()

    merged_df_2_date['Date'] = pd.to_datetime(merged_df_2_date['Date'], format='%Y%m%d')
    merged_df_2_date['股價淨值比'] = pd.to_numeric(merged_df_2_date['股價淨值比'])

    # '----' -> NaN
    merged_df_2_date.replace('----', pd.NA, inplace=True)

    # 
    merged_df_2_date['Close'] = pd.to_numeric(merged_df_2_date['Close'], errors='coerce')

    # 
    # merged_df_2_date.dropna(inplace=True)

    # 
    fig.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['Close'],
                            mode='lines',
                            line=dict(color='red', width=1.2),
                            name='收盤價',
                            yaxis='y'))

    # 
    fig.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['股價淨值比'],
                            mode='lines', 
                            line=dict(color='blue', width=1.2),
                            name='股價淨值比',
                            yaxis='y2'))

    # 
    stock_id = merged_df_2_date['股票代號'].iloc[0]

    y_range = [merged_df_2_date['Close'].min()-10, merged_df_2_date['Close'].max()+10]
    y_range2 = [merged_df_2_date['股價淨值比'].min()-1, merged_df_2_date['股價淨值比'].max()+1]


    fig.update_layout(title=f'{stock_industry} {stock_id} {stock_name} 收盤價、股價淨值比',
                        xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
                        yaxis=dict(title='收盤價', range=y_range),
                        yaxis2=dict(title='股價淨值比', overlaying='y', side='right', range=y_range2), 
                        width=900, height=350,
                        legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
                        xanchor='center',
                        x=0.5,
                        font=dict(size=13)   # 如覺得字太大可再調小
                        )
                    )
    return fig


# fig = plotly_pb(merged_df_date, stock_industry, stock_name, stock_id)
# fig.show()

def plotly_pe(merged_df_date, stock_industry, stock_name, stock_id): # , predicted_eps, predicted_net_profit):
    
    merged_df_2_date = merged_df_date[merged_df_date['股票代號']==stock_id]
    
    merged_df_2_date = merged_df_2_date.sort_values('Date')

    # 年增率
    # merged_df_2_date['近四季稅後淨利年增率'] = (
    #     (merged_df_2_date['近四季累積淨利淨損'] / merged_df_2_date['去年同期近四季累積淨利淨損']) - 1) * 100
        
    # 本益成長比（PEG）
    merged_df_2_date['PEG'] = merged_df_2_date['本益比'] / merged_df_2_date['近四季稅後淨利年增率']

    
    
    fig2 = go.Figure()

    merged_df_2_date['Date'] = pd.to_datetime(merged_df_2_date['Date'], format='%Y%m%d')

    # '----' -> NaN
    merged_df_2_date.replace('----', pd.NA, inplace=True)

    # 
    merged_df_2_date['Close'] = pd.to_numeric(merged_df_2_date['Close'], errors='coerce')


    # 
    if merged_df_2_date.empty:
        print("DataFrame is empty. No data to plot.")
        return fig2, go.Figure()
    
    # 
    fig2.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['本益比'],
                            mode='lines',
                            line=dict(color='red', width=1.6),
                            name='本益比(倍)',
                            yaxis='y'))

    # 
    fig2.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['expensive_pe'],
                            mode='lines', 
                            line=dict(color='violet', width=1.2),
                            name='昂貴本益比',
                            yaxis='y2'))

    # 
    fig2.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['high_pe'],
                            mode='lines', 
                            line=dict(color='hotpink', width=1.2),
                            name='偏高本益比',
                            yaxis='y3'))

    # 
    fig2.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['reasonable_pe'], 
                            mode='lines', 
                            line=dict(color='orange', width=1.2),
                            name='合理本益比',
                            yaxis='y4'))

    # 
    fig2.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['low_pe'],
                            mode='lines', 
                            line=dict(color='green', width=1.2),
                            name='偏低本益比',
                            yaxis='y5'))

    # 
    fig2.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['cheap_pe'],
                            mode='lines', 
                            line=dict(color='blue', width=1.2),
                            name='便宜本益比',
                            yaxis='y6'))

    # 
    fig2.add_trace(go.Scatter(
                            x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['PEG'],
                            mode='lines',
                            line=dict(color='black', width=1.6),
                            name='PEG(本益成長比)',
                            yaxis='y7' 
                        ))

    # 
    if len(merged_df_2_date) > 0:
        stock_id = merged_df_2_date['股票代號'].iloc[0]
    else:
        stock_id = "Unknown"

    min1 = (merged_df_2_date['cheap_pe'].min()) * 0.4
    max1 = (merged_df_2_date['expensive_pe'].max()) * 0.3
    y_range = [merged_df_2_date['cheap_pe'].min()-min1, merged_df_2_date['expensive_pe'].max()+max1]

    fig2.update_layout(title=f'{stock_industry} {stock_id} {stock_name} 本益比河流圖',
                        xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
                        yaxis=dict(title='', range=y_range),
                        yaxis2=dict(title='', overlaying='y', range=y_range, showline=False), 
                        yaxis3=dict(title='', overlaying='y', range=y_range, showline=False),
                        yaxis4=dict(title='', overlaying='y', range=y_range, showline=False),
                        yaxis5=dict(title='', overlaying='y', range=y_range, showline=False),
                        yaxis6=dict(title='', overlaying='y', range=y_range, showline=False),
                        yaxis7=dict(title='PEG', overlaying='y', side='right', showline=False),
                        width=1000, height=450,
                        legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
                        xanchor='center',
                        x=0.5,
                        font=dict(size=13)   # 如覺得字太大可再調小
                        )
                    )

    # 
    fig3 = go.Figure()

    merged_df_2_date['Date'] = pd.to_datetime(merged_df_2_date['Date'], format='%Y%m%d')

    # '----' -> NaN
    merged_df_2_date.replace('----', pd.NA, inplace=True)

    # 
    merged_df_2_date['Close'] = pd.to_numeric(merged_df_2_date['Close'], errors='coerce')

    # 
    fig3.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['Close'],
                            mode='lines',
                            line=dict(color='red', width=1.6),
                            name='收盤價',
                            yaxis='y'))

    # 
    fig3.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['expensive_price'],
                            mode='lines', 
                            line=dict(color='violet', width=1.2),
                            name='昂貴價',
                            yaxis='y2'))

    # 
    fig3.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['high_price'],
                            mode='lines', 
                            line=dict(color='hotpink', width=1.2),
                            name='偏高價',
                            yaxis='y3'))

    # 
    fig3.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['reasonable_price'], 
                            mode='lines', 
                            line=dict(color='orange', width=1.2),
                            name='合理價',
                            yaxis='y4'))

    # 
    fig3.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['low_price'],
                            mode='lines', 
                            line=dict(color='green', width=1.2),
                            name='偏低價',
                            yaxis='y5'))

    # 
    fig3.add_trace(go.Scatter(x=merged_df_2_date['Date'], 
                            y=merged_df_2_date['cheap_price'],
                            mode='lines', 
                            line=dict(color='blue', width=1.2),
                            name='便宜價',
                            yaxis='y6'))

    # 
    stock_id = merged_df_2_date['股票代號'].iloc[0]

    min1 = (merged_df_2_date['cheap_price'].min()) * 0.4
    max1 = (merged_df_2_date['expensive_price'].max()) * 0.3
    y_range = [merged_df_2_date['cheap_price'].min()-min1, merged_df_2_date['expensive_price'].max()+max1]


    # operating_safety_margin = merged_df_2['安全邊際%'].iloc[-1]
    # 由上方推估本季 EPS {predicted_eps}、淨利淨損 {predicted_net_profit} 算出，僅供參考

    fig3.update_layout(title=f'{stock_industry} {stock_id} {stock_name} 收盤價、價值河流圖',
                        xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
                        yaxis=dict(title='', range=y_range),
                        yaxis2=dict(title='', overlaying='y', range=y_range, showline=False), 
                        yaxis3=dict(title='', overlaying='y', range=y_range, showline=False),
                        yaxis4=dict(title='', overlaying='y', range=y_range, showline=False),
                        yaxis5=dict(title='', overlaying='y', range=y_range, showline=False),
                        yaxis6=dict(title='', overlaying='y', range=y_range, showline=False),
                        width=1000, height=450,
                        legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
                        xanchor='center',
                        x=0.5,
                        font=dict(size=13)   # 如覺得字太大可再調小
                        )
                    )


    return fig2, fig3


# fig2, fig3 = plotly_pe(merged_df_date, stock_industry, stock_name, stock_id) # , predicted_eps, predicted_net_profit)
# fig2.show()
# fig3.show()



#%%
# 估價
def valuation_summary(merged_df_date, stock_id):
    # 1. 指定股票後，依照 Date 遞減排序
    df = merged_df_date
    if stock_id is not None:
        df = df[df['股票代號'] == stock_id]
    df = df.sort_values('Date', ascending=False).reset_index(drop=True)
    # 2. 從最新日期開始，往前找近四季累積EPS有資料的那一行
    valid_row = None
    for idx, row in df.iterrows():
        if pd.notnull(row['近四季累積標準基本每股盈餘']) and row['近四季累積標準基本每股盈餘'] != 0:
            valid_row = row
            break
    if valid_row is None:
        print(f"{stock_id} 找不到近四季累積EPS有資料的行！")
        return None
    
    # === 主要指標 ===
    close = valid_row['Close']
    pe = valid_row['本益比']
    eps = valid_row['近四季累積標準基本每股盈餘']
    pb = valid_row['股價淨值比']
    yield_ = valid_row['殖利率(%)']
    growth = valid_row['近四季稅後淨利年增率']
    try:
        peg = pe / (growth / 100) if pd.notnull(pe) and pd.notnull(growth) and growth not in [0, np.nan] else None
    except Exception:
        peg = None

    cheap_pe = valid_row['cheap_pe']
    low_pe = valid_row['low_pe']
    reasonable_pe = valid_row['reasonable_pe']
    high_pe = valid_row['high_pe']
    expensive_pe = valid_row['expensive_pe']

    cheap_price = valid_row['cheap_price']
    low_price = valid_row['low_price']
    reasonable_price = valid_row['reasonable_price']
    high_price = valid_row['high_price']
    expensive_price = valid_row['expensive_price']

    # === EPS估值法（合理PE * EPS）===
    eps_valuation_low = low_pe * eps if pd.notnull(reasonable_pe) and pd.notnull(eps) else None
    eps_valuation_reasonable = reasonable_pe * eps if pd.notnull(reasonable_pe) and pd.notnull(eps) else None
    eps_valuation_high = high_pe * eps if pd.notnull(reasonable_pe) and pd.notnull(eps) else None
    
    # === PEG估值法（年增率>0時，合理PEG=1）===
    if pd.notnull(eps) and pd.notnull(growth) and growth > 0:
        peg_valuation = round(eps * (growth / 100), 2)
        peg_valuation_note = ""
    else:
        peg_valuation = None
        if pd.notnull(growth) and growth <= 0:
            peg_valuation_note = "小心謹慎！無EPS或年增率為負或零，請參考基本面"
        else:
            peg_valuation_note = "小心謹慎！無EPS或年增率數據為負或零，請參考基本面"


    # === PB估值法（反推每股淨值，再*合理PB）===
    pb_valuation = None
    if pd.notnull(pb) and pb > 0 and pd.notnull(close):
        book_value_per_share = close / pb
        pb_valuation = book_value_per_share * 1  # 1倍PB

    # 組合所有估值資訊
    valuation = {
        "股票代號": stock_id,
        "評價日期": valid_row['Date'],
        "評價日股價": round(close, 3),
        "本益比(現)": round(pe, 3),
        "近四季累積EPS": round(eps, 3),
        "殖利率(%)": round(yield_, 3),
        "股價淨值比(PB)": round(pb, 3),
        "PEG": round(peg, 3) if peg is not None else None,
        "近四季稅後淨利年增率(%)": round(growth, 3) if peg is not None else None,
        # 各分位本益比估值
        "便宜本益比": cheap_pe,
        "便宜價": cheap_price,
        "偏低本益比": low_pe,
        "偏低價": low_price,
        "合理本益比": reasonable_pe,
        "合理價": reasonable_price,
        "偏高本益比": high_pe,
        "偏高價": high_price,
        "昂貴本益比": expensive_pe,
        "昂貴價": expensive_price,
        # EPS估值法
        "- EPS估值法(偏低PE*EPS)": round(eps_valuation_low, 2) if eps_valuation_low else None,
        "- EPS估值法(合理PE*EPS)": round(eps_valuation_reasonable, 2) if eps_valuation_reasonable else None,
        "- EPS估值法(偏高PE*EPS)": round(eps_valuation_high, 2) if eps_valuation_high else None,
        # PEG估值法
        "- PEG估值法(PEG=1)": peg_valuation if peg_valuation is not None else peg_valuation_note,
        # PB估值法
        "- PB估值法(1倍PB)": round(pb_valuation, 2) if pb_valuation else None,
    }

    # === 印出（可改成df或table輸出） ===
#     print('''
# 估值方法僅供參考：
# 1. EPS × 合理本益比法
#    - 適合大多數電子、科技、成長型公司，主流市場普遍採用
# 2. PEG法
#    - 屬於保守評價，適合小型高成長或景氣循環早段公司
#    - 用在成熟大型公司容易「嚴重低估」合理價值
# 3. PB法
#    - 僅適用資產型、銀行、壽險、傳產等產業
#    - 對電子、AI、品牌、軟體公司參考價值低，通常不可用
# ''')
#     print(f"股票代號: {valid_row['股票代號']} ({valid_row['產業類別']}) 最新有EPS資料日期: {valid_row['Date']}")
#     for k, v in valuation.items():
#         print(f"{k}: {v}")

    return valuation



# valuation = valuation_summary(merged_df_date, stock_id)
# valuation
