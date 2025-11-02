# us_stock_ai_insight.py

import streamlit as st
import os
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from openai import OpenAI
from plotly.subplots import make_subplots


# ==================== FMP quarterly ====================
#%% 
@st.cache_data(ttl=3600)
def get_balance_ratios(symbol, api_key):
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={symbol}&apikey={api_key}"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data)
    
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    
    for c in ["totalAssets","totalLiabilities","totalStockholdersEquity",
              "totalCurrentAssets","totalCurrentLiabilities","netDebt",
              "cashAndShortTermInvestments","netReceivables",
              "totalDebt","shortTermDebt","longTermDebt", "retainedEarnings"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 比率
    # 流動比 / 速動比 / 現金比
    # 資產 / 負債 / 權益 
    # 負債比 / 權益比 / 淨負債比
    df["current_ratio"] = df["totalCurrentAssets"] / df["totalCurrentLiabilities"]
    df["quick_ratio"]   = (df["cashAndShortTermInvestments"] + df["netReceivables"]) / df["totalCurrentLiabilities"]
    df["debt_ratio"]    = df["totalLiabilities"] / df["totalAssets"]
    df["equity_ratio"]  = df["totalStockholdersEquity"] / df["totalAssets"]
    df["debt_to_equity"] = df["totalLiabilities"] / df["totalStockholdersEquity"]
    df["net_debt_ratio"] = df["netDebt"] / df["totalAssets"]
    df["cash_ratio"]   = df["cashAndShortTermInvestments"] / df["totalCurrentLiabilities"]
    df["longTermDebt"] = df["longTermDebt"]

    #
    cols_to_keep = [
        "date","symbol",
        "totalAssets","totalLiabilities","totalStockholdersEquity",
        "totalCurrentAssets","totalCurrentLiabilities","netDebt",
        "cashAndShortTermInvestments","netReceivables",
        "totalDebt","shortTermDebt","longTermDebt_inferred",
        "current_ratio","quick_ratio","debt_ratio","equity_ratio",
        "debt_to_equity","net_debt_ratio","cash_ratio", "longTermDebt","retainedEarnings"
    ]
    df = df[[c for c in cols_to_keep if c in df.columns]].round(3)
    return df



#%%
# ==================== FMP get_income_ratios ====================
@st.cache_data(ttl=3600)
def get_income_ratios(symbol, api_key):
    """
    從 FMP income-statement 取多期資料，計算常見損益表比率與成長率。
    回傳按日期遞增排序的 DataFrame。
    """
    import numpy as np
    import pandas as pd
    import requests

    url = f"https://financialmodelingprep.com/stable/income-statement?symbol={symbol}&apikey={api_key}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data)
    if df.empty:
        return df
    
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    # 確保欄位存在，缺的補 NaN 以避免 KeyError
    need = [
        "revenue","costOfRevenue","grossProfit",
        "sellingGeneralAndAdministrativeExpenses","researchAndDevelopmentExpenses",
        "operatingExpenses","ebit","ebitda","operatingIncome",
        "incomeBeforeTax","incomeTaxExpense","interestExpense",
        "netIncome","eps","epsDiluted","weightedAverageShsOutDil"
    ]
    for c in need:
        if c not in df.columns:
            df[c] = np.nan

    # ===== 比率（Margins / Expense mix）=====
    # 毛利率 / 營業利益率 / EBIT率 / EBITDA率 / 淨利率
    df["gross_margin"]     = df["grossProfit"]      / df["revenue"]
    df["operating_margin"] = df["operatingIncome"]  / df["revenue"]
    df["ebit_margin"]      = df["ebit"]             / df["revenue"]
    df["ebitda_margin"]    = df["ebitda"]           / df["revenue"]
    df["net_margin"]       = df["netIncome"]        / df["revenue"]

    # 費用率（研發 / 銷管）
    df["rnd_ratio"]  = df["researchAndDevelopmentExpenses"]          / df["revenue"]
    df["sga_ratio"]  = df["sellingGeneralAndAdministrativeExpenses"] / df["revenue"]

    # 稅率 / 利息保障倍數（避免除 0）
    df["tax_rate"] = df["incomeTaxExpense"] / df["incomeBeforeTax"]
    df["interest_coverage"] = np.where(df["interestExpense"].abs() > 0,
                                       df["ebit"] / df["interestExpense"].abs(),
                                       np.nan)

    # ===== 成長率（YoY 與 QoQ）=====
    # 註：FMP此端點可能回傳年度(FY)或季度(Q). 直接用相鄰期 pct_change()，名稱上標示「_chg」。
    # 如果你要明確 YoY，請先依「period」分組後與落後4期比較（季表）或落後1期比較（年表）。
    for col in ["revenue","grossProfit","operatingIncome","ebit","ebitda","netIncome","epsDiluted"]:
        if col in df.columns:
            df[f"{col}_chg"] = df[col].pct_change()  # 相鄰期變動率（可能是QoQ或YoY，視來源頻率）

    # 每股指標（利於跨期比較）
    df["revenue_ps"]   = df["revenue"]   / df["weightedAverageShsOutDil"]
    df["netincome_ps"] = df["netIncome"] / df["weightedAverageShsOutDil"]

    # 留幾個有用欄位供前端/AI
    keep = [
        "date","symbol","period","fiscalYear",
        "revenue","grossProfit","operatingIncome","ebit","ebitda","netIncome",
        "eps","epsDiluted","weightedAverageShsOutDil",
        "gross_margin","operating_margin","ebit_margin","ebitda_margin","net_margin",
        "rnd_ratio","sga_ratio","tax_rate","interest_coverage",
        "revenue_ps","netincome_ps",
        "revenue_chg","grossProfit_chg","operatingIncome_chg","ebit_chg","ebitda_chg","netIncome_chg","epsDiluted_chg"
    ]
    df = df[[c for c in keep if c in df.columns]].copy()

    # 數值整理
    pct_cols = [
        "gross_margin","operating_margin","ebit_margin","ebitda_margin","net_margin",
        "rnd_ratio","sga_ratio","tax_rate",
        "revenue_chg","grossProfit_chg","operatingIncome_chg","ebit_chg","ebitda_chg","netIncome_chg","epsDiluted_chg"
    ]
    df[pct_cols] = df[pct_cols].astype(float)

    return df


#%%
# ==================== FMP get_cashflow_ratios ====================
@st.cache_data(ttl=3600)
def get_cashflow_ratios(symbol, api_key):
    """
    從 FMP cash-flow-statement 取多期資料，計算常見指標：
    - OCF/CFI/CFF/FCF、CapEx、期末現金
    - 現金轉換率：OCF / Net Income
    - CapEx 強度：(-CapEx) / OCF
    - 股東回饋：股利、買回庫藏，及其相對 OCF 的比率
    - 營運資金變動、SBC、折舊攤銷
    回傳按 date 遞增的 DataFrame。
    """


    url = f"https://financialmodelingprep.com/stable/cash-flow-statement?symbol={symbol}&apikey={api_key}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data)
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    # 安全欄位（缺就補 NaN）
    need = [
        "netIncome",
        "netCashProvidedByOperatingActivities","operatingCashFlow",
        "netCashProvidedByInvestingActivities",
        "netCashProvidedByFinancingActivities",
        "capitalExpenditure","investmentsInPropertyPlantAndEquipment",
        "freeCashFlow",
        "netDividendsPaid","commonDividendsPaid","preferredDividendsPaid",
        "netCommonStockIssuance","commonStockRepurchased",
        "netDebtIssuance",
        "changeInWorkingCapital","stockBasedCompensation","depreciationAndAmortization",
        "cashAtBeginningOfPeriod","cashAtEndOfPeriod"
    ]
    for c in need:
        if c not in df.columns:
            df[c] = np.nan

    # 主要現金流
    df["OCF"] = df["netCashProvidedByOperatingActivities"].fillna(df["operatingCashFlow"])
    df["CFI"] = df["netCashProvidedByInvestingActivities"]
    df["CFF"] = df["netCashProvidedByFinancingActivities"]

    # CapEx（有兩種欄位，通常為負值）
    df["CapEx"] = df["capitalExpenditure"].fillna(df["investmentsInPropertyPlantAndEquipment"])

    # FCF：優先用 API 的 freeCashFlow，否則用 OCF + CapEx（CapEx 通常為負）
    df["FCF"] = df["freeCashFlow"]
    df.loc[df["FCF"].isna(), "FCF"] = df["OCF"] + df["CapEx"]

    # 股利與買回庫藏（轉為正號代表現金流出額度）
    div_raw = df["netDividendsPaid"].fillna(df["commonDividendsPaid"].fillna(0.0))
    buyback_raw = df["commonStockRepurchased"].fillna(df["netCommonStockIssuance"].fillna(0.0))
    df["Dividends"] = (-div_raw).clip(lower=0)          # 支出轉正值
    df["Buybacks"]  = (-buyback_raw).clip(lower=0)      # 支出轉正值
    df["Shareholder_Returns"] = df["Dividends"] + df["Buybacks"]

    # 比率
    df["cash_conversion"] = np.where(df["netIncome"] != 0, df["OCF"] / df["netIncome"], np.nan)
    df["capex_to_ocf"]    = np.where(df["OCF"] != 0, (-df["CapEx"]) / df["OCF"], np.nan)
    df["payout_to_ocf"]   = np.where(df["OCF"] != 0, df["Shareholder_Returns"] / df["OCF"], np.nan)

    # 取用欄位
    keep = [
        "date","symbol","period","fiscalYear",
        "netIncome","OCF","CFI","CFF","CapEx","FCF",
        "Dividends","Buybacks","Shareholder_Returns",
        "netDebtIssuance",
        "changeInWorkingCapital","stockBasedCompensation","depreciationAndAmortization",
        "cashAtBeginningOfPeriod","cashAtEndOfPeriod",
        "cash_conversion","capex_to_ocf","payout_to_ocf"
    ]
    df = df[[c for c in keep if c in df.columns]].copy()

    return df


#%%
# ==== FMP 3 financial ===
def compute_core_cross_metrics_from_frames(
    inc: pd.DataFrame, 
    bal: pd.DataFrame, 
    cfs: pd.DataFrame
) -> pd.DataFrame:

    if any(df is None or df.empty for df in [inc, bal, cfs]):
        return pd.DataFrame()

    inc, bal, cfs = inc.copy(), bal.copy(), cfs.copy()

    for df in (inc, bal, cfs):
        df["date"] = pd.to_datetime(df["date"])
        df["year_month"] = df["date"].dt.to_period("M").astype(str)

    # 判斷季報/年報
    def _infer_lag(df_income):
        if "period" in df_income.columns and df_income["period"].notna().any():
            if df_income["period"].astype(str).str.upper().str.startswith("Q").any():
                return 4
        return 1
    LAG = _infer_lag(inc)

    # 合併三表，用 year_month
    df = (
        inc.merge(bal, on=["symbol", "year_month"], how="inner", suffixes=("_is", "_bs"))
           .merge(cfs, on=["symbol", "year_month"], how="inner", suffixes=("", "_cf"))
           .sort_values("date_bs")   # 你也可以用 date_is or date_cf
           .reset_index(drop=True)
    )
    if df.empty:
        return df

    if "netIncomeFromContinuingOperations" in df.columns and df["netIncomeFromContinuingOperations"].notna().any():
        df["netIncome_used"] = df["netIncomeFromContinuingOperations"].combine_first(df["netIncome"])
    else:
        df["netIncome_used"] = df["netIncome"]
        
    # 日期統一（可以選用 balance sheet 日期）
    df["date"] = df["date_bs"]

    def _safe_div(num, den):
        den = den.replace(0, np.nan) if isinstance(den, pd.Series) else (np.nan if den == 0 else den)
        return num / den

    # # TTM/平均值
    # df["revenue_TTM"]   = df["revenue"].rolling(LAG, min_periods=LAG).sum()    
    # for col in ["OCF", "FCF", "CapEx", "Dividends", "Buybacks"]:
    #     if col in df.columns:
    #         df[f"{col}_TTM"] = df[col].rolling(LAG, min_periods=LAG).sum()
    
    # 近四季算法
    # df["avg_assets"] = (df["totalAssets"] + df["totalAssets"].shift(1)) / 2
    # df["avg_equity"] = (df["totalStockholdersEquity"] + df["totalStockholdersEquity"].shift(1)) / 2
    # df["ROE"] = df["netIncome"] / df["avg_equity"] * 100
    # df["ROA"] = df["netIncome"] / df["avg_assets"] * 100

    df = df.sort_values("date")   
    df["ROE"] = df["netIncome_used"] / df["totalStockholdersEquity"] * 100
    df["ROA"] = df["netIncome_used"] / df["totalAssets"] * 100
    
    
    df["asset_turnover"] = _safe_div(df["revenue"], df["totalAssets"])
    df["cash_conversion"] = _safe_div(df["OCF"], df["netIncome_used"])
    df["fcf_margin"] = _safe_div(df["FCF"], df["revenue"])
    df["capex_to_ocf"] = _safe_div(-df["CapEx"], df["OCF"])
    df["payout_to_ocf"] = _safe_div(df["Dividends"] + df["Buybacks"], df["OCF"])

    def _yoy(s):
        return _safe_div(s, s.shift(LAG)) - 1
    df["ROA_yoy"] = _yoy(df["ROA"])
    df["ROE_yoy"] = _yoy(df["ROE"])
    df["asset_turnover_yoy"] = _yoy(df["asset_turnover"])

    keep = [
        "date", "symbol",
        "ROA", "ROE", "asset_turnover",
        "cash_conversion", "fcf_margin", "capex_to_ocf", "payout_to_ocf",
        "ROA_yoy", "ROE_yoy", "asset_turnover_yoy"
    ]
    keep = [c for c in keep if c in df.columns]
    out = df[keep].copy()

    return out


#%%
# ==================== others ====================
@st.cache_data(ttl=3600)
def get_enterprise_values(symbol, api_key):
    """獲取企業價值數據"""
    try:
        url = f"https://financialmodelingprep.com/stable/enterprise-values?symbol={symbol}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return pd.DataFrame(data)
        st.warning(f"⚠️ 無法獲取 {symbol} 的企業價值數據")
        return None
    except Exception as e:
        st.error(f"❌ 獲取企業價值數據時發生錯誤: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def get_company_profile(symbol, api_key):
    """獲取公司基本資料"""
    try:
        url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]
        st.warning(f"⚠️ 無法獲取 {symbol} 的公司資料")
        return None
    except Exception as e:
        st.error(f"❌ 獲取公司資料時發生錯誤: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def get_key_metrics(symbol, api_key):
    """獲取關鍵指標"""
    try:
        url = f"https://financialmodelingprep.com/stable/key-metrics?symbol={symbol}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return pd.DataFrame(data)
        st.warning(f"⚠️ 無法獲取 {symbol} 的關鍵指標")
        return None
    except Exception as e:
        st.error(f"❌ 獲取關鍵指標時發生錯誤: {str(e)}")
        return None



#%%
# ==================== FMP daily ====================
def get_stock_data(symbol, api_key):
    try:
        url = f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={symbol}&apikey={api_key}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            st.error(f"❌ FMP API 請求失敗 ({response.status_code})，請確認金鑰或稍後再試。")
            return None

        data = response.json()
        rows = None
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = data.get("historical") or data.get("data")

        if not rows:
            st.error(f"⚠️ 找不到 {symbol} 的股價資料。")
            return None

        df = pd.DataFrame(rows)
        if df.empty:
            return None

        rename_map = {'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume', 't': 'date'}
        df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

        if "volume" not in df.columns:
            df["volume"] = 0

        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df

    except Exception as e:
        st.error(f"❌ 數據獲取失敗: {str(e)}")
        return None
    

#%%
# ==================== 四階段財報分析計算 ====================
def safe_divide(numerator, denominator, default=0):
    try:
        numerator = float(numerator) if not pd.isna(numerator) else 0
        denominator = float(denominator) if not pd.isna(denominator) else 1
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


def calculate_piotroski_fscore(df_income: pd.DataFrame,
                               df_balance: pd.DataFrame,
                               df_cash: pd.DataFrame):

    # --- 基本檢查 ---
    if any(x is None or x.empty for x in (df_income, df_balance, df_cash)):
        return None
    if len(df_income) < 2 or len(df_balance) < 2 or len(df_cash) < 2:
        return None

    # --- 時序：取「最近期」與「前一期」 ---
    df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
    df_balance = df_balance.sort_values('date', ascending=False).reset_index(drop=True)
    df_cash = df_cash.sort_values('date', ascending=False).reset_index(drop=True)

    ci, pi = df_income.iloc[0], df_income.iloc[1]
    cb, pb = df_balance.iloc[0], df_balance.iloc[1]
    cc, pc = df_cash.iloc[0], df_cash.iloc[1]

    # --- 直接用 longTermDebt 欄位 ---
    ltd_now = cb.get('longTermDebt', np.nan)
    ltd_prev = pb.get('longTermDebt', np.nan)

    # --- 指標計算 ---
    roa_now = safe_divide(ci.get('netIncome', 0), cb.get('totalAssets', 1))
    roa_prev = safe_divide(pi.get('netIncome', 0), pb.get('totalAssets', 1))
    roa_precentage = roa_now - roa_prev
    
    ocf_now = cc.get('OCF', 0)
    ocf_prev = pc.get('OCF', 0)
    net_income_now = ci.get('netIncome', 0)
    net_income_prev = pi.get('netIncome', 0)

    ca_now = cb.get('totalCurrentAssets', 0)
    ca_prev = pb.get('totalCurrentAssets', 0)
    cl_now = cb.get('totalCurrentLiabilities', 1)
    cl_prev = pb.get('totalCurrentLiabilities', 1)
    cr_now = safe_divide(ca_now, cl_now)
    cr_prev = safe_divide(ca_prev, cl_prev)

    ltd_now_ratio = safe_divide(ltd_now, cb.get('totalAssets', 1))
    ltd_prev_ratio = safe_divide(ltd_prev, pb.get('totalAssets', 1))

    # 股份（優先 Diluted）
    shares_now = ci.get('weightedAverageShsOutDil', ci.get('weightedAverageShsOut', 0))
    shares_prev = pi.get('weightedAverageShsOutDil', pi.get('weightedAverageShsOut', 0))

    # 營運效率
    gpm_now = safe_divide(ci.get('grossProfit', 0), ci.get('revenue', 1))
    gpm_prev = safe_divide(pi.get('grossProfit', 0), pi.get('revenue', 1))
    ato_now = safe_divide(ci.get('revenue', 0), cb.get('totalAssets', 1))
    ato_prev = safe_divide(pi.get('revenue', 0), pb.get('totalAssets', 1))

    # --- 組裝回傳（含打勾打叉與分數） ---
    score = dict(profitability=[], leverage=[], efficiency=[], total_score=0)

    # 1) 獲利能力（4項）
    score['profitability'] = [
        {
            'name': 'ROA正值',
            'score': int(roa_now > 0),
            'current': f"{roa_now:.4f}",
            'previous': f"{roa_prev:.4f}",
            'status': '✓' if roa_now > 0 else '✗'
        },
        {
            'name': '營運現金流正值',
            'score': int(ocf_now > 0),
            'current': f"${ocf_now:,.0f}",
            'previous': f"${ocf_prev:,.0f}",
            'status': '✓' if ocf_now > 0 else '✗'
        },
        {
            'name': 'ROA年增',
            'score': int(roa_now > roa_prev),
            'current': f"{roa_precentage:.4f}",
            'previous': f"-",
            'status': '✓' if roa_now > roa_prev else '✗'
        },
        {
            'name': '現金流品質（OCF - 淨利）',
            'score': int(ocf_now > net_income_now),
            'current': f"${ocf_now-net_income_now:,.0f}",
            'previous': f"${ocf_prev-net_income_prev:,.0f}",
            'status': '✓' if ocf_now > net_income_now else '✗'
        },
    ]

    # 2) 槓桿與流動性（3項）
    score['leverage'] = [
        {
            'name': '長期負債比率改善',
            'score': int(ltd_now_ratio < ltd_prev_ratio),
            'current': f"{(0.0 if np.isnan(ltd_now_ratio) else ltd_now_ratio):.4f}",
            'previous': f"{(0.0 if np.isnan(ltd_prev_ratio) else ltd_prev_ratio):.4f}",
            'status': '✓' if (not np.isnan(ltd_now_ratio) and not np.isnan(ltd_prev_ratio) and (ltd_now_ratio < ltd_prev_ratio)) else '✗'
        },
        {
            'name': '流動比率改善',
            'score': int(cr_now > cr_prev),
            'current': f"{cr_now:.2f}",
            'previous': f"{cr_prev:.2f}",
            'status': '✓' if cr_now > cr_prev else '✗'
        },
        {
            'name': '股份未稀釋',
            'score': int(shares_now <= shares_prev),
            'current': f"{shares_now:,.0f}",
            'previous': f"{shares_prev:,.0f}",
            'status': '✓' if shares_now <= shares_prev else '✗'
        },
    ]

    # 3) 營運效率（2項）
    score['efficiency'] = [
        {
            'name': '毛利率改善',
            'score': int(gpm_now > gpm_prev),
            'current': f"{gpm_now:.4f}",
            'previous': f"{gpm_prev:.4f}",
            'status': '✓' if gpm_now > gpm_prev else '✗'
        },
        {
            'name': '資產周轉率改善',
            'score': int(ato_now > ato_prev),
            'current': f"{ato_now:.4f}",
            'previous': f"{ato_prev:.4f}",
            'status': '✓' if ato_now > ato_prev else '✗'
        },
    ]

    # 總分
    score['total_score'] = sum(
        item['score']
        for group in (score['profitability'], score['leverage'], score['efficiency'])
        for item in group
    )

    return score


def calculate_altman_zscore(df_income, df_balance, market_cap):
    
    df_income = df_income.sort_values("date", ascending=False).reset_index(drop=True)
    df_balance = df_balance.sort_values("date", ascending=False).reset_index(drop=True)

    if df_income.empty or df_balance.empty or market_cap is None:
        return None
    
    ci = df_income.iloc[0]; cb = df_balance.iloc[0]
    ca = cb.get('totalCurrentAssets', 0)
    cl = cb.get('totalCurrentLiabilities', 0)
    ta = cb.get('totalAssets', 1)
    re = cb.get('retainedEarnings', 0)
    oi = ci.get('operatingIncome', 0)
    ie = ci.get('interestExpense', 0)
    tl = cb.get('totalLiabilities', 1)
    rev = ci.get('revenue', 0)
    wc = ca - cl
    ebit = oi + ie

    # DEBUG: 輸出所有來源數字
    print("="*40)
    print(f"【DEBUG Altman Z-Score】")
    print(f"CA (Current Assets):       {ca:,}")
    print(f"CL (Current Liabilities):  {cl:,}")
    print(f"TA (Total Assets):         {ta:,}")
    print(f"RE (Retained Earnings):    {re:,}")
    print(f"OI (Operating Income):     {oi:,}")
    print(f"IE (Interest Expense):     {ie:,}")
    print(f"TL (Total Liabilities):    {tl:,}")
    print(f"REV (Revenue):             {rev:,}")
    print(f"WC (Working Capital):      {wc:,}")
    print(f"EBIT:                      {ebit:,}")
    print(f"Market Cap:                {market_cap:,}")
    print("="*40)
    # 再來正常算你的組成比率
    A = safe_divide(wc, ta) * 1.2
    B = safe_divide(re, ta) * 1.4
    C = safe_divide(ebit, ta) * 3.3
    D = safe_divide(market_cap, tl) * 0.6
    E = safe_divide(rev, ta) * 1.0
    z_score = A+B+C+D+E
    
    risk_level = "安全區域" if z_score > 2.99 else ("灰色區域" if z_score >= 1.81 else "危險區域")
    risk_emoji = "😊" if z_score > 2.99 else ("😐" if z_score >= 1.81 else "😰")    

    return {
        'z_score': z_score,
        'components': {'A': A, 'B': B, 'C': C, 'D': D, 'E': E},
        'risk_level': risk_level,
        'risk_emoji': risk_emoji,
        'base_data': {
            'working_capital': wc,
            'total_assets': ta,
            'retained_earnings': re,
            'ebit': ebit,
            'market_cap': market_cap,
            'total_liabilities': tl,
            'revenues': rev,
        }
    }

def calculate_dupont_analysis(df_income, df_balance):
    
    df_income = df_income.sort_values("date", ascending=False).reset_index(drop=True)
    df_balance = df_balance.sort_values("date", ascending=False).reset_index(drop=True)

    if df_income.empty or df_balance.empty is None:
        return None
    
    if len(df_income) < 3 or len(df_balance) < 3: return None
    
    di = df_income.sort_values('date', ascending=False).reset_index(drop=True)
    db = df_balance.sort_values('date', ascending=False).reset_index(drop=True)
    results = []
    for i in range(min(3, len(di))):
        ir, br = di.iloc[i], db.iloc[i]
        net = ir.get('netIncome', 0)
        rev = ir.get('revenue', 1)
        ta = br.get('totalAssets', 1)
        eq = br.get('totalStockholdersEquity', 1)
        nm = safe_divide(net, rev)
        at = safe_divide(rev, ta)
        em = safe_divide(ta, eq)
        results.append({
            'date': ir.get('date', ''),
            'net_margin': nm,
            'asset_turnover': at,
            'equity_multiplier': em,
            'direct_roe': safe_divide(net, eq)
        })
    # 算變化
    changes = None
    if len(results) >= 2:
        changes = {
            'net_margin_change': results[0]['net_margin'] - results[1]['net_margin'],
            'asset_turnover_change': results[0]['asset_turnover'] - results[1]['asset_turnover'],
            'equity_multiplier_change': results[0]['equity_multiplier'] - results[1]['equity_multiplier'],
            'roe_change': results[0]['direct_roe'] - results[1]['direct_roe'],
        }
    return {'yearly_analysis': results, 'changes': changes}


def calculate_cashflow_analysis(df_income, df_cash):
    df_income = df_income.sort_values("date", ascending=False).reset_index(drop=True)
    df_cash = df_cash.sort_values("date", ascending=False).reset_index(drop=True)

    if df_income.empty or df_cash.empty is None:
        return None
    
    if df_income.empty or df_cash.empty: return None
    
    ci, cc = df_income.iloc[0], df_cash.iloc[0]
    ocf, icf, fcf_flow, net, capex = cc.get('OCF', 0), cc.get('CFI', 0), cc.get('CFF', 0), ci.get('netIncome', 1), cc.get('CapEx', 0)
    ocf_quality = safe_divide(ocf, net)
    if ocf_quality >= 1.2: q, emoji = "優秀", "😊"
    elif ocf_quality >= 1.0: q, emoji = "良好", "🙂"
    elif ocf_quality >= 0.8: q, emoji = "尚可", "😐"
    else: q, emoji = "需關注", "😰"
    total_cf = ocf + icf + fcf_flow
    free_cashflow = cc.get('FCF', ocf - abs(capex))
    return {
        'ocf_quality': ocf_quality, 'free_cashflow': free_cashflow, 'quality_assessment': q, 'quality_emoji': emoji,
        'structure': {'operating': ocf, 'investing': icf, 'financing': fcf_flow, 'total': total_cf}
    }

def format_large_number(num):
    try:
        num = float(num)
        if abs(num) >= 1e12: return f"${num/1e12:.2f}T"
        elif abs(num) >= 1e9: return f"${num/1e9:.2f}B"
        elif abs(num) >= 1e6: return f"${num/1e6:.2f}M"
        else: return f"${num:,.2f}"
    except: return "N/A"
    
    

#%%
# ==================== 日期篩選 ====================
def filter_by_date_range(df, start_date, end_date):
    mask = (df["date"] >= pd.Timestamp(start_date)) & (df["date"] <= pd.Timestamp(end_date))
    filtered_df = df[mask].copy()

    if len(filtered_df) == 0:
        st.warning("⚠️ 選擇的日期範圍內沒有數據，請調整日期範圍")
        return None
    return filtered_df


#%%
# ==================== 技術指標計算 ====================
# 移動平均線
def get_moving_averages(df):
    df = df.copy()
    for n in [5, 10, 20, 60]:
        df[f"MA{n}"] = df["close"].rolling(window=n, min_periods=1).mean()
    return df

#%%
# rsi
def _rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder RSI（用 EWM α=1/period 近似，效能佳）"""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["RSI9"]  = _rsi_wilder(df["close"], 9)
    df["RSI14"] = _rsi_wilder(df["close"], 14)
    return df


#%%
# kd
def add_kd(df: pd.DataFrame, period: int = 9, k_smooth: int = 3, d_smooth: int = 3) -> pd.DataFrame:
    """
    經典台股寫法：
      RSV_t = (Close - Low_n) / (High_n - Low_n) * 100
      K_t   = (2/3)*K_{t-1} + (1/3)*RSV_t   （k_smooth=3）
      D_t   = (2/3)*D_{t-1} + (1/3)*K_t     （d_smooth=3）
    初始值 K0 = D0 = 50
    """
    df = df.copy()
    low_n  = df["low"].rolling(period, min_periods=period).min()
    high_n = df["high"].rolling(period, min_periods=period).max()
    denom = (high_n - low_n).replace(0, np.nan)
    rsv = (df["close"] - low_n) / denom * 100
    df[f"RSV{period}"] = rsv

    # 以經典遞迴實作（非簡單SMA）
    K = np.full(len(df), np.nan, dtype=float)
    D = np.full(len(df), np.nan, dtype=float)
    k_alpha = 1.0 / k_smooth
    d_alpha = 1.0 / d_smooth

    prev_K, prev_D = 50.0, 50.0
    for i in range(len(df)):
        val = rsv.iloc[i]
        if np.isnan(val):
            K[i], D[i] = np.nan, np.nan
            continue
        curr_K = (1 - k_alpha) * prev_K + k_alpha * val
        curr_D = (1 - d_alpha) * prev_D + d_alpha * curr_K
        K[i], D[i] = curr_K, curr_D
        prev_K, prev_D = curr_K, curr_D

    df[f"K{period}"] = K
    df[f"D{period}"] = D
    return df

#%%
# macd
def add_macd(df: pd.DataFrame,
             short_period: int = 12,
             long_period: int = 26,
             signal_period: int = 9) -> pd.DataFrame:
    """
    MACD 指標：
    DIF = EMA(short) - EMA(long)
    MACD = EMA(DIF, signal_period)
    OSC = DIF - MACD （紅綠柱）
    """
    df = df.copy()
    ema_short = df["close"].ewm(span=short_period, adjust=False).mean()
    ema_long  = df["close"].ewm(span=long_period, adjust=False).mean()
    df["DIF"] = ema_short - ema_long
    df["MACD"] = df["DIF"].ewm(span=signal_period, adjust=False).mean()
    df["OSC"] = df["DIF"] - df["MACD"]
    return df


#%%
# Bollinger Bands
def add_bbands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    df = df.copy()
    mid = df["close"].rolling(window=window, min_periods=window).mean()
    std = df["close"].rolling(window=window, min_periods=window).std(ddof=0)  # population std
    upper = mid + num_std * std
    lower = mid - num_std * std
    df["BB_MID"] = mid
    df["BB_UPPER"] = upper
    df["BB_LOWER"] = lower
    return df


#%%
# ==================== AI 資產負債表分析 ====================
def generate_bs_insights(symbol: str, df_balance: pd.DataFrame, openai_api_key: str, periods: int = 8) -> str | None:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)

        if df_balance is None or df_balance.empty:
            return "查無資產負債表資料。"

        # 確保時間序與欄位
        dfb = df_balance.copy()
        if "date" in dfb.columns:
            dfb["date"] = pd.to_datetime(dfb["date"])
            dfb = dfb.sort_values("date")
        cols_needed_raw = [
            "totalAssets","totalLiabilities","totalStockholdersEquity",
            "totalCurrentAssets","totalCurrentLiabilities",
            "cashAndShortTermInvestments","netReceivables","netDebt"
        ]
        for c in cols_needed_raw:
            if c not in dfb.columns:
                dfb[c] = np.nan  # 若缺欄，避免 KeyError

        # 若比率未在 df 中，這裡補上（和你前面 get_balance_ratios 的公式一致）
        if "current_ratio" not in dfb.columns:
            dfb["current_ratio"] = dfb["totalCurrentAssets"] / dfb["totalCurrentLiabilities"]
        if "quick_ratio" not in dfb.columns:
            dfb["quick_ratio"] = (dfb["cashAndShortTermInvestments"] + dfb["netReceivables"]) / dfb["totalCurrentLiabilities"]
        if "cash_ratio" not in dfb.columns:
            dfb["cash_ratio"] = dfb["cashAndShortTermInvestments"] / dfb["totalCurrentLiabilities"]
        if "debt_ratio" not in dfb.columns:
            dfb["debt_ratio"] = dfb["totalLiabilities"] / dfb["totalAssets"]
        if "equity_ratio" not in dfb.columns:
            dfb["equity_ratio"] = dfb["totalStockholdersEquity"] / dfb["totalAssets"]
        if "debt_to_equity" not in dfb.columns:
            dfb["debt_to_equity"] = dfb["totalLiabilities"] / dfb["totalStockholdersEquity"]
        if "net_debt_ratio" not in dfb.columns:
            dfb["net_debt_ratio"] = dfb["netDebt"] / dfb["totalAssets"]

        # 只取需要餵給模型的欄位
        keep_cols = [
            "date","symbol",
            "totalAssets","totalLiabilities","totalStockholdersEquity",
            "totalCurrentAssets","totalCurrentLiabilities",
            "cashAndShortTermInvestments","netReceivables","netDebt",
            "current_ratio","quick_ratio","cash_ratio",
            "debt_ratio","equity_ratio","debt_to_equity","net_debt_ratio"
        ]
        use_cols = [c for c in keep_cols if c in dfb.columns]
        dfb_model = dfb[use_cols].tail(periods).copy()

        # 基本期間描述
        first_date = dfb_model["date"].iloc[0].strftime("%Y-%m-%d") if "date" in dfb_model.columns else "N/A"
        last_date  = dfb_model["date"].iloc[-1].strftime("%Y-%m-%d") if "date" in dfb_model.columns else "N/A"

        # 給模型的 JSON（不做四捨五入，保留精度；模型更好抓趨勢）
        data_json = dfb_model.to_json(orient="records", date_format="iso", force_ascii=False)

        system_msg = (
            "你是一位嚴謹的財務報表分析師"
            "使用繁體中文，聚焦解讀數據與比率含義"
        )

        user_prompt = f"""
        以下為近 {periods} 期資產負債表重點欄位與比率（JSON）：
        {data_json}
        
        根據資料內容，依照下列【固定架構】進行分析
        必須用「條列式」清楚列點，每個項目內細分，要有分點符號（如：•）
        每段標題請加粗（用 ** ），並保持簡潔、重點明確
        
        1 規模與結構（Size & Mix）
        - 分別列出總資產、總負債、股東權益歷史變化，並解說趨勢
        2 償債能力（Liquidity）
        - 分別條出流動比、速動比歷史變化，並解說趨勢
        - 分別列出現金比的相對區間歷史變化，並解說趨勢
        3 槓桿結構（Leverage）
        - 分別列出負債比、權益比、負債權益比歷史變化，並解說趨勢
        4 結語
        """

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=2500,
        )
        return resp.choices[0].message.content

    except Exception as e:
        st.error(f"❌ AI 資產負債表分析失敗: {str(e)}")
        return None

#%%
# ==================== AI 損益表分析 ====================
def generate_is_insights(symbol: str, df_income: pd.DataFrame, openai_api_key: str, periods: int = 8) -> str | None:
    import numpy as np
    import pandas as pd
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)

        if df_income is None or df_income.empty:
            return "查無損益表資料。"

        dfi = df_income.copy()
        if "date" in dfi.columns:
            dfi["date"] = pd.to_datetime(dfi["date"])
            dfi = dfi.sort_values("date")

        use_cols = [
            "date","symbol","period","fiscalYear",
            "revenue","grossProfit","operatingIncome","ebit","ebitda","netIncome",
            "epsDiluted","weightedAverageShsOutDil",
            "gross_margin","operating_margin","ebitda_margin","net_margin",
            "rnd_ratio","sga_ratio","tax_rate","interest_coverage",
            "revenue_ps","netincome_ps",
            "revenue_chg","grossProfit_chg","operatingIncome_chg","ebit_chg","ebitda_chg","netIncome_chg","epsDiluted_chg"
        ]
        use_cols = [c for c in use_cols if c in dfi.columns]
        dfi_model = dfi[use_cols].tail(periods).copy()

        first_date = dfi_model["date"].iloc[0].strftime("%Y-%m-%d") if "date" in dfi_model.columns else "N/A"
        last_date  = dfi_model["date"].iloc[-1].strftime("%Y-%m-%d") if "date" in dfi_model.columns else "N/A"

        data_json = dfi_model.to_json(orient="records", date_format="iso", force_ascii=False)

        system_msg = (
            "你是一位嚴謹的財務報表分析師"
            "使用繁體中文，聚焦解讀數據與比率含義"
        )

        user_prompt = f"""
        以下為近 {periods} 期損益表重點欄位與比率：
        {data_json}

        根據資料內容，依照下列【固定架構】進行分析
        必須用「條列式」清楚列點，每個項目內細分，要有分點符號（如：•）
        每段標題請加粗（用 ** ），並保持簡潔、重點明確

        1 規模與成長（Revenue / GP / OI / EBIT / EBITDA / Net Income / EPS）
        - 分別列出eps趨勢、各科目(如果有要分別列點)的歷史變化與相鄰期變動率，並解說趨勢
        2 獲利能力（Margins）
        - 分別列出毛利率、營業利益率、EBITDA 率、淨利率歷史變化，並解說趨勢
        3 費用結構（Expense Mix）
        - 分別列出研發比率、銷管比率歷史變化，是否反映策略與產品週期，並解說趨勢
        4 結語
        """

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=2500,
        )
        return resp.choices[0].message.content

    except Exception as e:
        st.error(f"❌ AI 損益表分析失敗: {str(e)}")
        return None


#%%
# ==================== AI 現金流量表分析 ====================
def generate_cf_insights(symbol: str, df_cash: pd.DataFrame, openai_api_key: str, periods: int = 8) -> str | None:
    import pandas as pd
    import numpy as np
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)

        if df_cash is None or df_cash.empty:
            return "查無現金流量表資料。"

        dfc = df_cash.copy()
        if "date" in dfc.columns:
            dfc["date"] = pd.to_datetime(dfc["date"])
            dfc = dfc.sort_values("date")

        use_cols = [
            "date","symbol","period","fiscalYear",
            "netIncome","OCF","CFI","CFF","CapEx","FCF",
            "Dividends","Buybacks","Shareholder_Returns",
            "netDebtIssuance",
            "changeInWorkingCapital","stockBasedCompensation","depreciationAndAmortization",
            "cashAtBeginningOfPeriod","cashAtEndOfPeriod",
            "cash_conversion","capex_to_ocf","payout_to_ocf"
        ]
        use_cols = [c for c in use_cols if c in dfc.columns]
        dfc_model = dfc[use_cols].tail(periods).copy()

        first_date = dfc_model["date"].iloc[0].strftime("%Y-%m-%d")
        last_date  = dfc_model["date"].iloc[-1].strftime("%Y-%m-%d")
        data_json  = dfc_model.to_json(orient="records", date_format="iso", force_ascii=False)

        system_msg = (
            "你是一位嚴謹的財務報表分析師"
            "使用繁體中文，聚焦解讀數據與比率含義"
        )
        user_prompt = f"""
            以下為近 {periods} 期現金流量表重點欄位與比率（JSON）：
            {data_json}

            根據資料內容，依照下列【固定架構】進行分析
            必須用「條列式」清楚列點，每個項目內細分，要有分點符號（如：•）
            每段標題請加粗（用 ** ），並保持簡潔、重點明確
            
            1 現金來源與去化
            - 分別列出 OCF / CFI / CFF 歷史變化，並解說趨勢
            2 自由現金流與投資強度
            - 分別列出 FCF / CapEx / capex_to_ocf 歷史變化，並解說趨勢
            3 現金轉換率
            - 分別列出（OCF/淨利） 歷史變化，並解說趨勢
            4 股東回饋（股利、買回）對 OCF 的占比（payout_to_ocf），及資本結構面（netDebtIssuance）
            5 營運資金變動、SBC、折舊攤銷
            6 結語
            """

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=2500,
        )
        return resp.choices[0].message.content

    except Exception as e:
        st.error(f"❌ AI 現金流量表分析失敗: {str(e)}")
        return None


#%%
# ==================== AI 財務分析 ======================
def generate_core_metrics_insights(symbol: str, core: pd.DataFrame, openai_api_key: str, periods: int = 8) -> str | None:
    """
    AI 條列式解讀財務核心指標（如 ROE/ROA、資產週轉率、現金轉換率、FCF Margin 等）
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        import pandas as pd
        import numpy as np

        if core is None or core.empty:
            return "查無核心指標資料。"

        dfc = core.copy()
        if "date" in dfc.columns:
            dfc["date"] = pd.to_datetime(dfc["date"])
            dfc = dfc.sort_values("date")

        use_cols = [
            "date", "ROE", "ROA", "asset_turnover",
            "cash_conversion", "fcf_margin", "capex_to_ocf", "payout_to_ocf",
            "ROE_yoy", "ROA_yoy", "asset_turnover_yoy"
        ]
        use_cols = [c for c in use_cols if c in dfc.columns]
        dfc_model = dfc[use_cols].tail(periods).copy()

        first_date = dfc_model["date"].iloc[0].strftime("%Y-%m-%d")
        last_date  = dfc_model["date"].iloc[-1].strftime("%Y-%m-%d")
        data_json  = dfc_model.to_json(orient="records", date_format="iso", force_ascii=False)

        system_msg = (
            "你是一位嚴謹的財務報表分析師"
            "使用繁體中文，聚焦解讀數據與比率含義"
        )
        user_prompt = f"""
            以下為近 {periods} 期財務核心指標（如 ROE/ROA、資產週轉率、現金轉換率、FCF Margin 等）之數據與比率：
            {data_json}

            根據資料內容，依下列【固定架構】進行分析，必須用「條列式」清楚列點，每個項目內細分，要有分點符號（如：•）
            每段標題請加粗（用 ** ），並保持簡潔、重點明確

            1 ROE / ROA
            - 條列式列出 ROE、ROA 歷史變化，並解說趨勢
            2 資產週轉率
            - 條列式列出資產週轉率，解說趨勢
            3 現金品質
            - 條列式列出現金轉換率、FCF Margin 之歷史變化，並解說
            4 資本支出與股東回饋
            - 條列式列出 CapEx / OCF 與 Payout / OCF（股東回饋比），解說趨勢
            5 結語
        """

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=2500,
        )
        return resp.choices[0].message.content

    except Exception as e:
        st.error(f"❌ AI 核心指標分析失敗: {str(e)}")
        return None


#%%
# ==================== AI 技術面分析 ====================
def generate_ai_insights(symbol, stock_data, openai_api_key):
    from datetime import datetime
    today_date = datetime.today().strftime("%Y-%m-%d")
    
    try:
        client = OpenAI(api_key=openai_api_key)
        first_date = stock_data["date"].iloc[0].strftime("%Y-%m-%d")
        last_date = stock_data["date"].iloc[-1].strftime("%Y-%m-%d")
        start_price = stock_data["close"].iloc[0]
        end_price = stock_data["close"].iloc[-1]
        price_change = ((end_price - start_price) / start_price) * 100
        
        # 
        cols = ["date","open","high","low","close","volume",
        "MA5","MA10","MA20","MA60",
        "RSI9","RSI14","K9","D9",
        "DIF","MACD","OSC",
        "BB_MID","BB_UPPER","BB_LOWER"] 
        use_cols = [c for c in cols if c in stock_data.columns]
        data_json = stock_data[use_cols].tail(30).to_json(orient="records", date_format="iso", force_ascii=False)
        
        system_msg = (
            "你是一位嚴謹的技術面分析師"
            "使用繁體中文，聚焦解讀數據與比率含義"
        )
        user_prompt = f"""
            歷史數據：
            {data_json}
            
            根據資料內容，依照下列【固定架構】進行分析
            必須用「條列式」清楚列點，每個項目內細分，要有分點符號（如：•）
            每段標題請加粗（用 ** ），並保持簡潔、重點明確
        
            1 趨勢、成交量
            2 均線
            3 rsi
            4 kd
            5 macd&OSC
            6 布林通道
            7 波動
            8 近期是否有影響到市場的消息面，原因解說
            9 技術面趨勢結語
            10 上下游可以關注的個股（列出台股、美股代號、關注原因、優劣勢比較)
            11 同業、競爭對手可以關注的個股（列出台股、美股代號、關注原因、優劣勢比較)
            12 分別列出市面上最新不同機構，對公司的估值，機構名稱、機構對此公司評價年月、目標價、評價、需注意點、產業前景(今日為{today_date}，不考慮財報，上網搜集高盛、摩根士丹利、摩根、瑞士信貸等最新評價)
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ AI 分析失敗: {str(e)}")
        return None


#%%
#%% ==================== AI 四階段財報結果 ====================
def generate_four_stage_ai_analysis(symbol, fscore, zscore, dupont, cashflow, openai_api_key):
    from openai import OpenAI
    client = OpenAI(api_key=openai_api_key)
    analysis_text = f"""
        #### 1. Piotroski F-Score 分析
        總分: {fscore['total_score']}/9分

        ##### 獲利能力指標:
        """ + "".join([f"- {i['name']}: {i['status']} (當前: {i['current']}, 前期: {i['previous']})\n" for i in fscore['profitability']]) + \
        """
        ##### 槓桿與流動性指標:
        """ + "".join([f"- {i['name']}: {i['status']} (當前: {i['current']}, 前期: {i['previous']})\n" for i in fscore['leverage']]) + \
        """
        ##### 營運效率指標:
        """ + "".join([f"- {i['name']}: {i['status']} (當前: {i['current']}, 前期: {i['previous']})\n" for i in fscore['efficiency']]) + \
        f"""

        #### 2. Altman Z-Score 分析
        Z-Score: {zscore['z_score']:.2f}
        風險等級: {zscore['risk_level']} {zscore['risk_emoji']}

        組成要素:
        - A項 (營運資本/總資產): {zscore['components']['A']:.4f}
        - B項 (保留盈餘/總資產): {zscore['components']['B']:.4f}
        - C項 (EBIT/總資產): {zscore['components']['C']:.4f}
        - D項 (市值/總負債): {zscore['components']['D']:.4f}
        - E項 (營收/總資產): {zscore['components']['E']:.4f}

#### 3. 杜邦分析
"""
    if dupont and dupont['yearly_analysis']:
        latest = dupont['yearly_analysis'][0]
        analysis_text += f"""
最新年度ROE: {latest['direct_roe']:.4f}
- 淨利率: {latest['net_margin']:.4f}
- 資產周轉率: {latest['asset_turnover']:.4f}
- 權益乘數: {latest['equity_multiplier']:.4f}
"""
    analysis_text += f"""

#### 4. 現金流分析
營運現金流品質比率: {cashflow['ocf_quality']:.2f}
自由現金流: {format_large_number(cashflow['free_cashflow'])}
品質評估: {cashflow['quality_assessment']} {cashflow['quality_emoji']}

現金流結構:
- 營運現金流: {format_large_number(cashflow['structure']['operating'])}
- 投資現金流: {format_large_number(cashflow['structure']['investing'])}
- 融資現金流: {format_large_number(cashflow['structure']['financing'])}
"""

    system_message = "你是一位專業的財務分析師，精通財報分析和投資評估。請基於已計算完成的四階段財務分析結果進行專業解讀。"
    user_message = f"""請基於以下 {symbol} 的四階段財務分析結果，提供專業的投資評估報告：

{analysis_text}

請按以下結構提供分析：
1. **Piotroski F-Score 解讀**
- 解釋得分的投資意義
- 分析各項指標反映的業務狀況
2. **Altman Z-Score 風險評估**
- 解讀風險等級的含義 (<1.81為危險區域，1.81~2.99為灰色區域，>2.99為安全區域)
- 分析各組成要素的影響
3. **杜邦分析趨勢洞察**
- 分析 ROE 三因子的變化
- 識別主要驅動力
4. **現金流結構深度分析**
- 評估現金流品質 (<0.8為需關注，0.8~1.0為尚可，1.1~1.2為良好.>1.2為優秀)
- 分析資本支出模式
5. **綜合財務健康診斷**
- 整體評估
- 潛在風險或機會
6. **投資建議**
- 主要優勢（3-5點）
- 風險因素
- 後續追蹤重點
7. **結論**
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_message}, {"role": "user", "content": user_message}],
        temperature=0.1,
        max_tokens=4000
    )
    return response.choices[0].message.content
