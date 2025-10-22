#%%
# 技術面比較 
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
from datetime import datetime, timedelta
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
import vectorbt as vbt
from plotly.subplots import make_subplots
import vectorbt as vbt
print("vectorbt version:", vbt.__version__)
print("vectorbt file:", vbt.__file__)


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


def _read_and_concat_sqlite_tables_tech():
    urls = [
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_1.sqlite3",
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_2.sqlite3",
        "https://github.com/06Cata/Taiwan_Stock/blob/main/merged_etf_index_pepb_3.sqlite3",
    ]
    table_names = [
        "merged_etf_index_pepb_1",
        "merged_etf_index_pepb_2",
        "merged_etf_index_pepb_3",
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


def _read_and_concat_sqlite_tables_tech_local():
    paths = [
        "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_1.sqlite3",
        "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_2.sqlite3",
        "/Users/catalinakuo/Downloads/for_git/Taiwan_Stock/merged_etf_index_pepb_3.sqlite3"
    ]
    table_names = [
        "merged_etf_index_pepb_1",
        "merged_etf_index_pepb_2",
        "merged_etf_index_pepb_3",
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
    return _read_and_concat_sqlite_tables_tech_local()


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
# cal ma
def add_ma_columns(df, ma_list=(5, 14, 20, 30, 60, 120, 240)):
    df = df.copy()
    for w in ma_list:
        ma_col = f'MA{w}'
        if ma_col not in df.columns:
            # groupby 股票代號，計算 rolling mean
            df[ma_col] = df.groupby('股票代號')['Close'].transform(lambda x: x.rolling(w, min_periods=1).mean())
    return df

# 
# daily_df_merge_index_pepb_selected_date_with_ma = add_ma_columns(daily_df_merge_index_pepb_selected_date)
# daily_df_merge_index_pepb_selected_date_with_ma


#%% 
# ADLs
def adls(daily_df_merge_index_pepb):
    df = daily_df_merge_index_pepb.copy()
    # 只保留「今天往前推一年」的資料
    today = pd.Timestamp.today().normalize()
    start_date = today - pd.Timedelta(days=200)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Date'] >= start_date]
    
    
    df = df.sort_values(['股票代號', 'Date'])
    df['昨日收盤'] = df.groupby('股票代號')['Close'].shift(1)
    df['漲跌'] = df['Close'] > df['昨日收盤']

    ad_stat = df.groupby('Date').agg(
        上漲家數 = ('漲跌', 'sum'),
        總家數 = ('股票代號', 'nunique'),
        收盤指數 = ('收盤指數', 'last')
    ).reset_index()

    ad_stat['ADLs'] = ad_stat['上漲家數'] / ad_stat['總家數'] - 0.5
    ad_stat['ADLs_fast'] = ad_stat['ADLs'].rolling(window=5, min_periods=1).mean()
    ad_stat['ADLs_slow'] = ad_stat['ADLs'].rolling(window=20, min_periods=1).mean()

    # 轉換 index 方便跑迴圈
    ad_stat = ad_stat.reset_index(drop=True)

    # =========== 金叉連續三天站穩才出訊號 ===========
    golden_signal_dates = []
    golden_cross_idx = ad_stat.index[
        (ad_stat['ADLs_fast'].shift(1) < ad_stat['ADLs_slow'].shift(1)) &
        (ad_stat['ADLs_fast'] >= ad_stat['ADLs_slow'])
    ]

    for idx in golden_cross_idx:
        # 五天都快線站在慢線上
        if idx + 5 < len(ad_stat):
            future_idx = range(idx, idx+6)
            if all(ad_stat.iloc[future_idx]['ADLs_fast'] > ad_stat.iloc[future_idx]['ADLs_slow']):
                golden_signal_dates.append(ad_stat.iloc[idx+2]['Date'])

    golden_dates = pd.Series(golden_signal_dates)

    # =========== 死叉連續五天站穩才出訊號 ===========
    dead_signal_dates = []
    dead_cross_idx = ad_stat.index[
        (ad_stat['ADLs_fast'].shift(1) > ad_stat['ADLs_slow'].shift(1)) &
        (ad_stat['ADLs_fast'] <= ad_stat['ADLs_slow']) &
        (ad_stat['ADLs'] < 0)
    ]
    for idx in dead_cross_idx:
        if idx + 4 < len(ad_stat):
            future_idx = range(idx, idx+5)
            if all(ad_stat.iloc[future_idx]['ADLs_fast'] < ad_stat.iloc[future_idx]['ADLs_slow']):
                dead_signal_dates.append(ad_stat.iloc[idx+2]['Date'])

    dead_dates = pd.Series(dead_signal_dates)

    # =========== 畫圖 ==============
    fig = go.Figure()

    # ADLs原始
    fig.add_trace(go.Scatter(
        x=ad_stat['Date'], y=ad_stat['ADLs'],
        mode='lines', name='ADLs (原始)', line=dict(width=1, color='gray')
    ))
    # ADLs 快線
    fig.add_trace(go.Scatter(
        x=ad_stat['Date'], y=ad_stat['ADLs_fast'],
        mode='lines', name='ADLs快線(5日)', line=dict(width=2, color='blue')
    ))
    # ADLs 慢線
    fig.add_trace(go.Scatter(
        x=ad_stat['Date'], y=ad_stat['ADLs_slow'],
        mode='lines', name='ADLs慢線(20日)', line=dict(width=2, color='red')
    ))
    # 大盤指數（右側Y軸）
    fig.add_trace(go.Scatter(
        x=ad_stat['Date'], y=ad_stat['收盤指數'],
        mode='lines', name='收盤指數', line=dict(width=1.2, color='green', dash='dot'),
        yaxis='y2'
    ))

    # 畫橘色金叉訊號線
    for date in golden_dates:
        fig.add_shape(
            type="line",
            x0=date, x1=date,
            y0=ad_stat['ADLs'].min(), y1=ad_stat['ADLs'].max(),
            line=dict(color='orange', width=2, dash='dot'),
            layer='above'
        )

    # 畫灰色死叉訊號線
    for date in dead_dates:
        fig.add_shape(
            type="line",
            x0=date, x1=date,
            y0=ad_stat['ADLs'].min(), y1=ad_stat['ADLs'].max(),
            line=dict(color='gray', width=2, dash='dot'),
            layer='above'
        )

    fig.update_layout(
        title='ADLs快慢線（5/20日）與大盤指數走勢\n(橘:連續五天快>慢，多頭進場/加碼, 灰:連續五天快<慢，觀望/減碼)',
        xaxis=dict(title='Date'),
        yaxis=dict(title='ADLs'),
        yaxis2=dict(
            title='收盤指數',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        width=900,
        height=450,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.3,
        xanchor='center',
        x=0.5
    )
)

    return fig

# fig = adls(daily_df_merge_index_pepb)
# fig.show()



#%%
# 盒鬚圖 + 多MA 

def plotly_k_ma_with_volume(
    df, stock_industry:str, stock_name:str, stock_id:str, 
    ma_list=(5, 14, 20, 30, 60, 120, 240), 
    vol_ma_list=(5, 10)):
    # 數字轉型
    for col in ['Close', 'High', 'Low', 'Open', '個股成交量']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')

    # 過濾個股
    if '股票代號' in df.columns and stock_id is not None:
        data = df[df['股票代號'] == stock_id].copy()
    else:
        data = df.copy()
    data = data.sort_values('Date')
    data = data.dropna(subset=['Date','Open','High','Low','Close','個股成交量'])

    # 成交量均線（如果還沒加過就加）
    for vma in vol_ma_list:
        vma_col = f'VOL_MA{vma}'
        if vma_col not in data.columns:
            data[vma_col] = data['個股成交量'].rolling(vma, min_periods=1).mean()

    # ==== 用 make_subplots 畫主副圖 ====
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.06,
        subplot_titles=(f"{stock_industry} {stock_id} {stock_name}｜K棒＋MA", "成交量（含均線）")
    )

    # ====== 主圖：K棒 + 多MA =====
    fig.add_trace(go.Candlestick(
        x=data['Date'],
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        increasing_line_color='red',
        decreasing_line_color='green',
        name='K棒'
    ), row=1, col=1)

    # 收盤價線
    fig.add_trace(go.Scatter(
        x=data['Date'],
        y=data['Close'],
        mode='lines',
        name='收盤價',
        line=dict(width=1.2, color='red')
    ), row=1, col=1)

    # 多條MA（直接抓欄位）
    ma_colors = ['royalblue', 'green', 'orange', 'purple', 'deeppink', 'brown', 'gray']
    for idx, w in enumerate(ma_list):
        ma_col = f'MA{w}'
        if ma_col in data.columns:
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=data[ma_col],
                mode='lines',
                name=f'MA{w}',
                line=dict(width=1.5, color=ma_colors[idx % len(ma_colors)])
            ), row=1, col=1)

    # ====== 副圖：成交量（紅漲綠跌） ======
    inc = data['Close'] >= data['Open']
    dec = data['Close'] < data['Open']
    fig.add_trace(go.Bar(
        x=data['Date'][inc], y=data['個股成交量'][inc],
        marker_color='red', name='漲成交量', showlegend=False
    ), row=2, col=1)
    fig.add_trace(go.Bar(
        x=data['Date'][dec], y=data['個股成交量'][dec],
        marker_color='green', name='跌成交量', showlegend=False
    ), row=2, col=1)

    # 成交量均線
    for idx, vma in enumerate(vol_ma_list):
        vma_col = f'VOL_MA{vma}'
        if vma_col in data.columns:
            fig.add_trace(go.Scatter(
                x=data['Date'], y=data[vma_col],
                mode='lines',
                line=dict(width=1.2, dash='dot'),
                name=f'成交量MA{vma}'
            ), row=2, col=1)

    # ====== 格式 ======
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        width=1000, height=700,
        hovermode='x unified',
        # legend=dict(orientation='h', x=0, y=1.02),
        margin=dict(l=60, r=20, t=60, b=40),
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.1,
        xanchor='center',
        x=0.5
    )
    )
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    return fig


# fig = plotly_k_ma_with_volume(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id, ma_list=(5, 14, 20, 30, 60, 120, 240), vol_ma_list=(5, 10))
# fig.show()


#%%
# Close、20 MA
def plotly_tec_close_ma_20_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):
    df_ma = daily_df_merge_index_pepb_selected_date_with_ma.copy()
    if '股票代號' in df_ma.columns and stock_id is not None:
        df_ma = df_ma[df_ma['股票代號'] == stock_id]

    df_ma['Date'] = pd.to_datetime(df_ma['Date'], format='%Y%m%d', errors='coerce')
    for c in ['Open', 'High', 'Low', 'Close', 'MA20', '收盤指數']:
        if c in df_ma.columns:
            df_ma[c] = pd.to_numeric(df_ma[c], errors='coerce')
    df_ma = df_ma.dropna(subset=['Date', 'Open', 'High', 'Low', 'Close', 'MA20']).sort_values('Date')
    if df_ma.empty:
        return go.Figure(), go.Figure(), None, None

    # ======= fig 主圖（收盤+20MA） =======
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['Close'],
                             mode='lines', line=dict(color='red', width=1.5), name='收盤價'))
    fig.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['MA20'],
                             mode='lines', line=dict(color='purple', width=1.5), name='20MA'))

    buy_signal = (df_ma['Close'].shift(1) < df_ma['MA20'].shift(1)) & (df_ma['Close'] >= df_ma['MA20'])
    sell_signal = (df_ma['Close'].shift(1) > df_ma['MA20'].shift(1)) & (df_ma['Close'] <= df_ma['MA20'])

    for date in df_ma.loc[buy_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df_ma['Close'].min(), y1=df_ma['Close'].max(),
                      line=dict(color='orange', width=2, dash='dot'), layer='above')
    for date in df_ma.loc[sell_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df_ma['Close'].min(), y1=df_ma['Close'].max(),
                      line=dict(color='gray', width=2, dash='dot'), layer='above')

    fig.update_layout(
        title=f'{stock_industry}{stock_id} {stock_name} 收盤價、20MA 趨勢線<br>橘色虛線=買入(突破20MA)、灰色虛線=賣出(跌破20MA)',
        xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
        yaxis=dict(title='收盤價'),
        width=900,
        height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
    )
)

    # ======= fig2（大盤指數圖）=======
    fig2 = go.Figure()
    if '收盤指數' in df_ma.columns:
        y_range2 = [df_ma['收盤指數'].min(), df_ma['收盤指數'].max()]
        fig2.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['收盤指數'],
                                  mode='lines', line=dict(color='red', width=1.5),
                                  name='收盤指數'))
        fig2.update_layout(
            title=f'{stock_id} 收盤指數',
            xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
            yaxis=dict(title='收盤指數', range=y_range2),
            legend=dict(title='', x=1.0, y=1.15, traceorder='normal', orientation='v'),
            width=900,
            height=250,
        )

    # ======= 用 vectorbt 做績效（fig3, fig4）=======
    df_ma = df_ma.set_index('Date')
    entries = (df_ma['Close'].shift(1) < df_ma['MA20'].shift(1)) & (df_ma['Close'] >= df_ma['MA20'])
    exits   = (df_ma['Close'].shift(1) > df_ma['MA20'].shift(1)) & (df_ma['Close'] <= df_ma['MA20'])

    pf = vbt.Portfolio.from_signals(
        close=df_ma['Close'],
        entries=entries,
        exits=exits,
        price=df_ma['Open'],
        fees=0.001425,
        slippage=0.0005,
        init_cash=1_000_000,
        size=1000,
        direction='longonly'
    )

    trades = pf.trades.records.copy()
    fig3 = None
    fig4 = None
    if not trades.empty:
        # 欄位標準化
        trades.columns = [col.strip().lower() for col in trades.columns]
        # 用 entry_idx/exit_idx 還原回日期
        trades['買入日期'] = df_ma.index[trades['entry_idx']]
        trades['賣出日期'] = df_ma.index[trades['exit_idx']]
        trades['買入金額'] = trades['entry_price'].round(3)
        trades['賣出金額'] = trades['exit_price'].round(3)
        trades['單次獲利(元)'] = trades['pnl'].round(0).astype(int)
        trades['收益(%)'] = (trades['return'] * 100).round(2)
        trades_show = trades[['買入日期', '買入金額', '賣出日期', '賣出金額', '單次獲利(元)', '收益(%)']].copy()
        trades_show['買入日期'] = trades_show['買入日期'].dt.strftime('%Y-%m-%d')
        trades_show['賣出日期'] = trades_show['賣出日期'].dt.strftime('%Y-%m-%d')

        fig3 = go.Figure(data=[go.Table(
            header=dict(values=list(trades_show.columns),
                        fill_color='paleturquoise',
                        align='center'),
            cells=dict(values=[trades_show[col] for col in trades_show.columns],
                    fill_color='lavender',
                    align='center'))
        ])
        fig3.update_layout(
            title=f"vectorbt MA20 策略交易明細：{stock_id}",
            width=900, height=350
        )

        equity_curve = pf.value()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode='lines',
            line=dict(color='royalblue', width=1.5),
            name='資產走勢'
        ))
        fig4.update_layout(
            title=f'vectorbt MA20 策略資產走勢：{stock_id}',
            xaxis_title='日期',
            yaxis_title='資產(元)',
            width=900,
            height=250
        )

    return fig, fig2, fig3, fig4

# fig, fig2, fig3, fig4 = plotly_tec_close_ma_20_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)

# fig.show()
# fig2.show()
# if fig3 is not None and fig4 is not None:
#     fig3.show()
#     fig4.show()
# else:
#     print("⚠️ 沒有任何成交紀錄，不顯示 fig3/fig4")



#%%
# 20MA 60MA
def plotly_tec_ma_20_and_60_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):
    df_ma = daily_df_merge_index_pepb_selected_date_with_ma.copy()
    if '股票代號' in df_ma.columns and stock_id is not None:
        df_ma = df_ma[df_ma['股票代號'] == stock_id]

    df_ma['Date'] = pd.to_datetime(df_ma['Date'], format='%Y%m%d', errors='coerce')
    for c in ['Open','High','Low','Close','MA20','MA60','收盤指數']:
        if c in df_ma.columns:
            df_ma[c] = pd.to_numeric(df_ma[c], errors='coerce')
    df_ma = df_ma.dropna(subset=['Date','Open','High','Low','Close','MA20','MA60']).sort_values('Date')
    if df_ma.empty:
        return go.Figure(), go.Figure(), None, None

    # 主圖
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['Close'],
                             mode='lines', line=dict(color='red', width=1.2), name='收盤價'))
    fig.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['MA20'],
                             mode='lines', line=dict(color='purple', width=1.5), name='20MA'))
    fig.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['MA60'],
                             mode='lines', line=dict(color='green', width=1.5), name='60MA'))

    buy_signal = (df_ma['MA20'].shift(1) < df_ma['MA60'].shift(1)) & (df_ma['MA20'] >= df_ma['MA60'])
    sell_signal = (df_ma['MA20'].shift(1) > df_ma['MA60'].shift(1)) & (df_ma['MA20'] <= df_ma['MA60'])

    for date in df_ma.loc[buy_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df_ma['Close'].min(), y1=df_ma['Close'].max(),
                      line=dict(color='orange', width=2, dash='dot'), layer='above')
    for date in df_ma.loc[sell_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df_ma['Close'].min(), y1=df_ma['Close'].max(),
                      line=dict(color='gray', width=2, dash='dot'), layer='above')

    y_range = [df_ma['Close'].min(), df_ma['Close'].max()]
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 收盤價、20MA、60MA 趨勢線<br>橘色虛線=買入(金叉)、灰色虛線=賣出(死叉)',
        xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
        yaxis=dict(title='收盤價', range=y_range),
        width=900,
        height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
    )
)


    # 指數圖
    fig2 = go.Figure()
    if '收盤指數' in df_ma.columns:
        y_range2 = [df_ma['收盤指數'].min(), df_ma['收盤指數'].max()]
        fig2.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['收盤指數'],
                                  mode='lines', line=dict(color='red', width=1.5),
                                  name='收盤指數'))
        fig2.update_layout(
            title=f'{stock_id} 收盤指數',
            xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
            yaxis=dict(title='收盤指數', range=y_range2),
            legend=dict(
                title='',
                x=1.0,
                y=1.15,
                traceorder='normal',
                orientation='v'
            ),
            width=900,
            height=250,
        )

    # ======= 用 vectorbt 做績效（fig3, fig4）=======
    df_ma = df_ma.set_index('Date')
    entries = (df_ma['MA20'].shift(1) < df_ma['MA60'].shift(1)) & (df_ma['MA20'] >= df_ma['MA60'])
    exits   = (df_ma['MA20'].shift(1) > df_ma['MA60'].shift(1)) & (df_ma['MA20'] <= df_ma['MA60'])

    pf = vbt.Portfolio.from_signals(
        close=df_ma['Close'],
        entries=entries,
        exits=exits,
        price=df_ma['Open'],
        fees=0.001425,
        slippage=0.0005,
        init_cash=1_000_000,
        size=1000,
        direction='longonly'
    )

    trades = pf.trades.records.copy()
    fig3 = None
    fig4 = None
    if not trades.empty:
        trades.columns = [col.strip().lower() for col in trades.columns]
        trades['買入日期'] = df_ma.index[trades['entry_idx']]
        trades['賣出日期'] = df_ma.index[trades['exit_idx']]
        trades['買入金額'] = trades['entry_price'].round(3)
        trades['賣出金額'] = trades['exit_price'].round(3)
        trades['單次獲利(元)'] = trades['pnl'].round(0).astype(int)
        trades['收益(%)'] = (trades['return'] * 100).round(2)
        trades_show = trades[['買入日期', '買入金額', '賣出日期', '賣出金額', '單次獲利(元)', '收益(%)']].copy()
        trades_show['買入日期'] = trades_show['買入日期'].dt.strftime('%Y-%m-%d')
        trades_show['賣出日期'] = trades_show['賣出日期'].dt.strftime('%Y-%m-%d')

        fig3 = go.Figure(data=[go.Table(
            header=dict(values=list(trades_show.columns),
                        fill_color='paleturquoise',
                        align='center'),
            cells=dict(values=[trades_show[col] for col in trades_show.columns],
                    fill_color='lavender',
                    align='center'))
        ])
        fig3.update_layout(
            title=f"vectorbt MA20/60MA 策略交易明細：{stock_id}",
            width=900, height=350
        )

        equity_curve = pf.value()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode='lines',
            line=dict(color='royalblue', width=1.5),
            name='資產走勢'
        ))
        fig4.update_layout(
            title=f'vectorbt MA20/60MA 策略資產走勢：{stock_id}',
            xaxis_title='日期',
            yaxis_title='資產(元)',
            width=900,
            height=250
        )

    return fig, fig2, fig3, fig4



# fig, fig2, fig3, fig4 = plotly_tec_ma_20_and_60_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)

# fig.show()
# fig2.show()
# if fig3 is not None and fig4 is not None:
#     fig3.show()
#     fig4.show()
# else:
#     print("⚠️ 沒有任何成交紀錄，不顯示 fig3/fig4")


#%%
# best ma
def find_best_sma_cross(daily_df_merge_index_pepb_selected_date_with_ma, equity_init=1_000_000, n1_range=range(5, 60, 5), n2_range=range(10, 200, 10)):
    
    df = daily_df_merge_index_pepb_selected_date_with_ma.copy()
    
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.set_index('Date')
        df = df.sort_index()
        
    results = []
    best_pf = None
    best_pair = None
    best_return = -np.inf

    close = df['Close']
    # 1. 強制 index 為 Datetime 並補 freq 為 'D'
    if not isinstance(close.index, pd.DatetimeIndex):
        raise ValueError('你的資料 index 需為 DatetimeIndex')
    close = close.asfreq('D')  # 這樣就能讓 vectorbt 各種年化報酬都不卡

    for n1 in n1_range:
        for n2 in n2_range:
            if n1 >= n2:
                continue
            sma1 = close.rolling(window=n1).mean()
            sma2 = close.rolling(window=n2).mean()

            entries = (sma1.shift(1) < sma2.shift(1)) & (sma1 >= sma2)
            exits   = (sma1.shift(1) > sma2.shift(1)) & (sma1 <= sma2)

            # 將所有 signal 補齊和 close 一樣長度、且 index 完全一致
            signals_index = close.index
            entries = entries.reindex(signals_index, fill_value=False)
            exits   = exits.reindex(signals_index, fill_value=False)
            price = df['Open'].reindex(signals_index, fill_value=np.nan) if 'Open' in df.columns else close

            pf = vbt.Portfolio.from_signals(
                close=close,
                entries=entries,
                exits=exits,
                price=price,
                fees=0.001425,
                slippage=0.0005,
                init_cash=equity_init,
                size=1000,
                direction='longonly'
            )

            total_return = pf.total_return()
            results.append({
                'n1': n1,
                'n2': n2,
                '總報酬率(%)': round(total_return*100, 2),
                '年化報酬率(%)': round(pf.annualized_return()*100, 2),
                '交易次數': int(pf.trades.count()),
                'max_drawdown(%)': round(pf.max_drawdown()*100, 2),
                'sharpe': round(pf.sharpe_ratio(), 2),
                'pf_obj': pf
            })
            if total_return > best_return:
                best_return = total_return
                best_pair = (n1, n2)
                best_pf = pf

    results_df = pd.DataFrame(results).sort_values('總報酬率(%)', ascending=False)
    return {
        'best_n1': best_pair[0],
        'best_n2': best_pair[1],
        'best_pf': best_pf,
        'results_df': results_df
    }


def plotly_tec_best_sma_cross_vectorbt(
    daily_df,     # 輸入已經有MA欄位的df
    stock_industry, stock_name, stock_id,
    n1, n2        # 你要用的最佳 SMA period
):
    df_ma = daily_df.copy()
    if '股票代號' in df_ma.columns and stock_id is not None:
        df_ma = df_ma[df_ma['股票代號'] == stock_id]
    df_ma['Date'] = pd.to_datetime(df_ma['Date'], format='%Y%m%d', errors='coerce')

    df_ma[f'MA{n1}'] = df_ma['Close'].rolling(window=n1, min_periods=1).mean()
    df_ma[f'MA{n2}'] = df_ma['Close'].rolling(window=n2, min_periods=1).mean()

    # 動態補足欄位
    for c in ['Open', 'High', 'Low', 'Close', f'MA{n1}', f'MA{n2}', '收盤指數']:
        if c in df_ma.columns:
            df_ma[c] = pd.to_numeric(df_ma[c], errors='coerce')

    df_ma = df_ma.dropna(subset=['Date', 'Open', 'High', 'Low', 'Close', f'MA{n1}', f'MA{n2}']).sort_values('Date')
    if df_ma.empty:
        return go.Figure(), go.Figure(), None, None

    # --- 主圖 ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['Close'],
                             mode='lines', line=dict(color='red', width=1.2), name='收盤價'))
    fig.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma[f'MA{n1}'],
                             mode='lines', line=dict(color='purple', width=1.5), name=f'{n1}MA'))
    fig.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma[f'MA{n2}'],
                             mode='lines', line=dict(color='green', width=1.5), name=f'{n2}MA'))

    # 金叉買進、死叉賣出
    buy_signal = (df_ma[f'MA{n1}'].shift(1) < df_ma[f'MA{n2}'].shift(1)) & (df_ma[f'MA{n1}'] >= df_ma[f'MA{n2}'])
    sell_signal = (df_ma[f'MA{n1}'].shift(1) > df_ma[f'MA{n2}'].shift(1)) & (df_ma[f'MA{n1}'] <= df_ma[f'MA{n2}'])

    for date in df_ma.loc[buy_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df_ma['Close'].min(), y1=df_ma['Close'].max(),
                      line=dict(color='orange', width=2, dash='dot'), layer='above')
    for date in df_ma.loc[sell_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df_ma['Close'].min(), y1=df_ma['Close'].max(),
                      line=dict(color='gray', width=2, dash='dot'), layer='above')

    y_range = [df_ma['Close'].min(), df_ma['Close'].max()]
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 收盤價、{n1}MA、{n2}MA 趨勢線<br>橘色虛線=買入(金叉)、灰色虛線=賣出(死叉)',
        xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
        yaxis=dict(title='收盤價', range=y_range),
        width=900,
        height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
    )
)

    # --- 指數圖 ---
    fig2 = go.Figure()
    if '收盤指數' in df_ma.columns:
        y_range2 = [df_ma['收盤指數'].min(), df_ma['收盤指數'].max()]
        fig2.add_trace(go.Scatter(x=df_ma['Date'], y=df_ma['收盤指數'],
                                  mode='lines', line=dict(color='red', width=1.5), name='收盤指數'))
        fig2.update_layout(
            title=f'{stock_id} 收盤指數',
            xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
            yaxis=dict(title='收盤指數', range=y_range2),
            legend=dict(
                title='',
                x=1.0, y=1.15, traceorder='normal', orientation='v'
            ),
            width=900, height=250,
        )

    # --- vectorbt績效 ---
    df_ma = df_ma.set_index('Date')
    entries = (df_ma[f'MA{n1}'].shift(1) < df_ma[f'MA{n2}'].shift(1)) & (df_ma[f'MA{n1}'] >= df_ma[f'MA{n2}'])
    exits   = (df_ma[f'MA{n1}'].shift(1) > df_ma[f'MA{n2}'].shift(1)) & (df_ma[f'MA{n1}'] <= df_ma[f'MA{n2}'])

    pf = vbt.Portfolio.from_signals(
        close=df_ma['Close'],
        entries=entries,
        exits=exits,
        price=df_ma['Open'],
        fees=0.001425,
        slippage=0.0005,
        init_cash=1_000_000,
        size=1000,
        direction='longonly'
    )

    trades = pf.trades.records.copy()
    fig3 = None
    fig4 = None
    if not trades.empty:
        trades.columns = [col.strip().lower() for col in trades.columns]
        trades['買入日期'] = df_ma.index[trades['entry_idx']]
        trades['賣出日期'] = df_ma.index[trades['exit_idx']]
        trades['買入金額'] = trades['entry_price'].round(3)
        trades['賣出金額'] = trades['exit_price'].round(3)
        trades['單次獲利(元)'] = trades['pnl'].round(0).astype(int)
        trades['收益(%)'] = (trades['return'] * 100).round(2)
        trades_show = trades[['買入日期', '買入金額', '賣出日期', '賣出金額', '單次獲利(元)', '收益(%)']].copy()
        trades_show['買入日期'] = trades_show['買入日期'].dt.strftime('%Y-%m-%d')
        trades_show['賣出日期'] = trades_show['賣出日期'].dt.strftime('%Y-%m-%d')

        fig3 = go.Figure(data=[go.Table(
            header=dict(values=list(trades_show.columns),
                        fill_color='paleturquoise', align='center'),
            cells=dict(values=[trades_show[col] for col in trades_show.columns],
                    fill_color='lavender', align='center'))
        ])
        fig3.update_layout(
            title=f"vectorbt {n1}/{n2}MA 策略交易明細：{stock_id}",
            width=900, height=350
        )

        equity_curve = pf.value()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=equity_curve.index, y=equity_curve.values,
            mode='lines', line=dict(color='royalblue', width=1.5),
            name='資產走勢'
        ))
        fig4.update_layout(
            title=f'vectorbt {n1}/{n2}MA 策略資產走勢：{stock_id}',
            xaxis_title='日期', yaxis_title='資產(元)', width=900, height=250
        )

    return fig, fig2, fig3, fig4


# result = find_best_sma_cross(daily_df_merge_index_pepb_selected_date_with_ma)
# n1, n2 = result['best_n1'], result['best_n2']


# fig, fig2, fig3, fig4 = plotly_tec_best_sma_cross_vectorbt(
#     daily_df_merge_index_pepb_selected_date_with_ma,
#     stock_industry, stock_name, stock_id,
#     n1=n1, n2=n2
# )

# fig.show()
# fig2.show()
# if fig3 is not None and fig4 is not None:
#     fig3.show()
#     fig4.show()
# else:
#     print("⚠️ 沒有任何成交紀錄，不顯示 fig3/fig4")



#%%
# RSI 9、RSI 14

def plotly_tec_rsi9_14_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):
    def calc_rsi_wilder(x, window):
        diff = x.diff()
        gain = diff.clip(lower=0)
        loss = -diff.clip(upper=0)
        avg_gain = gain.rolling(window, min_periods=window).mean()
        avg_loss = loss.rolling(window, min_periods=window).mean()
        rsi = pd.Series(np.nan, index=x.index)
        ag, al = np.nan, np.nan
        for i in range(len(x)):
            if i < window:
                continue
            elif i == window:
                ag = avg_gain.iloc[i]
                al = avg_loss.iloc[i]
            else:
                ag = (ag * (window - 1) + gain.iloc[i]) / window
                al = (al * (window - 1) + loss.iloc[i]) / window
            rs = ag / al if al != 0 else np.nan
            rsi.iloc[i] = 100 - 100 / (1 + rs)
        return rsi

    df = daily_df_merge_index_pepb_selected_date_with_ma.copy()
    if '股票代號' in df.columns and stock_id is not None:
        df = df[df['股票代號'] == stock_id]

    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
    for c in ['Open','High','Low','Close','收盤指數']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['Date','Open','High','Low','Close']).sort_values('Date')

    df['RSI9'] = calc_rsi_wilder(df['Close'], 9)
    df['RSI14'] = calc_rsi_wilder(df['Close'], 14)
    df = df.dropna(subset=['RSI9', 'RSI14'])

    if df.empty:
        return go.Figure(), go.Figure(), None, None, go.Figure()
    
    # ===== 主圖：收盤價 =====
    fig = go.Figure()
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['Close'],
            mode='lines', line=dict(color='red', width=1.2), name='收盤價'
        ))
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['RSI9'],
            mode='lines', line=dict(color='blue', width=1.2), name='RSI9',
            yaxis='y2'
        ))
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['RSI14'],
            mode='lines', line=dict(color='green', width=1.2), name='RSI14',
            yaxis='y2'
        ))

    y_range = [df['Close'].min(), df['Close'].max()]
    rsi_min = min(df['RSI9'].min(), df['RSI14'].min())
    rsi_max = max(df['RSI9'].max(), df['RSI14'].max())
    y_range2 = [rsi_min-5, rsi_max+5]
    
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} 收盤價走勢 (RSI9/14 金叉死叉策略)',
        xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
        yaxis=dict(title='收盤價', range=y_range),
        yaxis2=dict(
            title='RSI', side='right', overlaying='y', range=y_range2,
            showgrid=False, tickvals=[0, 30, 50, 70, 100]
        ),
        width=900, height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
        )
    )
    
    # ===== RSI 金叉死叉訊號 =====
    buy_signal = (df['RSI9'].shift(1) < df['RSI14'].shift(1)) & (df['RSI9'] >= df['RSI14'])
    sell_signal = (df['RSI9'].shift(1) > df['RSI14'].shift(1)) & (df['RSI9'] <= df['RSI14'])
    for date in df.loc[buy_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df['Close'].min(), y1=df['Close'].max(),
                      line=dict(color='orange', width=2, dash='dot'), layer='above')
    for date in df.loc[sell_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df['Close'].min(), y1=df['Close'].max(),
                      line=dict(color='gray', width=2, dash='dot'), layer='above')

    # ====== 指數圖 ======
    fig2 = go.Figure()
    if '收盤指數' in df.columns:
        y_range2 = [df['收盤指數'].min(), df['收盤指數'].max()]
        fig2.add_trace(go.Scatter(x=df['Date'], y=df['收盤指數'],
                                  mode='lines', line=dict(color='red', width=1.5),
                                  name='收盤指數'))
        fig2.update_layout(
            title=f'{stock_id} 收盤指數',
            xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
            yaxis=dict(title='收盤指數', range=y_range2),
            legend=dict(title='', x=1.0, y=1.15, traceorder='normal', orientation='v'),
            width=900, height=250,
        )

    # ======= vectorbt 回測 =======
    df = df.set_index('Date')
    entries = (df['RSI9'].shift(1) < df['RSI14'].shift(1)) & (df['RSI9'] >= df['RSI14'])
    exits   = (df['RSI9'].shift(1) > df['RSI14'].shift(1)) & (df['RSI9'] <= df['RSI14'])
    if entries.sum() > exits.sum():
        exits.iloc[-1] = True

    pf = vbt.Portfolio.from_signals(
        close=df['Close'],
        entries=entries,
        exits=exits,
        price=df['Open'],
        fees=0.001425,
        slippage=0.0005,
        init_cash=1_000_000,
        size=1000,
        direction='longonly',
        # stop_loss = dict(stop=0.1),    
        # take_profit = dict(stop=0.2),
    )

    trades = pf.trades.records.copy()
    fig3 = None
    fig4 = None
    if not trades.empty:
        trades.columns = [col.strip().lower() for col in trades.columns]
        trades['買入日期'] = df.index[trades['entry_idx']]
        trades['賣出日期'] = df.index[trades['exit_idx']]
        trades['買入金額'] = trades['entry_price'].round(3)
        trades['賣出金額'] = trades['exit_price'].round(3)
        trades['單次獲利(元)'] = trades['pnl'].round(0).astype(int)
        trades['收益(%)'] = (trades['return'] * 100).round(2)
        trades_show = trades[['買入日期', '買入金額', '賣出日期', '賣出金額', '單次獲利(元)', '收益(%)']].copy()
        trades_show['買入日期'] = trades_show['買入日期'].dt.strftime('%Y-%m-%d')
        trades_show['賣出日期'] = trades_show['賣出日期'].dt.strftime('%Y-%m-%d')

        fig3 = go.Figure(data=[go.Table(
            header=dict(values=list(trades_show.columns),
                        fill_color='paleturquoise',
                        align='center'),
            cells=dict(values=[trades_show[col] for col in trades_show.columns],
                    fill_color='lavender',
                    align='center'))
        ])
        fig3.update_layout(
            title=f"vectorbt RSI9/RSI14 策略交易明細：{stock_id}",
            width=900, height=350
        )

        equity_curve = pf.value()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode='lines',
            line=dict(color='royalblue', width=1.5),
            name='資產走勢'
        ))
        fig4.update_layout(
            title=f'vectorbt RSI9/RSI14 策略資產走勢：{stock_id}',
            xaxis_title='日期',
            yaxis_title='資產(元)',
            width=900,
            height=250
        )

    stats = pf.stats()
    
    return fig, fig2, fig3, fig4, stats 


# fig, fig2, fig3, fig4, stats = plotly_tec_rsi9_14_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)

# fig.show()
# fig2.show()

# if fig3 is not None and fig4 is not None:
#     fig3.show()
#     fig4.show()
#     display(stats)
# else:
#     print("⚠️ 沒有任何成交紀錄，不顯示 fig3/fig4")



#%%
# RSV、KD 
def plotly_tec_kd_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):

    # ====== 計算 RSV9 ======
    def calc_rsv(df, kd_period=9):
        df = df.copy()
        df = df.sort_values(['股票代號', 'Date'])
        df[f'Low_min_{kd_period}'] = df.groupby('股票代號')['Low'].transform(lambda x: x.rolling(kd_period, min_periods=kd_period).min())
        df[f'High_max_{kd_period}'] = df.groupby('股票代號')['High'].transform(lambda x: x.rolling(kd_period, min_periods=kd_period).max())
        df[f'RSV{kd_period}'] = (df['Close'] - df[f'Low_min_{kd_period}']) / (df[f'High_max_{kd_period}'] - df[f'Low_min_{kd_period}']) * 100
        def drop_inner_nan(group):
            idx_to_keep = group.index[:kd_period-1]
            nan_mask = group[f'RSV{kd_period}'].isna()
            drop_idx = group.index[(nan_mask) & (~group.index.isin(idx_to_keep))]
            return group.drop(index=drop_idx)
        df = df.groupby('股票代號', group_keys=False).apply(drop_inner_nan)
        df = df.reset_index(drop=True)
        return df

    # ====== 計算 K9、D9、J9 ======
    def calc_kd(df, kd_period=9):
        df = df.copy()
        def _kd_group(rsv):
            k_list = [50]
            d_list = [50]
            for i in range(1, len(rsv)):
                if pd.isna(rsv.iloc[i]):
                    k = np.nan
                    d = np.nan
                else:
                    prev_k = k_list[-1] if not pd.isna(k_list[-1]) else 50
                    prev_d = d_list[-1] if not pd.isna(d_list[-1]) else 50
                    k = prev_k * 2 / 3 + rsv.iloc[i] * 1 / 3
                    d = prev_d * 2 / 3 + k * 1 / 3
                k_list.append(k)
                d_list.append(d)
            return pd.DataFrame({'K': k_list, 'D': d_list}, index=rsv.index)
        kd_df = df.groupby('股票代號')[f'RSV{kd_period}'].apply(_kd_group).reset_index(level=0, drop=True)
        df[f'K{kd_period}'] = kd_df['K'].values
        df[f'D{kd_period}'] = kd_df['D'].values
        df[f'J{kd_period}'] = 3 * df[f'K{kd_period}'] - 2 * df[f'D{kd_period}']
        df[f'K{kd_period}'] = df[f'K{kd_period}'].round(2)
        df[f'D{kd_period}'] = df[f'D{kd_period}'].round(2)
        df[f'J{kd_period}'] = df[f'J{kd_period}'].round(2)
        return df

    # ====== 前處理 ======
    df = daily_df_merge_index_pepb_selected_date_with_ma.copy()
    if '股票代號' in df.columns and stock_id is not None:
        df = df[df['股票代號'] == stock_id]
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
    for c in ['Open','High','Low','Close','收盤指數']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['Date','Open','High','Low','Close']).sort_values('Date')
    if df.empty:
        return go.Figure(), go.Figure(), None, None, go.Figure()

    # ====== 計算 RSV、KD ======
    df = calc_rsv(df, kd_period=9)
    df = calc_kd(df, kd_period=9)
    df = df.dropna(subset=['K9', 'D9'])

    # ===== 主圖（收盤+K9/D9金叉死叉點） =====
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'],
                             mode='lines', line=dict(color='red', width=1.2), name='收盤價'))
    
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['K9'],
            mode='lines', line=dict(color='blue', width=1.2), name='K9',
            yaxis='y2'
        ))
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['D9'],
            mode='lines', line=dict(color='green', width=1.2), name='D9',
            yaxis='y2'
        ))
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['J9'],
            mode='lines', line=dict(color='pink', width=1.2), name='J9',
            yaxis='y2'
        ))
    
    y_range = [df['Close'].min(), df['Close'].max()]
    kdj_min = min(df['K9'].min(), df['D9'].min(), df['J9'].min())
    kdj_max = max(df['K9'].max(), df['D9'].max(), df['J9'].max())
    y_range2 = [kdj_min-5, kdj_max+5]

    # KD 金叉/死叉
    # buy_signal = (df['K9'].shift(1) < df['D9'].shift(1)) & (df['K9'] >= df['D9'])
    # sell_signal = (df['K9'].shift(1) > df['D9'].shift(1)) & (df['K9'] <= df['D9'])
    buy_signal = (
        (df['K9'].shift(1) < df['D9'].shift(1)) &  # 前一天K9在D9下方
        (df['K9'] >= df['D9'])                     # 當天K9上穿D9
    )
    sell_signal = (
        (df['K9'].shift(1) > df['D9'].shift(1)) &  # 前一天K9在D9上方
        (df['K9'] <= df['D9'])                     # 當天K9下穿D9
    )

    for date in df.loc[buy_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df['Close'].min(), y1=df['Close'].max(),
                      line=dict(color='orange', width=2, dash='dot'), layer='above')
    for date in df.loc[sell_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=df['Close'].min(), y1=df['Close'].max(),
                      line=dict(color='gray', width=2, dash='dot'), layer='above')
    fig.update_layout(
    title=f'{stock_industry} {stock_id} {stock_name} 收盤價走勢 (KD 金叉死叉策略)',
    xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
    yaxis=dict(title='收盤價', range=y_range),
    yaxis2=dict(
        title='KDJ',
        side='right',
        overlaying='y',
        range=y_range2,
        showgrid=False,
        tickvals=[0, 20, 50, 80, 100]
    ),
    width=900, height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
        )
    )
    
    # ===== 指數圖 =====
    fig2 = go.Figure()
    if '收盤指數' in df.columns:
        y_range2 = [df['收盤指數'].min(), df['收盤指數'].max()]
        fig2.add_trace(go.Scatter(x=df['Date'], y=df['收盤指數'],
                                  mode='lines', line=dict(color='red', width=1.5),
                                  name='收盤指數'))
        fig2.update_layout(
            title=f'{stock_id} 收盤指數',
            xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
            yaxis=dict(title='收盤指數', range=y_range2),
            legend=dict(title='', x=1.0, y=1.15, traceorder='normal', orientation='v'),
            width=900, height=250,
        )

    # ===== vectorbt 回測 =====
    df = df.set_index('Date')
    entries = (
        (df['K9'].shift(1) < df['D9'].shift(1)) &  # 前一天K9在D9下方
        (df['K9'] >= df['D9'])                     # 當天K9上穿D9
    )
    
    exits = (
        (df['K9'].shift(1) > df['D9'].shift(1)) &  # 前一天K9在D9上方
        (df['K9'] <= df['D9'])                     # 當天K9下穿D9
    )
    
    if entries.sum() > exits.sum():
        exits.iloc[-1] = True

    pf = vbt.Portfolio.from_signals(
        close=df['Close'],
        entries=entries,
        exits=exits,
        price=df['Open'],
        fees=0.001425,
        slippage=0.0005,
        init_cash=1_000_000,
        size=1000,
        direction='longonly',
    )

    trades = pf.trades.records.copy()
    fig3 = None
    fig4 = None
    if not trades.empty:
        trades.columns = [col.strip().lower() for col in trades.columns]
        trades['買入日期'] = df.index[trades['entry_idx']]
        trades['賣出日期'] = df.index[trades['exit_idx']]
        trades['買入金額'] = trades['entry_price'].round(3)
        trades['賣出金額'] = trades['exit_price'].round(3)
        trades['單次獲利(元)'] = trades['pnl'].round(0).astype(int)
        trades['收益(%)'] = (trades['return'] * 100).round(2)
        trades_show = trades[['買入日期', '買入金額', '賣出日期', '賣出金額', '單次獲利(元)', '收益(%)']].copy()
        trades_show['買入日期'] = trades_show['買入日期'].dt.strftime('%Y-%m-%d')
        trades_show['賣出日期'] = trades_show['賣出日期'].dt.strftime('%Y-%m-%d')
        fig3 = go.Figure(data=[go.Table(
            header=dict(values=list(trades_show.columns), fill_color='paleturquoise', align='center'),
            cells=dict(values=[trades_show[col] for col in trades_show.columns], fill_color='lavender', align='center'))
        ])
        fig3.update_layout(
            title=f"vectorbt KD 金叉/死叉 策略交易明細：{stock_id}",
            width=900, height=350
        )
        equity_curve = pf.value()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode='lines',
            line=dict(color='royalblue', width=1.5),
            name='資產走勢'
        ))
        fig4.update_layout(
            title=f'vectorbt KDJ 金叉/死叉 策略資產走勢：{stock_id}',
            xaxis_title='日期',
            yaxis_title='資產(元)',
            width=900,
            height=250
        )

    stats = pf.stats()

    return fig, fig2, fig3, fig4, stats


# fig, fig2, fig3, fig4, stats = plotly_tec_kd_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)

# fig.show()
# fig2.show()

# if fig3 is not None and fig4 is not None:
#     fig3.show()
#     fig4.show()
#     display(stats)
# else:
#     print("⚠️ 沒有任何成交紀錄，不顯示 fig3/fig4")



#%%
# MACD 金叉/死叉 + J9 篩選
def plotly_tec_macd_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):
    
    # 0. cal
    # === 3. rsv    
    def calc_rsv(df, kd_period=9):
        df = df.copy()
        df = df.sort_values(['股票代號', 'Date'])
        # 用 transform，解決 groupby-apply 造成的 shape 問題
        df[f'Low_min_{kd_period}'] = df.groupby('股票代號')['Low'].transform(lambda x: x.rolling(kd_period, min_periods=kd_period).min())
        df[f'High_max_{kd_period}'] = df.groupby('股票代號')['High'].transform(lambda x: x.rolling(kd_period, min_periods=kd_period).max())
        df[f'RSV{kd_period}'] = (df['Close'] - df[f'Low_min_{kd_period}']) / (df[f'High_max_{kd_period}'] - df[f'Low_min_{kd_period}']) * 100
     
        # 保留前九筆NaN，其餘NaN直接丟棄
        def drop_inner_nan(group):
            # 前面kd_period-1個保留，之後有NaN就drop
            idx_to_keep = group.index[:kd_period-1]
            nan_mask = group[f'RSV{kd_period}'].isna()
            # drop除了前面NaN以外的NaN
            drop_idx = group.index[(nan_mask) & (~group.index.isin(idx_to_keep))]
            return group.drop(index=drop_idx)

        df = df.groupby('股票代號', group_keys=False).apply(drop_inner_nan)
        df = df.reset_index(drop=True)
        return df
    daily_df_merge_index_pepb_selected_date_rsv = calc_rsv(daily_df_merge_index_pepb_selected_date_with_ma, kd_period=9)
    
    # === 4. kd ===
    def calc_kd(df, kd_period=9):
        """
        根據已經有RSV的df，計算所有股票的K/D/J值
        - 若當天RSV為NaN，K/D/J皆為NaN
        """
        df = df.copy()
        def _kd_group(rsv):
            k_list = [50]
            d_list = [50]
            for i in range(1, len(rsv)):
                if pd.isna(rsv.iloc[i]):
                    k = np.nan
                    d = np.nan
                else:
                    # 前一日K/D是NaN時，用50遞推
                    prev_k = k_list[-1] if not pd.isna(k_list[-1]) else 50
                    prev_d = d_list[-1] if not pd.isna(d_list[-1]) else 50
                    k = prev_k * 2 / 3 + rsv.iloc[i] * 1 / 3
                    d = prev_d * 2 / 3 + k * 1 / 3
                k_list.append(k)
                d_list.append(d)
            return pd.DataFrame({'K': k_list, 'D': d_list}, index=rsv.index)

        # 跑groupby，得到一個DataFrame
        kd_df = df.groupby('股票代號')[f'RSV{kd_period}'].apply(_kd_group).reset_index(level=0, drop=True)
        df[f'K{kd_period}'] = kd_df['K'].values
        df[f'D{kd_period}'] = kd_df['D'].values
        df[f'J{kd_period}'] = 3 * df[f'K{kd_period}'] - 2 * df[f'D{kd_period}']

        # 四捨五入
        df[f'K{kd_period}'] = df[f'K{kd_period}'].round(2)
        df[f'D{kd_period}'] = df[f'D{kd_period}'].round(2)
        df[f'J{kd_period}'] = df[f'J{kd_period}'].round(2)
        return df
    daily_df_merge_index_pepb_selected_date_rsv_kd = calc_kd(daily_df_merge_index_pepb_selected_date_rsv)
        
    # === 5. MACD ===
    def calc_macd(df, fast=12, slow=26, signal=9):
        df = df.copy()
        # 確保是時間排序 + 個股分組
        df = df.sort_values(['股票代號', 'Date'])
        
        # EMA 計算方式（用 ewm）
        def _macd_group(g):
            # 計算12/26 EMA
            ema_fast = g['Close'].ewm(span=fast, adjust=False).mean()
            ema_slow = g['Close'].ewm(span=slow, adjust=False).mean()
            dif = ema_fast - ema_slow
            macd = dif.ewm(span=signal, adjust=False).mean()
            osc = dif - macd
            return pd.DataFrame({
                'DIF': dif,
                'MACD': macd,
                'OSC': osc
            }, index=g.index)
        
        macd_df = df.groupby('股票代號').apply(_macd_group).reset_index(level=0, drop=True)
        df['DIF'] = macd_df['DIF'].round(4)
        df['MACD'] = macd_df['MACD'].round(4)
        df['OSC'] = macd_df['OSC'].round(4)
        return df
    daily_df_merge_index_pepb_selected_date_rsv_kd_macd = calc_macd(daily_df_merge_index_pepb_selected_date_rsv_kd)
    
    # 
    df = daily_df_merge_index_pepb_selected_date_rsv_kd_macd.copy()    
    if '股票代號' in df.columns and stock_id is not None:
        df = df[df['股票代號'] == stock_id]
    df = df.sort_values('Date')
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
    for c in ['Open', 'Close', 'DIF', 'MACD', 'OSC', 'High', 'Low', '收盤指數', 'J9']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['Date', 'Open', 'Close', 'DIF', 'MACD', 'OSC', 'High', 'Low', 'J9'])
    if df.empty:
        return go.Figure(), go.Figure(), None, None, go.Figure()

    # ====== 畫主圖（金叉/死叉）======
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'],
                             mode='lines', line=dict(color='red', width=1.2), name='收盤價'))
    
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['DIF'],
            mode='lines', line=dict(color='blue', width=1.2), name='DIF',
            yaxis='y2'
        ))
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['MACD'],
            mode='lines', line=dict(color='green', width=1.2), name='MACD',
            yaxis='y2'
        ))
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['J9'],
            mode='lines', line=dict(color='pink', width=1.2), name='J9',
            yaxis='y2'
        ))
    
    y_range = [df['Close'].min(), df['Close'].max()]
    macd_min = min(df['DIF'].min(), df['MACD'].min(), df['J9'].min())
    macd_max = max(df['DIF'].max(), df['MACD'].max(), df['J9'].max())
    y_range2 = [macd_min-5, macd_max+5]

    # MACD金叉，且J9<80才進場
    buy_signal = (df['DIF'].shift(1) < df['MACD'].shift(1)) & (df['DIF'] >= df['MACD'])
    # 死叉（DIF下穿MACD），可選擇要不要J9條件，通常不用
    sell_signal = (df['DIF'].shift(1) > df['MACD'].shift(1)) & (df['DIF'] <= df['MACD'])

    for date in df.loc[buy_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=y_range[0], y1=y_range[1],
                      line=dict(color='orange', width=2, dash='dot'), layer='above')
    for date in df.loc[sell_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=y_range[0], y1=y_range[1],
                      line=dict(color='gray', width=2, dash='dot'), layer='above')
    fig.update_layout(
    title=f'{stock_industry} {stock_id} {stock_name} 收盤價走勢 (MACD金叉死叉)',
    xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
    yaxis=dict(title='收盤價', range=y_range),
    yaxis2=dict(
        title='DIF / MACD / J9',
        side='right',
        overlaying='y',
        range=y_range2,
        showgrid=False
    ),
    width=900, height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
        )
    )
    
    # ====== 指數圖 ======
    fig2 = go.Figure()
    if '收盤指數' in df.columns:
        y_range2 = [df['收盤指數'].min(), df['收盤指數'].max()]
        fig2.add_trace(go.Scatter(x=df['Date'], y=df['收盤指數'],
                                  mode='lines', line=dict(color='red', width=1.5),
                                  name='收盤指數'))
        fig2.update_layout(
            title=f'{stock_id} 收盤指數',
            xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
            yaxis=dict(title='收盤指數', range=y_range2),
            legend=dict(title='', x=1.0, y=1.15, traceorder='normal', orientation='v'),
            width=900, height=250,
        )

    # ====== vectorbt 回測 ======
    df = df.set_index('Date')
    entries = (df['DIF'].shift(1) < df['MACD'].shift(1)) & (df['DIF'] >= df['MACD'])
    exits   = (df['DIF'].shift(1) > df['MACD'].shift(1)) & (df['DIF'] <= df['MACD'])
    if entries.sum() > exits.sum():
        exits.iloc[-1] = True

    pf = vbt.Portfolio.from_signals(
        close=df['Close'],
        entries=entries,
        exits=exits,
        price=df['Open'],
        fees=0.001425,
        slippage=0.0005,
        init_cash=1_000_000,
        size=1000,
        direction='longonly',
    )

    trades = pf.trades.records.copy()
    fig3 = None
    fig4 = None
    if not trades.empty:
        trades.columns = [col.strip().lower() for col in trades.columns]
        trades['買入日期'] = df.index[trades['entry_idx']]
        trades['賣出日期'] = df.index[trades['exit_idx']]
        trades['買入金額'] = trades['entry_price'].round(3)
        trades['賣出金額'] = trades['exit_price'].round(3)
        trades['單次獲利(元)'] = trades['pnl'].round(0).astype(int)
        trades['收益(%)'] = (trades['return'] * 100).round(2)
        trades_show = trades[['買入日期', '買入金額', '賣出日期', '賣出金額', '單次獲利(元)', '收益(%)']].copy()
        trades_show['買入日期'] = trades_show['買入日期'].dt.strftime('%Y-%m-%d')
        trades_show['賣出日期'] = trades_show['賣出日期'].dt.strftime('%Y-%m-%d')
        fig3 = go.Figure(data=[go.Table(
            header=dict(values=list(trades_show.columns), fill_color='paleturquoise', align='center'),
            cells=dict(values=[trades_show[col] for col in trades_show.columns], fill_color='lavender', align='center'))
        ])
        fig3.update_layout(
            title=f"vectorbt MACD 金叉/死叉 策略交易明細：{stock_id}",
            width=900, height=350
        )
        equity_curve = pf.value()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode='lines',
            line=dict(color='royalblue', width=1.5),
            name='資產走勢'
        ))
        fig4.update_layout(
            title=f'vectorbt MACD 金叉/死叉 策略資產走勢：{stock_id}',
            xaxis_title='日期',
            yaxis_title='資產(元)',
            width=900,
            height=250
        )

    stats = pf.stats()

    return fig, fig2, fig3, fig4, stats


# fig, fig2, fig3, fig4, stats = plotly_tec_macd_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)

# fig.show()
# fig2.show()

# if fig3 is not None and fig4 is not None:
#     fig3.show()
#     fig4.show()
#     display(stats)
# else:
#     print("⚠️ 沒有任何成交紀錄，不顯示 fig3/fig4")


#%%
# AO AC + vectorbt回測

def plotly_tec_ao_ac_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):
    
    # ===== 1. 計算 AO/AC 指標 =====
    def calc_ao_ac(df):
        df = df.copy()
        df = df.sort_values(['股票代號', 'Date'])
        df['Median_Price'] = (df['High'] + df['Low']) / 2
        df['AO_5'] = df.groupby('股票代號')['Median_Price'].transform(lambda x: x.rolling(5, min_periods=5).mean())
        df['AO_34'] = df.groupby('股票代號')['Median_Price'].transform(lambda x: x.rolling(34, min_periods=34).mean())
        df['AO'] = df['AO_5'] - df['AO_34']
        df['AO_MA5'] = df.groupby('股票代號')['AO'].transform(lambda x: x.rolling(5, min_periods=5).mean())
        df['AC'] = df['AO'] - df['AO_MA5']
        return df

    df = daily_df_merge_index_pepb_selected_date_with_ma.copy()
    if '股票代號' in df.columns and stock_id is not None:
        df = df[df['股票代號'] == stock_id].copy()
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
    for c in ['Open','High','Low','Close','收盤指數']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['Date','Open','High','Low','Close']).sort_values('Date').reset_index(drop=True)
    if df.empty:
        return go.Figure(), go.Figure(), None, None, go.Figure()

    # 計算 AO/AC
    df = calc_ao_ac(df)
    df = df.dropna(subset=['AO', 'AC'])

    # ===== 2. 畫主圖（收盤價+AO/AC訊號） =====
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', line=dict(color='red', width=1.2), name='收盤價'))
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['AO'],
            mode='lines', line=dict(color='blue', width=1.2), name='AO',
            yaxis='y2'
        ))
    fig.add_trace(go.Scatter(
            x=df['Date'], y=df['AC'],
            mode='lines', line=dict(color='green', width=1.2), name='AC',
            yaxis='y2'
        ))
    y_range = [df['Close'].min(), df['Close'].max()]
    ao_min = min(df['AO'].min(), df['AC'].min())
    ac_max = max(df['AO'].max(), df['AC'].max())
    y_range2 = [ao_min-5, ac_max+5]
    
    # AO/AC進出場訊號（可依自己習慣修改）
    buy_signal = (df['AO'] > 0) & (df['AC'] > 0) & (df['AC'].shift(1) < 0)
    sell_signal = (df['AO'] < 0) & (df['AC'] < 0) & (df['AC'].shift(1) > 0)
    for date in df.loc[buy_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=y_range[0], y1=y_range[1],
                      line=dict(color='orange', width=2, dash='dot'), layer='above')
    for date in df.loc[sell_signal, 'Date']:
        fig.add_shape(type="line", x0=date, x1=date,
                      y0=y_range[0], y1=y_range[1],
                      line=dict(color='gray', width=2, dash='dot'), layer='above')
    fig.update_layout(
    title=f'{stock_industry} {stock_id} {stock_name} 收盤價走勢 (AO/AC策略)',
    xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
    yaxis=dict(title='收盤價', range=y_range),
    yaxis2=dict(
        title='AO / AC',
        side='right',
        overlaying='y',
        range=y_range2,
        showgrid=False,
    ),
    width=900, height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
        )
    )

    # ===== 3. 指數圖 =====
    fig2 = go.Figure()
    if '收盤指數' in df.columns:
        y_range2 = [df['收盤指數'].min(), df['收盤指數'].max()]
        fig2.add_trace(go.Scatter(x=df['Date'], y=df['收盤指數'],
                                  mode='lines', line=dict(color='red', width=1.5), name='收盤指數'))
        fig2.update_layout(
            title=f'{stock_id} 收盤指數',
            xaxis=dict(title='日期', type='date', tickformat='%Y%m%d', tickangle=60),
            yaxis=dict(title='收盤指數', range=y_range2),
            legend=dict(title='', x=1.0, y=1.15, traceorder='normal', orientation='v'),
            width=900, height=250,
        )

    # ===== 4. vectorbt 回測 =====
    df = df.set_index('Date')
    entries = (df['AO'] > 0) & (df['AC'] > 0) & (df['AC'].shift(1) < 0)
    exits = (df['AO'] < 0) & (df['AC'] < 0) & (df['AC'].shift(1) > 0)
    if entries.sum() > exits.sum():
        exits.iloc[-1] = True

    pf = vbt.Portfolio.from_signals(
        close=df['Close'],
        entries=entries,
        exits=exits,
        price=df['Open'],
        fees=0.001425,
        slippage=0.0005,
        init_cash=1_000_000,
        size=1000,
        direction='longonly'
    )

    trades = pf.trades.records.copy()
    fig3 = None
    fig4 = None
    if not trades.empty:
        trades.columns = [col.strip().lower() for col in trades.columns]
        trades['買入日期'] = df.index[trades['entry_idx']]
        trades['賣出日期'] = df.index[trades['exit_idx']]
        trades['買入金額'] = trades['entry_price'].round(3)
        trades['賣出金額'] = trades['exit_price'].round(3)
        trades['單次獲利(元)'] = trades['pnl'].round(0).astype(int)
        trades['收益(%)'] = (trades['return'] * 100).round(2)
        trades_show = trades[['買入日期', '買入金額', '賣出日期', '賣出金額', '單次獲利(元)', '收益(%)']].copy()
        trades_show['買入日期'] = trades_show['買入日期'].dt.strftime('%Y-%m-%d')
        trades_show['賣出日期'] = trades_show['賣出日期'].dt.strftime('%Y-%m-%d')
        fig3 = go.Figure(data=[go.Table(
            header=dict(values=list(trades_show.columns), fill_color='paleturquoise', align='center'),
            cells=dict(values=[trades_show[col] for col in trades_show.columns], fill_color='lavender', align='center'))
        ])
        fig3.update_layout(
            title=f"vectorbt AO/AC 策略交易明細：{stock_id}",
            width=900, height=350
        )
        equity_curve = pf.value()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve.values,
            mode='lines',
            line=dict(color='royalblue', width=1.5),
            name='資產走勢'
        ))
        fig4.update_layout(
            title=f'vectorbt AO/AC 策略資產走勢：{stock_id}',
            xaxis_title='日期',
            yaxis_title='資產(元)',
            width=900,
            height=250
        )

    stats = pf.stats()

    return fig, fig2, fig3, fig4, stats

# fig, fig2, fig3, fig4, stats = plotly_tec_ao_ac_vectorbt(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)

# fig.show()
# fig2.show()

# if fig3 is not None and fig4 is not None:
#     fig3.show()
#     fig4.show()
#     display(stats)
# else:
#     print("⚠️ 沒有任何成交紀錄，不顯示 fig3/fig4")



#%%
# bollinger
# 上軸突破 + 均線多頭排列 + 量增 → 很強的多頭啟動
# 下軸跌破 + 均線空頭排列 + 量增 → 強空訊號
# 上下軸突破但沒量、型態不佳，就要小心假突破

def plotly_bollinger_ma(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):
    # === 7. bollinger 布林通道 ===
    def calc_bollinger(df, window_list=[20], K=2):
        df = df.copy()
        df = df.sort_values(['股票代號', 'Date'])
        for N in window_list:
            # Middle Band（這裡順便叫 MA20，一起存）
            df[f'MB{N}'] = df.groupby('股票代號')['Close'].transform(lambda x: x.rolling(N).mean())
            if N == 20:
                df['MA20'] = df[f'MB{N}']  # 直接算 MA20，畫線才不會漏
            # 標準差
            df[f'STD{N}'] = df.groupby('股票代號')['Close'].transform(lambda x: x.rolling(N).std())
            # Upper Band
            df[f'UB{N}'] = df[f'MB{N}'] + K * df[f'STD{N}']
            # Lower Band
            df[f'LB{N}'] = df[f'MB{N}'] - K * df[f'STD{N}']
        return df

    daily_df_merge_index_pepb_selected_date_bollinger = calc_bollinger(daily_df_merge_index_pepb_selected_date_with_ma)


    df = daily_df_merge_index_pepb_selected_date_bollinger.copy()
    # 選股票
    if '股票代號' in df.columns and stock_id is not None:
        df = df[df['股票代號'] == stock_id]
    df = df.sort_values('Date').copy()
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
    for c in ['Close', 'High', 'Low', 'Open', 'MB20', 'UB20', 'LB20', 'MA20', '個股成交量', '收盤指數']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # long_signal: 跌破下軸 & 均線多頭排列 & 量增
    df['多頭排列'] = (df['MA20'] > df['MA30']) & (df['MA30'] > df['MA60'])
    # 可以根據實際需求設量增條件
    df['量均'] = df['個股成交量'].rolling(20, min_periods=1).mean()
    df['量增'] = df['個股成交量'] > df['量均']
    df['long_signal'] = (df['Close'] < df['LB20']) & df['多頭排列'] & df['量增']

    # short_signal: 跌破上軸 & 均線空頭排列 & 量增
    df['空頭排列'] = (df['MA20'] < df['MA30']) & (df['MA30'] < df['MA60'])
    df['short_signal'] = (df['Close'] > df['UB20']) & df['空頭排列'] & df['量增']

    # 主圖
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='收盤價', line=dict(color='red', width=1)))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['UB20'], name='布林上軸', line=dict(color='black', width=1)))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MB20'], name='布林中軸', line=dict(color='blue', width=1, dash='dot')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['LB20'], name='布林下軸', line=dict(color='green', width=1)))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], name='MA20', line=dict(color='orange', width=1, dash='dash')))

    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 布林通道+均線突破策略",
        xaxis_title="Date", yaxis_title="股價",
        width=900, height=400,
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


# fig = plotly_bollinger_ma(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)
# fig.show()




#%% ATR
# 判斷近期「波動大還是小」
# ATR高 → 價格大幅波動，市場熱絡
# ATR低 → 盤整、行情沉悶
# 動態調整停損（ATR倍數停損）
# 例如：設停損在「進場價 - 2倍ATR」外
# 用波動率來設止損，比用固定價差更貼近行情
import plotly.graph_objects as go

def plotly_tec_atr(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):
    # 0. cal
    # === 6. ATR 波動率 ===
    def calc_atr(df, window_list=[5, 14]):
        df = df.copy()
        df = df.sort_values(['股票代號', 'Date'])
        # 前一天收盤
        df['前收'] = df.groupby('股票代號')['Close'].shift(1)
        # True Range三種方式
        df['TR1'] = df['High'] - df['Low']
        df['TR2'] = (df['High'] - df['前收']).abs()
        df['TR3'] = (df['Low'] - df['前收']).abs()
        df['TR'] = df[['TR1','TR2','TR3']].max(axis=1)
        # 多個ATR
        for win in window_list:
            df[f'ATR{win}'] = df.groupby('股票代號')['TR'].transform(lambda x: x.rolling(win).mean())
        return df
    daily_df_merge_index_pepb_selected_date_atr = calc_atr(daily_df_merge_index_pepb_selected_date_with_ma)


    df = daily_df_merge_index_pepb_selected_date_atr.copy()
    # 篩選單一股票（可選）
    if '股票代號' in df.columns and stock_id is not None:
        df = df[df['股票代號'] == stock_id].copy()
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
    df = df.sort_values('Date')
    # 直接用現有 ATR 欄位
    for c in ['Close','ATR5','ATR14']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    if stock_id is None and '股票代號' in df.columns:
        try:
            stock_id = df['股票代號'].iloc[0]
        except: stock_id = ''
    if stock_name is None:
        stock_name = ''
    
    # 主圖 ATR + Close（雙y軸）
    fig = go.Figure()
    # ATR14 (左側)
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['ATR14'],
        mode='lines', name='ATR14',
        line=dict(color='royalblue', width=2), yaxis='y1'
    ))
    # ATR5 (左側)
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['ATR5'],
        mode='lines', name='ATR5',
        line=dict(color='orange', width=2, dash='dot'), yaxis='y1'
    ))
    # 收盤價 (右側)
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Close'],
        mode='lines', name='收盤價',
        line=dict(color='red', width=1), yaxis='y2'
    ))
    fig.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} ATR5 / ATR14 波動率線＋收盤價',
        xaxis_title='Date',
        yaxis=dict(title='ATR值', side='left'),
        yaxis2=dict(title='收盤價', overlaying='y', side='right'),  # 右側
        width=900, height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
        )
    )

    # ATR 百分比（波動率%）圖
    if 'ATR5' in df.columns and 'ATR14' in df.columns and 'Close' in df.columns:
        df['ATR5_pct'] = df['ATR5'] / df['Close']
        df['ATR14_pct'] = df['ATR14'] / df['Close']
    else:
        df['ATR5_pct'] = df['ATR14_pct'] = None

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df['Date'], y=df['ATR5_pct'],
        mode='lines', name='ATR5波動率%',
        line=dict(color='orange', width=2, dash='dot')
    ))
    fig2.add_trace(go.Scatter(
        x=df['Date'], y=df['ATR14_pct'],
        mode='lines', name='ATR14波動率%',
        line=dict(color='royalblue', width=2)
    ))
    # 警戒線
    fig2.add_shape(type="line", x0=df['Date'].min(), x1=df['Date'].max(),
                   y0=0.04, y1=0.04, line=dict(color='red', dash='dot'))
    fig2.add_shape(type="line", x0=df['Date'].min(), x1=df['Date'].max(),
                   y0=0.08, y1=0.08, line=dict(color='green', dash='dot'))

    fig2.update_layout(
        title=f'{stock_industry} {stock_id} {stock_name} ATR5 / ATR14 (%) 波動率線',
        xaxis_title='Date',
        yaxis_title='ATR波動率(%)',
        yaxis_tickformat='.2%',
        width=900, height=400,
        legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.25,         # 建議從 -0.10 ~ -0.18 之間測試，找到最適合你畫面的值
        xanchor='center',
        x=0.5,
        font=dict(size=13)   # 如覺得字太大可再調小
        )
    )

    return fig, fig2


# fig, fig2 = plotly_tec_atr(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)
# fig.show()
# fig2.show()


#%% 
# 乖離率
 
def bia(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id):
    
    df = daily_df_merge_index_pepb_selected_date_with_ma.copy()
    # 0. cal
    # === 8. 乖離率 ===
    df['Bias_MA14'] = (df['Close'] - df['MA14']) / df['MA14'] * 100
    df['Bias_MA20'] = (df['Close'] - df['MA20']) / df['MA20'] * 100
    df['Bias_MA30'] = (df['Close'] - df['MA30']) / df['MA30'] * 100
    df['Bias_MA60'] = (df['Close'] - df['MA60']) / df['MA60'] * 100
    
    if '股票代號' in df.columns and stock_id is not None:
        df = df[df['股票代號'] == stock_id]
    df = df.sort_values('Date').copy()
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
    for c in ['Close', 'MA14', 'MA20', 'MA30', 'MA60']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    fig = go.Figure()

    # 左軸：乖離率
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Bias_MA20'],
        mode='lines', name='MA20乖離率',
        line=dict(color='blue', width=1.2),
        yaxis='y1'
    ))
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Bias_MA60'],
        mode='lines', name='MA60乖離率',
        line=dict(color='orange', width=1.2),
        yaxis='y1'
    ))
    # 右軸：收盤價
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Close'],
        mode='lines', name='收盤價',
        line=dict(color='red', width=1),
        yaxis='y2'
    ))

    # 0軸
    fig.add_shape(type="line", x0=df['Date'].min(), x1=df['Date'].max(), y0=0, y1=0,
                line=dict(color='gray', dash='dot'), yref='y1')
    # ±5% 警戒線
    fig.add_shape(type="line", x0=df['Date'].min(), x1=df['Date'].max(), y0=5, y1=5,
                line=dict(color='red', dash='dot'), yref='y1')
    fig.add_shape(type="line", x0=df['Date'].min(), x1=df['Date'].max(), y0=-5, y1=-5,
                line=dict(color='green', dash='dot'), yref='y1')

    fig.update_layout(
        title=f"{stock_industry} {stock_id} {stock_name} 乖離率(BIAS)走勢",
        xaxis_title='日期',
        yaxis=dict(title='乖離率 (%)', side='left'),
        yaxis2=dict(title='收盤價', overlaying='y', side='right'),
        width=900, height=400,
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


# fig = bia(daily_df_merge_index_pepb_selected_date_with_ma, stock_industry, stock_name, stock_id)
# fig.show()