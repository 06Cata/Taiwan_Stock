# tw_stock_ai_insight.py

import streamlit as st
import os
import requests
import pandas as pd
import numpy as np 
import plotly.graph_objects as go
from datetime import datetime, timedelta
from openai import OpenAI
from plotly.subplots import make_subplots

#%%
# ==================== FinMind quarterly ====================
@st.cache_data(ttl=3600)
def get_finmind_data(dataset: str, api_token: str, stock_id: str, start_date: str = '2019-01-01') -> pd.DataFrame:
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": dataset,
        "data_id": stock_id,
        "start_date": start_date,
        "token": api_token,
    }
    if start_date:
        params["start_date"] = start_date
        
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == 200 and data.get("data"):
            return pd.DataFrame(data["data"])
        else:
            st.warning(f"⚠️ {dataset} 查無資料")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ 獲取 {dataset} 失敗: {str(e)}")
        return pd.DataFrame()

#%%
# ==================== FMP get_balance_ratios ====================
def get_balance_ratios(api_token: str, stock_id: str) -> pd.DataFrame:
    df = get_finmind_data("TaiwanStockBalanceSheet", api_token, stock_id)
    
    if df.empty:
        return df
    
    # 轉為寬表格式（每個 date 一行）
    df_pivot = df.pivot_table(
        index=['date', 'stock_id'], 
        columns='type', 
        values='value', 
        aggfunc='first'
    ).reset_index()
    
    df_pivot["date"] = pd.to_datetime(df_pivot["date"])
    df_pivot = df_pivot.sort_values("date", ascending=False).reset_index(drop=True)
    
    # ✅ 添加季度標籤
    df_pivot["quarter_label"] = df_pivot["date"].dt.year.astype(str) + "-Q" + df_pivot["date"].dt.quarter.astype(str)
    
    # 確保必要欄位存在
    required = [
        "TotalAssets", "Liabilities", "Equity",
        "CurrentAssets", "CurrentLiabilities",
        "CashAndCashEquivalents", "AccountsReceivableNet"
    ]
    for col in required:
        if col not in df_pivot.columns:
            df_pivot[col] = np.nan
    
    # 計算比率
    df_pivot["current_ratio"] = df_pivot["CurrentAssets"] / df_pivot["CurrentLiabilities"]
    
    # df_pivot["quick_ratio"] = (
    #     (df_pivot["CashAndCashEquivalents"] + df_pivot["AccountsReceivableNet"]) 
    #     / df_pivot["CurrentLiabilities"]
    # )
    
    den = df_pivot["CurrentLiabilities"].replace({0: np.nan})
    
#     df_pivot["quick_ratio"] = (
#     df_pivot.get("CashAndCashEquivalents", 0).fillna(0)
#     + df_pivot.get("AccountsReceivableNet", 0).fillna(0)
#     + df_pivot.get("CurrentFinancialAssetsAtFairvalueThroughProfitOrLoss", 0).fillna(0)
#     + df_pivot.get("FinancialAssetsAtFairvalueThroughOtherComprehensiveIncome", 0).fillna(0)
#     + df_pivot.get("FinancialAssetsAtAmortizedCost", 0).fillna(0)
# )        / den

    quick_asset_cols = [
    "CashAndCashEquivalents",
    "AccountsReceivableNet", 
    "CurrentFinancialAssetsAtFairvalueThroughProfitOrLoss",
    "FinancialAssetsAtFairvalueThroughOtherComprehensiveIncome",
    "FinancialAssetsAtAmortizedCost"
    ]
    
    df_pivot["quick_ratio"] = sum(
        df_pivot[col].fillna(0) if col in df_pivot.columns else 0
        for col in quick_asset_cols
    ) / den
    
        
    df_pivot["cash_ratio"] = df_pivot["CashAndCashEquivalents"] / den
    
    df_pivot["debt_ratio"] = df_pivot["Liabilities"] / df_pivot["TotalAssets"]
    df_pivot["equity_ratio"] = df_pivot["Equity"] / df_pivot["TotalAssets"]
    df_pivot["debt_to_equity"] = df_pivot["Liabilities"] / df_pivot["Equity"].replace({0: np.nan})
    
    # 長期負債（如果有）
    if "LongtermBorrowings" in df_pivot.columns and "BondsPayable" in df_pivot.columns:
        df_pivot["longTermDebt"] = df_pivot["LongtermBorrowings"].fillna(0) + df_pivot["BondsPayable"].fillna(0)
    else:
        df_pivot["longTermDebt"] = np.nan
    
    # 淨負債（假設短期借款在流動負債中）
    if "ShortTermBorrowings" in df_pivot.columns:
        total_debt = df_pivot["ShortTermBorrowings"].fillna(0) + df_pivot["longTermDebt"].fillna(0)
        df_pivot["netDebt"] = total_debt - df_pivot["CashAndCashEquivalents"].fillna(0)
    else:
        df_pivot["netDebt"] = np.nan
        
    df_pivot["net_debt_ratio"] = df_pivot["netDebt"] / df_pivot["TotalAssets"]
    
    # 保留盈餘
    if "RetainedEarnings" in df_pivot.columns:
        df_pivot["retainedEarnings"] = df_pivot["RetainedEarnings"]
    elif "UnappropriatedRetainedEarningsAaccumulatedDeficit" in df_pivot.columns:
        df_pivot["retainedEarnings"] = df_pivot["UnappropriatedRetainedEarningsAaccumulatedDeficit"]
    else:
        df_pivot["retainedEarnings"] = np.nan
    
    keep_cols = [
        "date", "quarter_label", "stock_id",
        "TotalAssets", "Liabilities", "Equity",
        "CurrentAssets", "CurrentLiabilities",
        "CashAndCashEquivalents", "AccountsReceivableNet",
        "longTermDebt", "netDebt", "retainedEarnings",
        "current_ratio", "quick_ratio", "cash_ratio",
        "debt_ratio", "equity_ratio", "debt_to_equity", "net_debt_ratio"
    ]
    
    df_pivot = df_pivot[[c for c in keep_cols if c in df_pivot.columns]].round(4)
    
    return df_pivot


#%%
# ==================== FMP get_income_ratios ====================
@st.cache_data(ttl=3600)
def get_income_ratios(api_token: str, stock_id: str) -> pd.DataFrame:
    df = get_finmind_data("TaiwanStockFinancialStatements", api_token, stock_id)
    
    if df.empty:
        return df
    
    # 轉為寬表
    df_pivot = df.pivot_table(
        index=['date', 'stock_id'], 
        columns='type', 
        values='value', 
        aggfunc='first'
    ).reset_index()
    
    df_pivot["date"] = pd.to_datetime(df_pivot["date"])
    df_pivot = df_pivot.sort_values("date", ascending=False).reset_index(drop=True)
    
    # ✅ 添加季度標籤
    df_pivot["quarter_label"] = df_pivot["date"].dt.year.astype(str) + "-Q" + df_pivot["date"].dt.quarter.astype(str)
    
    # 欄位映射（FinMind -> 標準名稱）
    rename_map = {
        "Revenue": "revenue",
        "CostOfGoodsSold": "costOfRevenue",
        "GrossProfit": "grossProfit",
        "OperatingExpenses": "operatingExpenses",
        "OperatingIncome": "operatingIncome",
        "PreTaxIncome": "incomeBeforeTax",
        "TAX": "incomeTaxExpense",
        "IncomeAfterTaxes": "netIncome",
        "IncomeFromContinuingOperations": "netIncomeFromContinuingOperations",
        "EPS": "eps",
    }
    
    for old_name, new_name in rename_map.items():
        if old_name in df_pivot.columns:
            df_pivot[new_name] = df_pivot[old_name]
    
    # 確保必要欄位
    required = ["revenue", "grossProfit", "operatingIncome", "netIncome", "costOfRevenue"]
    for col in required:
        if col not in df_pivot.columns:
            df_pivot[col] = np.nan
    
    # EBIT / EBITDA（台股報表可能沒有，用營業利益近似）
    df_pivot["ebit"] = df_pivot.get("operatingIncome", 0)
    df_pivot["ebitda"] = df_pivot.get("operatingIncome", 0)  # 簡化處理
    
    # 計算利潤率
    df_pivot["gross_margin"] = df_pivot["grossProfit"] / df_pivot["revenue"]
    df_pivot["operating_margin"] = df_pivot["operatingIncome"] / df_pivot["revenue"]
    df_pivot["ebit_margin"] = df_pivot["ebit"] / df_pivot["revenue"]
    df_pivot["ebitda_margin"] = df_pivot["ebitda"] / df_pivot["revenue"]
    df_pivot["net_margin"] = df_pivot["netIncome"] / df_pivot["revenue"]
    
    # 費用率（如果有）
    if "OTHNOE" in df_pivot.columns:
        df_pivot["rnd_ratio"] = 0  # FinMind 沒有單獨的研發費用
        df_pivot["sga_ratio"] = df_pivot["operatingExpenses"] / df_pivot["revenue"]
    else:
        df_pivot["rnd_ratio"] = np.nan
        df_pivot["sga_ratio"] = df_pivot.get("operatingExpenses", 0) / df_pivot["revenue"]
    
    # 稅率
    df_pivot["tax_rate"] = df_pivot.get("incomeTaxExpense", 0) / df_pivot.get("incomeBeforeTax", 1)
    
    # 每股營收/盈餘（需要股數，簡化處理）
    df_pivot["epsDiluted"] = df_pivot.get("eps", np.nan)
    df_pivot["revenue_ps"] = np.nan  # 需要流通股數
    df_pivot["netincome_ps"] = np.nan
    
    # === TTM 滾動4季計算 ===
    df_pivot = df_pivot.sort_values("date").reset_index(drop=True)
    
    for col in ["revenue", "grossProfit", "operatingIncome", "ebit", "ebitda", "netIncome"]:
        if col in df_pivot.columns:
            df_pivot[f"{col}_TTM"] = df_pivot[col].rolling(4, min_periods=4).sum()
    
    # === YoY 計算（最新4季 vs 前4季，即 shift 4）===
    for col in ["revenue", "grossProfit", "operatingIncome", "ebit", "ebitda", "netIncome", "epsDiluted"]:
        if col in df_pivot.columns:
            df_pivot[f"{col}_chg"] = df_pivot[col].pct_change(periods=4)  # 4季前比較
    
    df_pivot = df_pivot.sort_values("date", ascending=False).reset_index(drop=True)
    
    keep_cols = [
        "date", "quarter_label", "stock_id",
        "revenue", "grossProfit", "operatingIncome", "ebit", "ebitda", "netIncome",
        "eps", "epsDiluted",
        "gross_margin", "operating_margin", "ebit_margin", "ebitda_margin", "net_margin",
        "rnd_ratio", "sga_ratio", "tax_rate",
        "revenue_ps", "netincome_ps",
        "revenue_TTM", "grossProfit_TTM", "operatingIncome_TTM", "netIncome_TTM",
        "revenue_chg", "grossProfit_chg", "operatingIncome_chg", "netIncome_chg", "epsDiluted_chg"
    ]
    
    df_pivot = df_pivot[[c for c in keep_cols if c in df_pivot.columns]].round(4)
    
    return df_pivot


#%%
# ==================== FMP get_cashflow_ratios ====================
# @st.cache_data(ttl=3600)
# def get_cashflow_ratios(api_token: str, stock_id: str) -> pd.DataFrame:
#     df = get_finmind_data("TaiwanStockCashFlowsStatement", api_token, stock_id)
    
#     if df.empty:
#         return df
    
#     # 轉為寬表
#     df_pivot = df.pivot_table(
#         index=['date', 'stock_id'], 
#         columns='type', 
#         values='value', 
#         aggfunc='first'
#     ).reset_index()
    
#     df_pivot["date"] = pd.to_datetime(df_pivot["date"])
#     df_pivot = df_pivot.sort_values("date", ascending=False).reset_index(drop=True)
    
#     # ✅ 添加季度標籤
#     df_pivot["quarter_label"] = df_pivot["date"].dt.year.astype(str) + "-Q" + df_pivot["date"].dt.quarter.astype(str)
    
#     # 欄位映射
#     df_pivot["OCF"] = df_pivot.get("CashFlowsFromOperatingActivities", 
#                                     df_pivot.get("NetCashInflowFromOperatingActivities", 0))
#     df_pivot["CFI"] = df_pivot.get("CashProvidedByInvestingActivities", 0)
#     df_pivot["CFF"] = df_pivot.get("CashFlowsProvidedFromFinancingActivities", 0)
    
#     # CapEx（取得不動產廠房設備）
#     df_pivot["CapEx"] = df_pivot.get("PropertyAndPlantAndEquipment", 0)
    
#     # FCF
#     df_pivot["FCF"] = df_pivot["OCF"] + df_pivot["CapEx"]  # CapEx通常為負
    
#     # 折舊攤銷
#     df_pivot["depreciationAndAmortization"] = (
#         df_pivot.get("Depreciation", 0) + df_pivot.get("AmortizationExpense", 0)
#     )
    
#     # 股利/買回（FinMind較少提供，暫設為0）
#     df_pivot["Dividends"] = 0
#     df_pivot["Buybacks"] = 0
#     df_pivot["Shareholder_Returns"] = 0
    
#     # 現金餘額
#     df_pivot["cashAtBeginningOfPeriod"] = df_pivot.get("CashBalancesBeginningOfPeriod", 0)
#     df_pivot["cashAtEndOfPeriod"] = df_pivot.get("CashBalancesEndOfPeriod", 0)
    
#     # 營運資金變動（如果有）
#     df_pivot["changeInWorkingCapital"] = np.nan
#     df_pivot["stockBasedCompensation"] = np.nan
#     df_pivot["netDebtIssuance"] = np.nan
    
#     # === TTM 滾動4季計算 ===
#     df_pivot = df_pivot.sort_values("date").reset_index(drop=True)
    
#     for col in ["OCF", "CFI", "CFF", "CapEx", "FCF"]:
#         if col in df_pivot.columns:
#             df_pivot[f"{col}_TTM"] = df_pivot[col].rolling(4, min_periods=4).sum()
    
#     df_pivot = df_pivot.sort_values("date", ascending=False).reset_index(drop=True)
    
#     keep_cols = [
#         "date", "quarter_label", "stock_id",
#         "OCF", "CFI", "CFF", "CapEx", "FCF",
#         "Dividends", "Buybacks", "Shareholder_Returns",
#         "netDebtIssuance",
#         "changeInWorkingCapital", "stockBasedCompensation", "depreciationAndAmortization",
#         "cashAtBeginningOfPeriod", "cashAtEndOfPeriod",
#         "OCF_TTM", "FCF_TTM"
#     ]
    
#     df_pivot = df_pivot[[c for c in keep_cols if c in df_pivot.columns]].round(4)
    
#     return df_pivot

@st.cache_data(ttl=3600)
def get_cashflow_ratios(api_token: str, stock_id: str) -> pd.DataFrame:
    df = get_finmind_data("TaiwanStockCashFlowsStatement", api_token, stock_id)
    if df.empty:
        return df

    # pivot 成寬表
    df_pivot = df.pivot_table(
        index=['date', 'stock_id'],
        columns='type',
        values='value',
        aggfunc='first'
    ).reset_index()

    # 轉 datetime / 年 / 季
    df_pivot["date"] = pd.to_datetime(df_pivot["date"])
    df_pivot["year"] = df_pivot["date"].dt.year
    df_pivot["q"] = df_pivot["date"].dt.quarter
    df_pivot["quarter_label"] = df_pivot["year"].astype(str) + "-Q" + df_pivot["q"].astype(str)

    # 我們要把同年累計(YTD)還原成當季：對每個 stock_id, 每個 year 做差分
    # 先把可能為數值的欄位轉成 numeric（排除 meta 欄位）
    meta_cols = {"date", "stock_id", "year", "q", "quarter_label"}
    # 先確保欄位排序（由早到晚）以利後續 rolling / 差分
    df_pivot = df_pivot.sort_values(["stock_id", "year", "q", "date"]).reset_index(drop=True)

    amount_cols = [c for c in df_pivot.columns if c not in meta_cols]
    # 轉成浮點數（非數字會變 NaN）
    df_pivot[amount_cols] = df_pivot[amount_cols].apply(pd.to_numeric, errors="coerce")

    # 嚴格還原函式：符合你示例的邏輯
    def _convert_group_ytd_to_quarter(g):
        # g 已經是同一 stock_id & year 的子表，且按 q 升序
        # 若 group 裡只有一筆（通常 Q1），就保持不動或按照邏輯處理
        idxs = g.index.tolist()
        if len(idxs) == 0:
            return g
        for col in amount_cols:
            vals = g.loc[idxs, col].to_numpy(dtype=float)
            vals_q = np.zeros_like(vals, dtype=float)
            for i in range(len(vals)):
                cur = vals[i]
                prev = vals[i-1] if i-1 >= 0 else None
                # i == 0 -> 第一季
                if i == 0:
                    if pd.isna(cur) or cur == 0:
                        vals_q[i] = 0.0
                    else:
                        vals_q[i] = cur
                else:
                    # 當前是 NaN 或 0 -> 當季視為 0
                    if pd.isna(cur) or cur == 0:
                        vals_q[i] = 0.0
                    # 若前一季是 NaN 或 0 -> 直接以當前累計視為當季（可能是資料只在這季開始有累計）
                    elif pd.isna(prev) or prev == 0:
                        vals_q[i] = cur
                    else:
                        vals_q[i] = cur - prev
            # 將計算結果回寫回 group（保留 index 對齊）
            g.loc[idxs, col] = vals_q
        return g

    # 針對每個 stock_id 與 year 做轉換
    df_conv = df_pivot.groupby(["stock_id", "year"], group_keys=False).apply(_convert_group_ytd_to_quarter)
    df_conv = df_conv.sort_values(["stock_id", "date"]).reset_index(drop=True)

    # 現在 df_conv 的所有 numeric 欄位都已被還原成「當季」口徑（根據上述嚴格邏輯）
    # 接下來做欄位映射（用已還原的欄位）
    # OCF / CFI / CFF mapping（如果沒有欄位會變成 NaN）
    df_conv["OCF"] = df_conv.get("CashFlowsFromOperatingActivities",
                                 df_conv.get("NetCashInflowFromOperatingActivities", np.nan))
    df_conv["CFI"] = df_conv.get("CashProvidedByInvestingActivities",
                                 df_conv.get("InvestingActivitiesNetCashFlows", np.nan))
    df_conv["CFF"] = df_conv.get("CashFlowsProvidedFromFinancingActivities",
                                 df_conv.get("FinancingActivitiesNetCashFlows", np.nan))

    # CapEx - 這個視資料來源命名不同，試幾個常見候選
    capex_candidates = [
        "AcquisitionOfPropertyPlantAndEquipment", "AdditionsToPropertyPlantAndEquipment",
        "PropertyPlantAndEquipment", "PurchaseOfPropertyPlantAndEquipment",
        "PaymentsForPropertyPlantAndEquipment"
    ]
    df_conv["CapEx"] = np.nan
    for c in capex_candidates:
        if c in df_conv.columns:
            df_conv["CapEx"] = df_conv["CapEx"].fillna(df_conv[c])

    # 若仍是 NaN，嘗試直接用 PropertyAndPlantAndEquipment（如你原本）
    if "CapEx" in df_conv.columns and df_conv["CapEx"].isna().all() and "PropertyAndPlantAndEquipment" in df_conv.columns:
        df_conv["CapEx"] = df_conv["PropertyAndPlantAndEquipment"]

    # FCF（注意 CapEx 通常為負值）
    df_conv["FCF"] = df_conv["OCF"] + df_conv["CapEx"]

    # 折舊攤銷
    dep_cands = ["Depreciation", "AmortizationExpense", "DepreciationAndAmortization"]
    df_conv["depreciationAndAmortization"] = np.nan
    for c in dep_cands:
        if c in df_conv.columns:
            df_conv["depreciationAndAmortization"] = df_conv["depreciationAndAmortization"].fillna(df_conv[c])

    # 股利/買回/現金餘額欄位（若存在就取）
    if "DividendsPaid" in df_conv.columns:
        df_conv["Dividends"] = df_conv["DividendsPaid"]
    else:
        df_conv["Dividends"] = 0.0
    # FinMind 可能沒 buybacks 欄位，預設 0
    df_conv["Buybacks"] = df_conv.get("Buybacks", 0.0)
    df_conv["Shareholder_Returns"] = df_conv.get("ShareholderReturns", 0.0)

    df_conv["cashAtBeginningOfPeriod"] = df_conv.get("CashBalancesBeginningOfPeriod", df_conv.get("CashAtBeginningOfPeriod", np.nan))
    df_conv["cashAtEndOfPeriod"] = df_conv.get("CashBalancesEndOfPeriod", df_conv.get("CashAtEndOfPeriod", np.nan))

    # 其他欄位預填 NaN（若來源有再替換）
    df_conv["changeInWorkingCapital"] = df_conv.get("ChangeInWorkingCapital", np.nan)
    df_conv["stockBasedCompensation"] = df_conv.get("StockBasedCompensation", np.nan)
    df_conv["netDebtIssuance"] = df_conv.get("NetDebtIssuance", np.nan)

    # === 計算 TTM（過去 4 季合計），每個 stock_id 做 rolling sum（需按 date 升序）
    df_conv = df_conv.sort_values(["stock_id", "date"]).reset_index(drop=True)
    for col in ["OCF", "CFI", "CFF", "CapEx", "FCF"]:
        if col in df_conv.columns:
            df_conv[f"{col}_TTM"] = df_conv.groupby("stock_id")[col].rolling(window=4, min_periods=4).sum().reset_index(level=0, drop=True)

    # 最後整理輸出欄位（你要的 keep_cols）
    keep_cols = [
        "date", "quarter_label", "stock_id",
        "OCF", "CFI", "CFF", "CapEx", "FCF",
        "Dividends", "Buybacks", "Shareholder_Returns",
        "netDebtIssuance",
        "changeInWorkingCapital", "stockBasedCompensation", "depreciationAndAmortization",
        "cashAtBeginningOfPeriod", "cashAtEndOfPeriod",
        "OCF_TTM", "FCF_TTM"
    ]
    out_cols = [c for c in keep_cols if c in df_conv.columns]

    # 把數字四捨五入並把 date 排回降序（與你原本一致）
    result = df_conv[out_cols].copy()
    num_cols = [c for c in result.columns if c not in {"date", "quarter_label", "stock_id"}]
    result[num_cols] = result[num_cols].round(4)
    result = result.sort_values("date", ascending=False).reset_index(drop=True)

    return result



#%%
# ==== FMP 3 financial ===
@st.cache_data(ttl=3600)
def compute_core_cross_metrics_from_frames(
    inc: pd.DataFrame,
    bal: pd.DataFrame,
    cfs: pd.DataFrame
) -> pd.DataFrame:
    """
    合併三張表計算核心指標 — 全部以『單季口徑』計算：
    - 單季 ROE = 單季淨利 / 平均權益((本季+前季)/2)
    - 單季 ROA = 單季淨利 / 平均資產((本季+前季)/2)
    - 資產週轉率 = 單季營收 / 平均資產
    - cash_conversion = 單季 OCF / 單季淨利
    - fcf_margin = 單季 FCF / 單季營收
    - capex_to_ocf = -單季 CapEx / 單季 OCF
    """
    if any(df is None or df.empty for df in [inc, bal, cfs]):
        return pd.DataFrame()

    inc, bal, cfs = inc.copy(), bal.copy(), cfs.copy()

    for df_ in (inc, bal, cfs):
        df_["date"] = pd.to_datetime(df_["date"])
        df_["quarter"] = df_["date"].dt.to_period("Q").astype(str)

    # 合併（用 quarter 對齊）
    df = (
        inc.merge(bal, on=["stock_id", "quarter"], how="inner", suffixes=("_inc", "_bal"))
           .merge(cfs, on=["stock_id", "quarter"], how="inner", suffixes=("", "_cfs"))
    )

    if df.empty:
        return df

    # 使用資產負債表的 date 為主（若有），確保每個 stock_id 內時間排序
    df["date"] = df.get("date_bal", df.get("date"))
    df = df.sort_values(["stock_id", "date"]).reset_index(drop=True)
    df["quarter_label"] = df["date"].dt.year.astype(str) + "-Q" + df["date"].dt.quarter.astype(str)

    # --- 取單季欄位（若沒有則為 NaN） ---
    net_income_q = df.get("netIncome", np.nan)            # 單季淨利
    revenue_q = df.get("revenue", np.nan)                 # 單季營收
    ocf_q = df.get("OCF", np.nan)                         # 單季營運現金流
    capex_q = df.get("CapEx", np.nan)                     # 單季 CapEx（通常為負）
    # FCF 單季 = OCF + CapEx（CapEx 通常是負數）
    fcf_q = np.where(pd.isna(ocf_q) & pd.isna(capex_q), np.nan, (ocf_q.fillna(0) + capex_q.fillna(0)))

    # 嘗試抓股利 / 回購（若沒提供就 0）
    dividends_q = df.get("Dividends", df.get("DividendsPaid", 0))
    buybacks_q = df.get("Buybacks", 0)

    # 時點資產/權益與前季（用於平均）
    df["assets_prev"] = df.groupby("stock_id")["TotalAssets"].shift(1)
    df["equity_prev"] = df.groupby("stock_id")["Equity"].shift(1)

    df["avg_assets"] = (df["TotalAssets"] + df["assets_prev"]) / 2.0
    df["avg_equity"] = (df["Equity"] + df["equity_prev"]) / 2.0

    def _safe_div(num, den):
        return np.where((den != 0) & (~pd.isna(den)), num / den, np.nan)

    # === 指標（單季口徑） ===
    df["ROE"] = _safe_div(net_income_q, df["avg_equity"]) * 100                # 單季 ROE (%)
    df["ROA"] = _safe_div(net_income_q, df["avg_assets"]) * 100                # 單季 ROA (%)
    df["asset_turnover"] = _safe_div(revenue_q, df["avg_assets"])              # 季度資產週轉率（季度營收 / 平均資產）
    df["cash_conversion"] = _safe_div(ocf_q, net_income_q)                     # 單季 OCF / 單季淨利
    df["fcf_margin"] = _safe_div(fcf_q, revenue_q)                             # 單季 FCF / 單季營收
    df["capex_to_ocf"] = _safe_div(-capex_q, ocf_q)                            # -CapEx / OCF（若 CapEx 負，分子為正）
    df["payout_to_ocf"] = _safe_div(dividends_q.fillna(0), ocf_q)              # 股利 / OCF（若資料缺則為 NaN 或 0，視來源）

    # 若你不想把 dividends/buybacks 當 0，可把上面候補預設改為 np.nan

    # YoY：以單季指標與 4 季前比較（同季比較）
    for col in ["ROE", "ROA", "asset_turnover", "cash_conversion", "fcf_margin", "capex_to_ocf", "payout_to_ocf"]:
        df[f"{col}_yoy"] = df.groupby("stock_id")[col].pct_change(periods=4)

    # 選要輸出的欄位
    keep = [
        "date", "quarter_label", "stock_id",
        "ROE", "ROA", "asset_turnover",
        "cash_conversion", "fcf_margin", "capex_to_ocf", "payout_to_ocf",
        "ROE_yoy", "ROA_yoy", "asset_turnover_yoy", "cash_conversion_yoy", "fcf_margin_yoy",
        "capex_to_ocf_yoy", "payout_to_ocf_yoy"
    ]

    out = df[[c for c in keep if c in df.columns]].copy()
    out = out.sort_values(["stock_id", "date"], ascending=[True, False]).reset_index(drop=True)

    return out


#%%
# ==================== others ====================
@st.cache_data(ttl=3600)
def get_company_profile(api_token: str, stock_id: str) -> dict:
    df = get_finmind_data("TaiwanStockInfo", api_token, stock_id)
    return df

@st.cache_data(ttl=3600)
def get_company_per(api_token: str, stock_id: str) -> pd.DataFrame:
    df = get_finmind_data("TaiwanStockPER", api_token, stock_id)
    return df


#%%
# ==================== FMP daily ====================
@st.cache_data(ttl=3600)
def get_stock_data(api_token: str, stock_id: str)  -> pd.DataFrame:
    start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    df = get_finmind_data("TaiwanStockPrice", api_token, stock_id, start_date)
    
    if df.empty:
        return None
    
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    # 確保必要欄位
    required = ["open", "max", "min", "close", "Trading_Volume"]
    for col in required:
        if col not in df.columns:
            df[col] = 0
    
    # 重新命名以匹配原程式碼
    df = df.rename(columns={
        "max": "high",
        "min": "low",
        "Trading_Volume": "volume"
    })
    
    return df

#%%
def filter_by_date_range(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """日期範圍篩選"""
    if df is None or df.empty:
        return None
    
    mask = (df["date"] >= pd.Timestamp(start_date)) & (df["date"] <= pd.Timestamp(end_date))
    filtered_df = df[mask].copy()
    
    if len(filtered_df) == 0:
        st.warning("⚠️ 選擇的日期範圍內沒有資料，請調整日期範圍")
        return None
    
    return filtered_df


#%%
# ==================== 技術指標計算 ====================
def get_moving_averages(df):
    """計算移動平均線"""
    df = df.copy()
    for n in [5, 10, 20, 60]:
        df[f"MA{n}"] = df["close"].rolling(window=n, min_periods=1).mean()
    return df


def _rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder RSI"""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """新增RSI指標"""
    df = df.copy()
    df["RSI9"] = _rsi_wilder(df["close"], 9)
    df["RSI14"] = _rsi_wilder(df["close"], 14)
    return df


def add_kd(df: pd.DataFrame, period: int = 9, k_smooth: int = 3, d_smooth: int = 3) -> pd.DataFrame:
    """新增KD指標"""
    df = df.copy()
    low_n = df["low"].rolling(period, min_periods=period).min()
    high_n = df["high"].rolling(period, min_periods=period).max()
    denom = (high_n - low_n).replace(0, np.nan)
    rsv = (df["close"] - low_n) / denom * 100
    df[f"RSV{period}"] = rsv
    
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


def add_macd(df: pd.DataFrame, short_period: int = 12, long_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """新增MACD指標"""
    df = df.copy()
    ema_short = df["close"].ewm(span=short_period, adjust=False).mean()
    ema_long = df["close"].ewm(span=long_period, adjust=False).mean()
    df["DIF"] = ema_short - ema_long
    df["MACD"] = df["DIF"].ewm(span=signal_period, adjust=False).mean()
    df["OSC"] = df["DIF"] - df["MACD"]
    return df


def add_bbands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """新增布林通道"""
    df = df.copy()
    mid = df["close"].rolling(window=window, min_periods=window).mean()
    std = df["close"].rolling(window=window, min_periods=window).std(ddof=0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    df["BB_MID"] = mid
    df["BB_UPPER"] = upper
    df["BB_LOWER"] = lower
    return df


#%%
# ==================== 四階段財報分析計算 ====================
def safe_divide(numerator, denominator, default=0):
    """安全除法，避免除以零"""
    try:
        numerator = float(numerator) if not pd.isna(numerator) else 0
        denominator = float(denominator) if not pd.isna(denominator) else 1
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


def format_large_number(num):
    """格式化大數字顯示"""
    try:
        num = float(num)
        if abs(num) >= 1e12: return f"${num/1e12:.2f}T"
        elif abs(num) >= 1e9: return f"${num/1e9:.2f}B"
        elif abs(num) >= 1e6: return f"${num/1e6:.2f}M"
        else: return f"${num:,.2f}"
    except:
        return "N/A"


def calculate_weighted_avg_shares(df_income: pd.DataFrame) -> float:
    """
    計算加權平均股數（補償機制）
    weightedAverageShsOutDil = netIncome ÷ EPS
    """
    if df_income is None or df_income.empty:
        return np.nan
    
    # 取最新一期資料
    latest = df_income.iloc[0]
    net_income = latest.get('netIncome', 0)
    eps = latest.get('eps', latest.get('epsDiluted', 0))
    
    if eps != 0 and not pd.isna(eps):
        return abs(net_income / eps)
    return np.nan


def estimate_interest_expense(df_income: pd.DataFrame) -> float:
    """
    推估利息費用（補償機制）
    interestExpense = abs(營業外支出) if 營業外 < 0 else 0
    """
    if df_income is None or df_income.empty:
        return 0
    
    latest = df_income.iloc[0]
    non_op = latest.get('TotalNonoperatingIncomeAndExpense', 0)
    
    if non_op < 0:
        return abs(non_op)
    return 0


def calculate_market_cap(df_balance: pd.DataFrame, pbr_df: pd.DataFrame) -> float:
    """
    計算市值（補償機制）
    market_cap = PBR × stockholdersEquity
    """
    if df_balance is None or df_balance.empty:
        return None
    
    latest_balance = df_balance.iloc[0]
    equity = latest_balance.get('Equity', 0)
    
    # 嘗試從 PBR DataFrame 取得最新 PBR
    pbr_value = None
    if pbr_df is not None and not pbr_df.empty:
        candidate_cols = ["PBR", "pb", "pb_ratio", "PB", "PriceBookValueRatio"]
        for c in candidate_cols:
            if c in pbr_df.columns:
                try:
                    pbr_value = float(pd.to_numeric(pbr_df[c], errors="coerce").dropna().iloc[-1])
                    break
                except:
                    pass
    
    if pbr_value and equity and not pd.isna(pbr_value) and not pd.isna(equity):
        return pbr_value * equity
    
    return None


def aggregate_quarterly_to_annual(df: pd.DataFrame, periods_latest: int = 4, periods_previous: int = 4) -> dict:
    """
    將季報合併為年度資料（帶四捨五入）
    最新年度：t0-t3（最新4季）
    前一年度：t4-t7（前4季）
    回傳：{'current': {...}, 'previous': {...}}
    """
    if df is None or df.empty or len(df) < (periods_latest + periods_previous):
        return None
    
    # 確保按日期降序排列
    df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    # 最新年度（t0-t3）
    current_data = df.iloc[:periods_latest]
    
    # 前一年度（t4-t7）
    previous_data = df.iloc[periods_latest:periods_latest + periods_previous]
    
    def _aggregate(data_df):
        """對單一年度資料進行加總或平均（帶四捨五入）"""
        result = {}
        
        # 需要加總的欄位（損益表、現金流量表）
        sum_cols = [
            'revenue', 'grossProfit', 'operatingIncome', 'netIncome', 'ebit', 'ebitda',
            'costOfRevenue', 'operatingExpenses', 'incomeBeforeTax', 'incomeTaxExpense',
            'OCF', 'CFI', 'CFF', 'CapEx', 'FCF',
            'depreciationAndAmortization', 'Dividends', 'Buybacks'
        ]
        
        # 需要取平均的欄位（資產負債表）
        avg_cols = [
            'TotalAssets', 'Liabilities', 'Equity', 'CurrentAssets', 'CurrentLiabilities',
            'CashAndCashEquivalents', 'AccountsReceivableNet', 'longTermDebt', 'retainedEarnings'
        ]
        
        # 【策略一】加總欄位：先 round(2) 每個季度值，再加總
        for col in sum_cols:
            if col in data_df.columns:
                # 先對每季數據四捨五入，再加總
                rounded_series = data_df[col].round(2)
                result[col] = round(rounded_series.sum(), 2)
        
        # 【策略二】平均欄位：先平均，再 round(2) 結果
        for col in avg_cols:
            if col in data_df.columns:
                # 先計算平均，再對結果四捨五入
                result[col] = round(data_df[col].mean(), 2)
        
        return result
    
    return {
        'current': _aggregate(current_data),
        'previous': _aggregate(previous_data)
    }


# def calculate_piotroski_fscore(df_income: pd.DataFrame, df_balance: pd.DataFrame, df_cash: pd.DataFrame) -> dict:
#     """
#     計算 Piotroski F-Score（台股版）
#     使用最新4季 vs 前4季的年度比較
#     """
#     # 合併季報為年度
#     income_annual = aggregate_quarterly_to_annual(df_income)
#     balance_annual = aggregate_quarterly_to_annual(df_balance)
#     cash_annual = aggregate_quarterly_to_annual(df_cash)
    
#     if not all([income_annual, balance_annual, cash_annual]):
#         return None
    
#     # 當期與前期資料
#     ci, pi = income_annual['current'], income_annual['previous']
#     cb, pb = balance_annual['current'], balance_annual['previous']
#     cc, pc = cash_annual['current'], cash_annual['previous']
    
#     # 計算加權平均股數
#     shares_now = calculate_weighted_avg_shares(df_income)
#     shares_prev = calculate_weighted_avg_shares(df_income.iloc[4:8] if len(df_income) >= 8 else df_income)
    
#     # ===== 指標計算 =====
#     # ROA
#     roa_now = safe_divide(ci.get('netIncome', 0), cb.get('TotalAssets', 1))
#     roa_prev = safe_divide(pi.get('netIncome', 0), pb.get('TotalAssets', 1))
    
#     # 營運現金流
#     ocf_now = cc.get('OCF', 0)
#     ocf_prev = pc.get('OCF', 0)
#     net_income_now = ci.get('netIncome', 0)
#     net_income_prev = pi.get('netIncome', 0)
    
#     # 流動比率
#     ca_now = cb.get('CurrentAssets', 0)
#     ca_prev = pb.get('CurrentAssets', 0)
#     cl_now = cb.get('CurrentLiabilities', 1)
#     cl_prev = pb.get('CurrentLiabilities', 1)
#     cr_now = safe_divide(ca_now, cl_now)
#     cr_prev = safe_divide(ca_prev, cl_prev)
    
#     # 長期負債比率
#     ltd_now = cb.get('longTermDebt', 0)
#     ltd_prev = pb.get('longTermDebt', 0)
#     ltd_now_ratio = safe_divide(ltd_now, cb.get('TotalAssets', 1))
#     ltd_prev_ratio = safe_divide(ltd_prev, pb.get('TotalAssets', 1))
    
#     # 營運效率
#     gpm_now = safe_divide(ci.get('grossProfit', 0), ci.get('revenue', 1))
#     gpm_prev = safe_divide(pi.get('grossProfit', 0), pi.get('revenue', 1))
#     ato_now = safe_divide(ci.get('revenue', 0), cb.get('TotalAssets', 1))
#     ato_prev = safe_divide(pi.get('revenue', 0), pb.get('TotalAssets', 1))
    
#     # ===== 組裝評分 =====
#     score = {'profitability_scores': [], 'leverage_scores': [], 'efficiency_scores': [], 'total_score': 0}
    
#     # 1) 獲利能力（4項）
#     score['profitability_scores'] = [
#         {'name': 'ROA正值', 'score': int(roa_now > 0), 'current': f"{roa_now:.4f}", 
#          'previous': f"{roa_prev:.4f}", 'status': '✓' if roa_now > 0 else '✗'},
#         {'name': '營運現金流正值', 'score': int(ocf_now > 0), 'current': f"${ocf_now:,.0f}", 
#          'previous': f"${ocf_prev:,.0f}", 'status': '✓' if ocf_now > 0 else '✗'},
#         {'name': 'ROA年增', 'score': int(roa_now > roa_prev), 'current': f"{roa_now-roa_prev:.4f}", 
#          'previous': "-", 'status': '✓' if roa_now > roa_prev else '✗'},
#         {'name': '現金流品質（OCF > 淨利）', 'score': int(ocf_now > net_income_now), 
#          'current': f"${ocf_now-net_income_now:,.0f}", 'previous': f"${ocf_prev-net_income_prev:,.0f}", 
#          'status': '✓' if ocf_now > net_income_now else '✗'},
#     ]
    
#     # 2) 槓桿與流動性（3項）
#     score['leverage_scores'] = [
#         {'name': '長期負債比率改善', 'score': int(ltd_now_ratio < ltd_prev_ratio), 
#          'current': f"{ltd_now_ratio:.4f}", 'previous': f"{ltd_prev_ratio:.4f}", 
#          'status': '✓' if ltd_now_ratio < ltd_prev_ratio else '✗'},
#         {'name': '流動比率改善', 'score': int(cr_now > cr_prev), 'current': f"{cr_now:.2f}", 
#          'previous': f"{cr_prev:.2f}", 'status': '✓' if cr_now > cr_prev else '✗'},
#         {'name': '股份未稀釋', 'score': int(shares_now <= shares_prev) if (shares_now and shares_prev) else 0, 
#          'current': f"{shares_now:,.0f}" if shares_now else "N/A", 
#          'previous': f"{shares_prev:,.0f}" if shares_prev else "N/A", 
#          'status': '✓' if (shares_now and shares_prev and shares_now <= shares_prev) else '✗'},
#     ]
    
#     # 3) 營運效率（2項）
#     score['efficiency_scores'] = [
#         {'name': '毛利率改善', 'score': int(gpm_now > gpm_prev), 'current': f"{gpm_now:.4f}", 
#          'previous': f"{gpm_prev:.4f}", 'status': '✓' if gpm_now > gpm_prev else '✗'},
#         {'name': '資產周轉率改善', 'score': int(ato_now > ato_prev), 'current': f"{ato_now:.4f}", 
#          'previous': f"{ato_prev:.4f}", 'status': '✓' if ato_now > ato_prev else '✗'},
#     ]
    
#     # 總分
#     score['total_score'] = sum(
#         item['score']
#         for group in (score['profitability_scores'], score['leverage_scores'], score['efficiency_scores'])
#         for item in group
#     )
    
#     return score


# def calculate_altman_zscore(df_income: pd.DataFrame, df_balance: pd.DataFrame, market_cap: float) -> dict:
#     """
#     計算 Altman Z-Score（台股版）
#     """
#     income_annual = aggregate_quarterly_to_annual(df_income)
#     balance_annual = aggregate_quarterly_to_annual(df_balance)
    
#     if not all([income_annual, balance_annual, market_cap]):
#         return None
    
#     ci = income_annual['current']
#     cb = balance_annual['current']
    
#     # 取得必要數據
#     ca = cb.get('CurrentAssets', 0)
#     cl = cb.get('CurrentLiabilities', 0)
#     ta = cb.get('TotalAssets', 1)
#     re = cb.get('retainedEarnings', 0)
#     oi = ci.get('operatingIncome', 0)
#     ie = estimate_interest_expense(df_income)
#     tl = cb.get('Liabilities', 1)
#     rev = ci.get('revenue', 0)
    
#     wc = ca - cl
#     ebit = oi + ie  # 直接相加，不使用 abs()
    
#     # 計算五個組成要素
#     A = safe_divide(wc, ta) * 1.2
#     B = safe_divide(re, ta) * 1.4
#     C = safe_divide(ebit, ta) * 3.3
#     D = safe_divide(market_cap, tl) * 0.6
#     E = safe_divide(rev, ta) * 1.0
    
#     z_score = A + B + C + D + E
    
#     # 風險等級
#     if z_score > 2.99:
#         risk_level, risk_emoji = "安全區域", "😊"
#     elif z_score >= 1.81:
#         risk_level, risk_emoji = "灰色區域", "😐"
#     else:
#         risk_level, risk_emoji = "危險區域", "😰"
    
#     return {
#         'z_score': z_score,
#         'components': {'A': A, 'B': B, 'C': C, 'D': D, 'E': E},
#         'risk_level': risk_level,
#         'risk_emoji': risk_emoji,
#         'base_data': {
#             'working_capital': wc,
#             'total_assets': ta,
#             'retained_earnings': re,
#             'ebit': ebit,
#             'market_cap': market_cap,
#             'total_liabilities': tl,
#             'revenues': rev,
#         }
#     }


# def calculate_dupont_analysis(df_income: pd.DataFrame, df_balance: pd.DataFrame) -> dict:
#     """
#     杜邦分析（台股版）
#     分析最近3年（12季）的ROE三因子
#     """
#     if df_income is None or df_income.empty or df_balance is None or df_balance.empty:
#         return None
    
#     if len(df_income) < 12 or len(df_balance) < 12:
#         return None
    
#     results = []
    
#     # 計算最近3年（每年4季）
#     for year_idx in range(3):
#         start_idx = year_idx * 4
#         end_idx = start_idx + 4
        
#         income_data = aggregate_quarterly_to_annual(df_income.iloc[start_idx:end_idx + 4], periods_latest=4, periods_previous=4)
#         balance_data = aggregate_quarterly_to_annual(df_balance.iloc[start_idx:end_idx + 4], periods_latest=4, periods_previous=4)
        
#         if not income_data or not balance_data:
#             continue
        
#         ci = income_data['current']
#         cb = balance_data['current']
        
#         net = ci.get('netIncome', 0)
#         rev = ci.get('revenue', 1)
#         ta = cb.get('TotalAssets', 1)
#         eq = cb.get('Equity', 1)
        
#         nm = safe_divide(net, rev)  # 淨利率
#         at = safe_divide(rev, ta)   # 資產週轉率
#         em = safe_divide(ta, eq)    # 權益乘數
        
#         # 取最新一季的日期作為年度標記
#         date_label = df_income.iloc[start_idx].get('date', '')
        
#         results.append({
#             'date': date_label,
#             'net_margin': nm,
#             'asset_turnover': at,
#             'equity_multiplier': em,
#             'direct_roe': safe_divide(net, eq)
#         })
    
#     # 計算變化
#     changes = None
#     if len(results) >= 2:
#         changes = {
#             'net_margin_change': results[0]['net_margin'] - results[1]['net_margin'],
#             'asset_turnover_change': results[0]['asset_turnover'] - results[1]['asset_turnover'],
#             'equity_multiplier_change': results[0]['equity_multiplier'] - results[1]['equity_multiplier'],
#             'roe_change': results[0]['direct_roe'] - results[1]['direct_roe'],
#         }
    
#     return {'yearly_analysis': results, 'changes': changes}


# def calculate_cashflow_analysis(df_income: pd.DataFrame, df_cash: pd.DataFrame) -> dict:
#     """
#     現金流分析（台股版）
#     """
#     income_annual = aggregate_quarterly_to_annual(df_income)
#     cash_annual = aggregate_quarterly_to_annual(df_cash)
    
#     if not all([income_annual, cash_annual]):
#         return None
    
#     ci = income_annual['current']
#     cc = cash_annual['current']
    
#     ocf = cc.get('OCF', 0)
#     cfi = cc.get('CFI', 0)
#     cff = cc.get('CFF', 0)
#     net = ci.get('netIncome', 1)
#     capex = cc.get('CapEx', 0)
    
#     # 現金流品質比率
#     ocf_quality = safe_divide(ocf, net)
    
#     # 品質評估
#     if ocf_quality >= 1.2:
#         q, emoji = "優秀", "😊"
#     elif ocf_quality >= 1.0:
#         q, emoji = "良好", "🙂"
#     elif ocf_quality >= 0.8:
#         q, emoji = "尚可", "😐"
#     else:
#         q, emoji = "需關注", "😰"
    
#     # 自由現金流（使用絕對值確保 CapEx 為正）
#     free_cashflow = ocf - abs(capex)
    
#     total_cf = ocf + cfi + cff
    
#     return {
#         'ocf_quality': ocf_quality,
#         'free_cashflow': free_cashflow,
#         'quality_assessment': q,
#         'quality_emoji': emoji,
#         'structure': {
#             'operating': ocf,
#             'investing': cfi,
#             'financing': cff,
#             'total': total_cf
#         }
#     }

# # ==================== 四階段財報分析計算（修正排序問題）====================

# def calculate_piotroski_fscore(df_income: pd.DataFrame, df_balance: pd.DataFrame, df_cash: pd.DataFrame) -> dict:
#     """
#     計算 Piotroski F-Score（台股版）
#     使用最新4季 vs 前4季的年度比較
#     """
#     print("\n" + "="*80)
#     print("📊 Piotroski F-Score 計算過程")
#     print("="*80)
    
#     # ⚠️ 確保數據按日期降序排列（最新的在前，索引0是最新的季度）
#     if df_income is not None and not df_income.empty:
#         df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
#     if df_balance is not None and not df_balance.empty:
#         df_balance = df_balance.sort_values('date', ascending=False).reset_index(drop=True)
#     if df_cash is not None and not df_cash.empty:
#         df_cash = df_cash.sort_values('date', ascending=False).reset_index(drop=True)
    
#     print(f"\n🔍 數據範圍檢查：")
#     if df_income is not None and not df_income.empty:
#         print(f"  損益表: {len(df_income)} 季，最新: {df_income.iloc[0]['date'].strftime('%Y-%m-%d')}, 最舊: {df_income.iloc[-1]['date'].strftime('%Y-%m-%d')}")
#     if df_balance is not None and not df_balance.empty:
#         print(f"  資產負債表: {len(df_balance)} 季，最新: {df_balance.iloc[0]['date'].strftime('%Y-%m-%d')}, 最舊: {df_balance.iloc[-1]['date'].strftime('%Y-%m-%d')}")
#     if df_cash is not None and not df_cash.empty:
#         print(f"  現金流量表: {len(df_cash)} 季，最新: {df_cash.iloc[0]['date'].strftime('%Y-%m-%d')}, 最舊: {df_cash.iloc[-1]['date'].strftime('%Y-%m-%d')}")
    
#     # 合併季報為年度
#     income_annual = aggregate_quarterly_to_annual(df_income)
#     balance_annual = aggregate_quarterly_to_annual(df_balance)
#     cash_annual = aggregate_quarterly_to_annual(df_cash)
    
#     if not all([income_annual, balance_annual, cash_annual]):
#         return None
    
#     # 打印原始季度數據（最新4季，從早到晚顯示）
#     print("\n📅 損益表 - 最新4季（t0-t3）數據（從早到晚顯示）：")
#     if df_income is not None and not df_income.empty and len(df_income) >= 4:
#         # iloc[:4] 取索引 0,1,2,3（最新的4季）
#         latest_4q = df_income.iloc[:4].copy()
#         # 反轉順序以從早到晚顯示
#         latest_4q = latest_4q.sort_values('date', ascending=True)
#         for idx, row in latest_4q.iterrows():
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 營收: {row.get('revenue', 0):,.0f} | 淨利: {row.get('netIncome', 0):,.0f}")
    
#     print("\n📅 損益表 - 前4季（t4-t7）數據（從早到晚顯示）：")
#     if df_income is not None and len(df_income) >= 8:
#         # iloc[4:8] 取索引 4,5,6,7（前4季）
#         prev_4q = df_income.iloc[4:8].copy()
#         prev_4q = prev_4q.sort_values('date', ascending=True)
#         for idx, row in prev_4q.iterrows():
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 營收: {row.get('revenue', 0):,.0f} | 淨利: {row.get('netIncome', 0):,.0f}")
    
#     print("\n📅 資產負債表 - 最新4季（t0-t3）數據（從早到晚顯示）：")
#     if df_balance is not None and not df_balance.empty and len(df_balance) >= 4:
#         latest_4q = df_balance.iloc[:4].copy()
#         latest_4q = latest_4q.sort_values('date', ascending=True)
#         for idx, row in latest_4q.iterrows():
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 總資產: {row.get('TotalAssets', 0):,.0f} | 股東權益: {row.get('Equity', 0):,.0f}")
    
#     print("\n📅 現金流量表 - 最新4季（t0-t3）數據（從早到晚顯示）：")
#     if df_cash is not None and not df_cash.empty and len(df_cash) >= 4:
#         latest_4q = df_cash.iloc[:4].copy()
#         latest_4q = latest_4q.sort_values('date', ascending=True)
#         for idx, row in latest_4q.iterrows():
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | OCF: {row.get('OCF', 0):,.0f} | FCF: {row.get('FCF', 0):,.0f}")
    
#     # 當期與前期資料
#     ci, pi = income_annual['current'], income_annual['previous']
#     cb, pb = balance_annual['current'], balance_annual['previous']
#     cc, pc = cash_annual['current'], cash_annual['previous']
    
#     print("\n💰 年度合計數據（4季加總/平均）：")
#     print(f"  當期年度（t0-t3）營收: {ci.get('revenue', 0):,.0f}")
#     print(f"  前期年度（t4-t7）營收: {pi.get('revenue', 0):,.0f}")
#     print(f"  當期年度（t0-t3）淨利: {ci.get('netIncome', 0):,.0f}")
#     print(f"  前期年度（t4-t7）淨利: {pi.get('netIncome', 0):,.0f}")
#     print(f"  當期年度（t0-t3）總資產(平均): {cb.get('TotalAssets', 0):,.0f}")
#     print(f"  前期年度（t4-t7）總資產(平均): {pb.get('TotalAssets', 0):,.0f}")
#     print(f"  當期年度（t0-t3）OCF: {cc.get('OCF', 0):,.0f}")
#     print(f"  前期年度（t4-t7）OCF: {pc.get('OCF', 0):,.0f}")
    
#     # 計算加權平均股數
#     shares_now = calculate_weighted_avg_shares(df_income)
#     shares_prev = calculate_weighted_avg_shares(df_income.iloc[4:8] if len(df_income) >= 8 else df_income)
    
#     print(f"\n📈 加權平均股數：")
#     print(f"  當期: {shares_now:,.0f} 股" if shares_now and not np.isnan(shares_now) else "  當期: N/A")
#     print(f"  前期: {shares_prev:,.0f} 股" if shares_prev and not np.isnan(shares_prev) else "  前期: N/A")
    
#     # ===== 指標計算 =====
#     # ROA
#     roa_now = safe_divide(ci.get('netIncome', 0), cb.get('TotalAssets', 1))
#     roa_prev = safe_divide(pi.get('netIncome', 0), pb.get('TotalAssets', 1))
    
#     print(f"\n🔢 ROA 計算：")
#     print(f"  當期 ROA = {ci.get('netIncome', 0):,.0f} / {cb.get('TotalAssets', 1):,.0f} = {roa_now:.4f}")
#     print(f"  前期 ROA = {pi.get('netIncome', 0):,.0f} / {pb.get('TotalAssets', 1):,.0f} = {roa_prev:.4f}")
    
#     # 營運現金流
#     ocf_now = cc.get('OCF', 0)
#     ocf_prev = pc.get('OCF', 0)
#     net_income_now = ci.get('netIncome', 0)
#     net_income_prev = pi.get('netIncome', 0)
    
#     print(f"\n💵 現金流品質：")
#     print(f"  當期 OCF: {ocf_now:,.0f}, 淨利: {net_income_now:,.0f}, 品質比: {safe_divide(ocf_now, net_income_now):.4f}")
#     print(f"  前期 OCF: {ocf_prev:,.0f}, 淨利: {net_income_prev:,.0f}, 品質比: {safe_divide(ocf_prev, net_income_prev):.4f}")
    
#     # 流動比率
#     ca_now = cb.get('CurrentAssets', 0)
#     ca_prev = pb.get('CurrentAssets', 0)
#     cl_now = cb.get('CurrentLiabilities', 1)
#     cl_prev = pb.get('CurrentLiabilities', 1)
#     cr_now = safe_divide(ca_now, cl_now)
#     cr_prev = safe_divide(ca_prev, cl_prev)
    
#     print(f"\n📊 流動比率：")
#     print(f"  當期 = {ca_now:,.0f} / {cl_now:,.0f} = {cr_now:.2f}")
#     print(f"  前期 = {ca_prev:,.0f} / {cl_prev:,.0f} = {cr_prev:.2f}")
    
#     # 長期負債比率
#     ltd_now = cb.get('longTermDebt', 0)
#     ltd_prev = pb.get('longTermDebt', 0)
#     ltd_now_ratio = safe_divide(ltd_now, cb.get('TotalAssets', 1))
#     ltd_prev_ratio = safe_divide(ltd_prev, pb.get('TotalAssets', 1))
    
#     print(f"\n🏦 長期負債比率：")
#     print(f"  當期 = {ltd_now:,.0f} / {cb.get('TotalAssets', 1):,.0f} = {ltd_now_ratio:.4f}")
#     print(f"  前期 = {ltd_prev:,.0f} / {pb.get('TotalAssets', 1):,.0f} = {ltd_prev_ratio:.4f}")
    
#     # 營運效率
#     gpm_now = safe_divide(ci.get('grossProfit', 0), ci.get('revenue', 1))
#     gpm_prev = safe_divide(pi.get('grossProfit', 0), pi.get('revenue', 1))
#     ato_now = safe_divide(ci.get('revenue', 0), cb.get('TotalAssets', 1))
#     ato_prev = safe_divide(pi.get('revenue', 0), pb.get('TotalAssets', 1))
    
#     print(f"\n📈 毛利率：")
#     print(f"  當期 = {ci.get('grossProfit', 0):,.0f} / {ci.get('revenue', 1):,.0f} = {gpm_now:.4f}")
#     print(f"  前期 = {pi.get('grossProfit', 0):,.0f} / {pi.get('revenue', 1):,.0f} = {gpm_prev:.4f}")
    
#     print(f"\n🔄 資產周轉率：")
#     print(f"  當期 = {ci.get('revenue', 0):,.0f} / {cb.get('TotalAssets', 1):,.0f} = {ato_now:.4f}")
#     print(f"  前期 = {pi.get('revenue', 0):,.0f} / {pb.get('TotalAssets', 1):,.0f} = {ato_prev:.4f}")
    
#     # ===== 組裝評分 =====
#     score = {'profitability_scores': [], 'leverage_scores': [], 'efficiency_scores': [], 'total_score': 0}
    
#     # 1) 獲利能力（4項）
#     score['profitability_scores'] = [
#         {'name': 'ROA正值', 'score': int(roa_now > 0), 'current': f"{roa_now:.4f}", 
#          'previous': f"{roa_prev:.4f}", 'status': '✓' if roa_now > 0 else '✗'},
#         {'name': '營運現金流正值', 'score': int(ocf_now > 0), 'current': f"${ocf_now:,.0f}", 
#          'previous': f"${ocf_prev:,.0f}", 'status': '✓' if ocf_now > 0 else '✗'},
#         {'name': 'ROA年增', 'score': int(roa_now > roa_prev), 'current': f"{roa_now-roa_prev:.4f}", 
#          'previous': "-", 'status': '✓' if roa_now > roa_prev else '✗'},
#         {'name': '現金流品質（OCF > 淨利）', 'score': int(ocf_now > net_income_now), 
#          'current': f"${ocf_now-net_income_now:,.0f}", 'previous': f"${ocf_prev-net_income_prev:,.0f}", 
#          'status': '✓' if ocf_now > net_income_now else '✗'},
#     ]
    
#     # 2) 槓桿與流動性（3項）
#     score['leverage_scores'] = [
#         {'name': '長期負債比率改善', 'score': int(ltd_now_ratio < ltd_prev_ratio), 
#          'current': f"{ltd_now_ratio:.4f}", 'previous': f"{ltd_prev_ratio:.4f}", 
#          'status': '✓' if ltd_now_ratio < ltd_prev_ratio else '✗'},
#         {'name': '流動比率改善', 'score': int(cr_now > cr_prev), 'current': f"{cr_now:.2f}", 
#          'previous': f"{cr_prev:.2f}", 'status': '✓' if cr_now > cr_prev else '✗'},
#         {'name': '股份未稀釋', 'score': int(shares_now <= shares_prev) if (shares_now and shares_prev and not np.isnan(shares_now) and not np.isnan(shares_prev)) else 0, 
#          'current': f"{shares_now:,.0f}" if shares_now and not np.isnan(shares_now) else "N/A", 
#          'previous': f"{shares_prev:,.0f}" if shares_prev and not np.isnan(shares_prev) else "N/A", 
#          'status': '✓' if (shares_now and shares_prev and not np.isnan(shares_now) and not np.isnan(shares_prev) and shares_now <= shares_prev) else '✗'},
#     ]
    
#     # 3) 營運效率（2項）
#     score['efficiency_scores'] = [
#         {'name': '毛利率改善', 'score': int(gpm_now > gpm_prev), 'current': f"{gpm_now:.4f}", 
#          'previous': f"{gpm_prev:.4f}", 'status': '✓' if gpm_now > gpm_prev else '✗'},
#         {'name': '資產周轉率改善', 'score': int(ato_now > ato_prev), 'current': f"{ato_now:.4f}", 
#          'previous': f"{ato_prev:.4f}", 'status': '✓' if ato_now > ato_prev else '✗'},
#     ]
    
#     # 總分
#     score['total_score'] = sum(
#         item['score']
#         for group in (score['profitability_scores'], score['leverage_scores'], score['efficiency_scores'])
#         for item in group
#     )
    
#     print(f"\n🎯 F-Score 總分: {score['total_score']}/9")
#     print("="*80 + "\n")
    
#     return score


# def calculate_altman_zscore(df_income: pd.DataFrame, df_balance: pd.DataFrame, market_cap: float) -> dict:
#     """
#     計算 Altman Z-Score（台股版）
#     """
#     print("\n" + "="*80)
#     print("📊 Altman Z-Score 計算過程")
#     print("="*80)
    
#     # ⚠️ 確保數據按日期降序排列（最新的在前）
#     if df_income is not None and not df_income.empty:
#         df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
#     if df_balance is not None and not df_balance.empty:
#         df_balance = df_balance.sort_values('date', ascending=False).reset_index(drop=True)
    
#     income_annual = aggregate_quarterly_to_annual(df_income)
#     balance_annual = aggregate_quarterly_to_annual(df_balance)
    
#     if not all([income_annual, balance_annual, market_cap]):
#         return None
    
#     # 打印原始季度數據
#     print("\n📅 最新4季資產負債數據（從早到晚顯示）：")
#     if df_balance is not None and not df_balance.empty and len(df_balance) >= 4:
#         latest_4q = df_balance.iloc[:4].copy()
#         latest_4q = latest_4q.sort_values('date', ascending=True)
#         for idx, row in latest_4q.iterrows():
#             ca = row.get('CurrentAssets', 0)
#             cl = row.get('CurrentLiabilities', 0)
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 流動資產: {ca:,.0f} | 流動負債: {cl:,.0f} | 營運資金: {ca-cl:,.0f}")
    
#     ci = income_annual['current']
#     cb = balance_annual['current']
    
#     print(f"\n💰 市值: {market_cap:,.0f}")
    
#     # 取得必要數據
#     ca = cb.get('CurrentAssets', 0)
#     cl = cb.get('CurrentLiabilities', 0)
#     ta = cb.get('TotalAssets', 1)
#     re = cb.get('retainedEarnings', 0)
#     oi = ci.get('operatingIncome', 0)
#     ie = estimate_interest_expense(df_income)
#     tl = cb.get('Liabilities', 1)
#     rev = ci.get('revenue', 0)
    
#     wc = ca - cl
#     ebit = oi + ie
    
#     print(f"\n📊 基礎數據：")
#     print(f"  營運資金(WC) = 流動資產 - 流動負債 = {ca:,.0f} - {cl:,.0f} = {wc:,.0f}")
#     print(f"  總資產(TA) = {ta:,.0f}")
#     print(f"  保留盈餘(RE) = {re:,.0f}")
#     print(f"  營業利益(OI) = {oi:,.0f}")
#     print(f"  估計利息費用(IE) = {ie:,.0f}")
#     print(f"  EBIT = OI + IE = {oi:,.0f} + {ie:,.0f} = {ebit:,.0f}")
#     print(f"  總負債(TL) = {tl:,.0f}")
#     print(f"  營收(Rev) = {rev:,.0f}")
    
#     # 計算五個組成要素
#     A = safe_divide(wc, ta) * 1.2
#     B = safe_divide(re, ta) * 1.4
#     C = safe_divide(ebit, ta) * 3.3
#     D = safe_divide(market_cap, tl) * 0.6
#     E = safe_divide(rev, ta) * 1.0
    
#     print(f"\n🔢 Z-Score 組成要素：")
#     print(f"  A = (WC/TA) × 1.2 = ({wc:,.0f}/{ta:,.0f}) × 1.2 = {A:.4f}")
#     print(f"  B = (RE/TA) × 1.4 = ({re:,.0f}/{ta:,.0f}) × 1.4 = {B:.4f}")
#     print(f"  C = (EBIT/TA) × 3.3 = ({ebit:,.0f}/{ta:,.0f}) × 3.3 = {C:.4f}")
#     print(f"  D = (MC/TL) × 0.6 = ({market_cap:,.0f}/{tl:,.0f}) × 0.6 = {D:.4f}")
#     print(f"  E = (Rev/TA) × 1.0 = ({rev:,.0f}/{ta:,.0f}) × 1.0 = {E:.4f}")
    
#     z_score = A + B + C + D + E
    
#     print(f"\n🎯 Z-Score = A + B + C + D + E = {A:.4f} + {B:.4f} + {C:.4f} + {D:.4f} + {E:.4f} = {z_score:.4f}")
    
#     # 風險等級
#     if z_score > 2.99:
#         risk_level, risk_emoji = "安全區域", "😊"
#     elif z_score >= 1.81:
#         risk_level, risk_emoji = "灰色區域", "😐"
#     else:
#         risk_level, risk_emoji = "危險區域", "😰"
    
#     print(f"📈 風險等級: {risk_level} {risk_emoji}")
#     print("="*80 + "\n")
    
#     return {
#         'z_score': z_score,
#         'components': {'A': A, 'B': B, 'C': C, 'D': D, 'E': E},
#         'risk_level': risk_level,
#         'risk_emoji': risk_emoji,
#         'base_data': {
#             'working_capital': wc,
#             'total_assets': ta,
#             'retained_earnings': re,
#             'ebit': ebit,
#             'market_cap': market_cap,
#             'total_liabilities': tl,
#             'revenues': rev,
#         }
#     }


# def calculate_dupont_analysis(df_income: pd.DataFrame, df_balance: pd.DataFrame) -> dict:
#     """
#     杜邦分析（台股版）
#     分析最近3年（12季）的ROE三因子
#     """
#     print("\n" + "="*80)
#     print("📊 杜邦分析計算過程")
#     print("="*80)
    
#     if df_income is None or df_income.empty or df_balance is None or df_balance.empty:
#         return None
    
#     # ⚠️ 確保數據按日期降序排列（最新的在前）
#     df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
#     df_balance = df_balance.sort_values('date', ascending=False).reset_index(drop=True)
    
#     if len(df_income) < 12 or len(df_balance) < 12:
#         print(f"⚠️ 數據不足：損益表 {len(df_income)} 季，資產負債表 {len(df_balance)} 季（需要至少12季）")
#         return None
    
#     results = []
    
#     # 計算最近3年（每年4季）
#     for year_idx in range(3):
#         start_idx = year_idx * 4
#         end_idx = start_idx + 4
        
#         print(f"\n📅 第 {year_idx + 1} 年分析（索引 {start_idx}-{end_idx-1}，即 t{start_idx}-t{end_idx-1}）:")
        
#         # 打印該年度4季數據（從早到晚）
#         print(f"  損益表 4季數據（從早到晚顯示）：")
#         df_sorted = df_income.iloc[start_idx:end_idx].copy().sort_values('date', ascending=True)
#         for idx, row in df_sorted.iterrows():
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"    {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 營收: {row.get('revenue', 0):,.0f} | 淨利: {row.get('netIncome', 0):,.0f}")
        
#         print(f"  資產負債表 4季數據（從早到晚顯示）：")
#         df_sorted = df_balance.iloc[start_idx:end_idx].copy().sort_values('date', ascending=True)
#         for idx, row in df_sorted.iterrows():
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"    {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 總資產: {row.get('TotalAssets', 0):,.0f} | 權益: {row.get('Equity', 0):,.0f}")
        
#         income_data = aggregate_quarterly_to_annual(df_income.iloc[start_idx:end_idx + 4], periods_latest=4, periods_previous=4)
#         balance_data = aggregate_quarterly_to_annual(df_balance.iloc[start_idx:end_idx + 4], periods_latest=4, periods_previous=4)
        
#         if not income_data or not balance_data:
#             continue
        
#         ci = income_data['current']
#         cb = balance_data['current']
        
#         net = ci.get('netIncome', 0)
#         rev = ci.get('revenue', 1)
#         ta = cb.get('TotalAssets', 1)
#         eq = cb.get('Equity', 1)
        
#         nm = safe_divide(net, rev)  # 淨利率
#         at = safe_divide(rev, ta)   # 資產週轉率
#         em = safe_divide(ta, eq)    # 權益乘數
#         roe = safe_divide(net, eq)
        
#         print(f"\n  💰 年度合計/平均：")
#         print(f"    淨利: {net:,.0f}")
#         print(f"    營收: {rev:,.0f}")
#         print(f"    總資產(平均): {ta:,.0f}")
#         print(f"    權益(平均): {eq:,.0f}")
        
#         print(f"\n  🔢 ROE三因子：")
#         print(f"    淨利率(NM) = 淨利/營收 = {net:,.0f}/{rev:,.0f} = {nm:.4f}")
#         print(f"    資產週轉率(AT) = 營收/總資產 = {rev:,.0f}/{ta:,.0f} = {at:.4f}")
#         print(f"    權益乘數(EM) = 總資產/權益 = {ta:,.0f}/{eq:,.0f} = {em:.4f}")
#         print(f"    ROE = NM × AT × EM = {nm:.4f} × {at:.4f} × {em:.4f} = {nm*at*em:.4f}")
#         print(f"    直接ROE = 淨利/權益 = {net:,.0f}/{eq:,.0f} = {roe:.4f}")
        
#         # 取最新一季的日期作為年度標記
#         date_label = df_income.iloc[start_idx].get('date', '')
        
#         results.append({
#             'date': date_label,
#             'net_margin': nm,
#             'asset_turnover': at,
#             'equity_multiplier': em,
#             'direct_roe': roe
#         })
    
#     # 計算變化
#     changes = None
#     if len(results) >= 2:
#         changes = {
#             'net_margin_change': results[0]['net_margin'] - results[1]['net_margin'],
#             'asset_turnover_change': results[0]['asset_turnover'] - results[1]['asset_turnover'],
#             'equity_multiplier_change': results[0]['equity_multiplier'] - results[1]['equity_multiplier'],
#             'roe_change': results[0]['direct_roe'] - results[1]['direct_roe'],
#         }
        
#         print(f"\n📈 年度變化（最新年 vs 前一年）：")
#         print(f"  淨利率變化: {changes['net_margin_change']:+.4f}")
#         print(f"  資產週轉率變化: {changes['asset_turnover_change']:+.4f}")
#         print(f"  權益乘數變化: {changes['equity_multiplier_change']:+.4f}")
#         print(f"  ROE變化: {changes['roe_change']:+.4f}")
    
#     print("="*80 + "\n")
    
#     return {'yearly_analysis': results, 'changes': changes}


# def calculate_cashflow_analysis(df_income: pd.DataFrame, df_cash: pd.DataFrame) -> dict:
#     """
#     現金流分析（台股版）
#     """
#     print("\n" + "="*80)
#     print("📊 現金流分析計算過程")
#     print("="*80)
    
#     # ⚠️ 確保數據按日期降序排列（最新的在前）
#     if df_income is not None and not df_income.empty:
#         df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
#     if df_cash is not None and not df_cash.empty:
#         df_cash = df_cash.sort_values('date', ascending=False).reset_index(drop=True)
    
#     income_annual = aggregate_quarterly_to_annual(df_income)
#     cash_annual = aggregate_quarterly_to_annual(df_cash)
    
#     if not all([income_annual, cash_annual]):
#         return None
    
#     # 打印原始季度數據（從早到晚）
#     print("\n📅 最新4季現金流數據（從早到晚顯示）：")
#     if df_cash is not None and not df_cash.empty and len(df_cash) >= 4:
#         latest_4q = df_cash.iloc[:4].copy()
#         latest_4q = latest_4q.sort_values('date', ascending=True)
#         for idx, row in latest_4q.iterrows():
#             ocf = row.get('OCF', 0)
#             capex = row.get('CapEx', 0)
#             fcf = row.get('FCF', 0)
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | OCF: {ocf:,.0f} | CapEx: {capex:,.0f} | FCF: {fcf:,.0f}")
    
#     print("\n📅 最新4季淨利數據（從早到晚顯示）：")
#     if df_income is not None and not df_income.empty and len(df_income) >= 4:
#         latest_4q = df_income.iloc[:4].copy()
#         latest_4q = latest_4q.sort_values('date', ascending=True)
#         for idx, row in latest_4q.iterrows():
#             q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
#             print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 淨利: {row.get('netIncome', 0):,.0f}")
    
#     ci = income_annual['current']
#     cc = cash_annual['current']
    
#     ocf = cc.get('OCF', 0)
#     cfi = cc.get('CFI', 0)
#     cff = cc.get('CFF', 0)
#     net = ci.get('netIncome', 1)
#     capex = cc.get('CapEx', 0)
    
#     print(f"\n💰 年度合計數據（4季加總）：")
#     print(f"  營運現金流(OCF): {ocf:,.0f}")
#     print(f"  投資現金流(CFI): {cfi:,.0f}")
#     print(f"  融資現金流(CFF): {cff:,.0f}")
#     print(f"  淨利: {net:,.0f}")
#     print(f"  資本支出(CapEx): {capex:,.0f}")
    
#     # 現金流品質比率
#     ocf_quality = safe_divide(ocf, net)
    
#     print(f"\n🔢 現金流品質比率：")
#     print(f"  OCF品質 = OCF/淨利 = {ocf:,.0f}/{net:,.0f} = {ocf_quality:.4f}")
    
#     # 品質評估
#     if ocf_quality >= 1.2:
#         q, emoji = "優秀", "😊"
#     elif ocf_quality >= 1.0:
#         q, emoji = "良好", "🙂"
#     elif ocf_quality >= 0.8:
#         q, emoji = "尚可", "😐"
#     else:
#         q, emoji = "需關注", "😰"
    
#     print(f"  評估: {q} {emoji}")
    
#     # 自由現金流（使用絕對值確保 CapEx 為正）
#     free_cashflow = ocf - abs(capex)
    
#     print(f"\n💵 自由現金流：")
#     print(f"  FCF = OCF - |CapEx| = {ocf:,.0f} - {abs(capex):,.0f} = {free_cashflow:,.0f}")
    
#     total_cf = ocf + cfi + cff
    
#     print(f"\n📊 現金流結構：")
#     print(f"  營運現金流: {ocf:,.0f} ({safe_divide(ocf, total_cf)*100:.1f}%)" if total_cf != 0 else f"  營運現金流: {ocf:,.0f}")
#     print(f"  投資現金流: {cfi:,.0f} ({safe_divide(cfi, total_cf)*100:.1f}%)" if total_cf != 0 else f"  投資現金流: {cfi:,.0f}")
#     print(f"  融資現金流: {cff:,.0f} ({safe_divide(cff, total_cf)*100:.1f}%)" if total_cf != 0 else f"  融資現金流: {cff:,.0f}")
#     print(f"  總現金流: {total_cf:,.0f}")
    
#     print("="*80 + "\n")
    
#     return {
#         'ocf_quality': ocf_quality,
#         'free_cashflow': free_cashflow,
#         'quality_assessment': q,
#         'quality_emoji': emoji,
#         'structure': {
#             'operating': ocf,
#             'investing': cfi,
#             'financing': cff,
#             'total': total_cf
#         }
#     }


# ==================== 四階段財報分析計算（完整打印版）====================

def calculate_piotroski_fscore(df_income: pd.DataFrame, df_balance: pd.DataFrame, df_cash: pd.DataFrame) -> dict:
    """
    計算 Piotroski F-Score（台股版）
    使用最新4季 vs 前4季的年度比較
    """
    print("\n" + "="*80)
    print("📊 Piotroski F-Score 計算過程")
    print("="*80)
    
    # ⚠️ 確保數據按日期降序排列（最新的在前，索引0是最新的季度）
    if df_income is not None and not df_income.empty:
        df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
    if df_balance is not None and not df_balance.empty:
        df_balance = df_balance.sort_values('date', ascending=False).reset_index(drop=True)
    if df_cash is not None and not df_cash.empty:
        df_cash = df_cash.sort_values('date', ascending=False).reset_index(drop=True)
    
    print(f"\n🔍 數據範圍檢查：")
    if df_income is not None and not df_income.empty:
        print(f"  損益表: {len(df_income)} 季，最新: {df_income.iloc[0]['date'].strftime('%Y-%m-%d')}, 最舊: {df_income.iloc[-1]['date'].strftime('%Y-%m-%d')}")
    if df_balance is not None and not df_balance.empty:
        print(f"  資產負債表: {len(df_balance)} 季，最新: {df_balance.iloc[0]['date'].strftime('%Y-%m-%d')}, 最舊: {df_balance.iloc[-1]['date'].strftime('%Y-%m-%d')}")
    if df_cash is not None and not df_cash.empty:
        print(f"  現金流量表: {len(df_cash)} 季，最新: {df_cash.iloc[0]['date'].strftime('%Y-%m-%d')}, 最舊: {df_cash.iloc[-1]['date'].strftime('%Y-%m-%d')}")
    
    # 合併季報為年度
    income_annual = aggregate_quarterly_to_annual(df_income)
    balance_annual = aggregate_quarterly_to_annual(df_balance)
    cash_annual = aggregate_quarterly_to_annual(df_cash)
    
    if not all([income_annual, balance_annual, cash_annual]):
        return None
    
    # 打印原始季度數據（最新4季，從早到晚顯示）
    print("\n📅 損益表 - 最新4季（t0-t3）數據（從早到晚顯示）：")
    if df_income is not None and not df_income.empty and len(df_income) >= 4:
        latest_4q = df_income.iloc[:4].copy()
        latest_4q = latest_4q.sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 營收: {row.get('revenue', 0):,.0f} | 淨利: {row.get('netIncome', 0):,.0f}")
    
    print("\n📅 損益表 - 前4季（t4-t7）數據（從早到晚顯示）：")
    if df_income is not None and len(df_income) >= 8:
        prev_4q = df_income.iloc[4:8].copy()
        prev_4q = prev_4q.sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 營收: {row.get('revenue', 0):,.0f} | 淨利: {row.get('netIncome', 0):,.0f}")
    
    print("\n📅 資產負債表 - 最新4季（t0-t3）數據（從早到晚顯示）：")
    if df_balance is not None and not df_balance.empty and len(df_balance) >= 4:
        latest_4q = df_balance.iloc[:4].copy()
        latest_4q = latest_4q.sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 總資產: {row.get('TotalAssets', 0):,.0f} | 股東權益: {row.get('Equity', 0):,.0f}")
    
    print("\n📅 資產負債表 - 前4季（t4-t7）數據（從早到晚顯示）：")
    if df_balance is not None and len(df_balance) >= 8:
        prev_4q = df_balance.iloc[4:8].copy()
        prev_4q = prev_4q.sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 總資產: {row.get('TotalAssets', 0):,.0f} | 股東權益: {row.get('Equity', 0):,.0f}")
    
    print("\n📅 現金流量表 - 最新4季（t0-t3）數據（從早到晚顯示）：")
    if df_cash is not None and not df_cash.empty and len(df_cash) >= 4:
        latest_4q = df_cash.iloc[:4].copy()
        latest_4q = latest_4q.sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | OCF: {row.get('OCF', 0):,.0f} | FCF: {row.get('FCF', 0):,.0f}")
    
    print("\n📅 現金流量表 - 前4季（t4-t7）數據（從早到晚顯示）：")
    if df_cash is not None and len(df_cash) >= 8:
        prev_4q = df_cash.iloc[4:8].copy()
        prev_4q = prev_4q.sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | OCF: {row.get('OCF', 0):,.0f} | FCF: {row.get('FCF', 0):,.0f}")
    
    # 當期與前期資料
    ci, pi = income_annual['current'], income_annual['previous']
    cb, pb = balance_annual['current'], balance_annual['previous']
    cc, pc = cash_annual['current'], cash_annual['previous']
    
    print("\n💰 年度合計數據（4季加總/平均）：")
    print(f"  當期年度（t0-t3）營收: {ci.get('revenue', 0):,.0f}")
    print(f"  前期年度（t4-t7）營收: {pi.get('revenue', 0):,.0f}")
    print(f"  當期年度（t0-t3）淨利: {ci.get('netIncome', 0):,.0f}")
    print(f"  前期年度（t4-t7）淨利: {pi.get('netIncome', 0):,.0f}")
    print(f"  當期年度（t0-t3）總資產(平均): {cb.get('TotalAssets', 0):,.0f}")
    print(f"  前期年度（t4-t7）總資產(平均): {pb.get('TotalAssets', 0):,.0f}")
    print(f"  當期年度（t0-t3）OCF: {cc.get('OCF', 0):,.0f}")
    print(f"  前期年度（t4-t7）OCF: {pc.get('OCF', 0):,.0f}")
    
    # 計算加權平均股數
    shares_now = calculate_weighted_avg_shares(df_income)
    shares_prev = calculate_weighted_avg_shares(df_income.iloc[4:8] if len(df_income) >= 8 else df_income)
    
    print(f"\n📈 加權平均股數：")
    print(f"  當期: {shares_now:,.0f} 股" if shares_now and not np.isnan(shares_now) else "  當期: N/A")
    print(f"  前期: {shares_prev:,.0f} 股" if shares_prev and not np.isnan(shares_prev) else "  前期: N/A")
    
    # ===== 指標計算 =====
    
    # 1. ROA 計算
    print("\n" + "="*80)
    print("📊 指標 1: ROA（資產報酬率）")
    print("="*80)
    
    print("\n📋 最新4季數據：")
    if df_income is not None and df_balance is not None and len(df_income) >= 4 and len(df_balance) >= 4:
        latest_4q_income = df_income.iloc[:4].copy().sort_values('date', ascending=True)
        latest_4q_balance = df_balance.iloc[:4].copy().sort_values('date', ascending=True)
        for i, (idx_i, row_i) in enumerate(latest_4q_income.iterrows()):
            row_b = latest_4q_balance.iloc[i]
            q_label = row_i.get('quarter_label', f"{row_i['date'].year}-Q{row_i['date'].quarter}")
            print(f"  {q_label}: 淨利 {row_i.get('netIncome', 0):,.0f} | 總資產 {row_b.get('TotalAssets', 0):,.0f}")
    
    print("\n📋 前4季數據：")
    if df_income is not None and df_balance is not None and len(df_income) >= 8 and len(df_balance) >= 8:
        prev_4q_income = df_income.iloc[4:8].copy().sort_values('date', ascending=True)
        prev_4q_balance = df_balance.iloc[4:8].copy().sort_values('date', ascending=True)
        for i, (idx_i, row_i) in enumerate(prev_4q_income.iterrows()):
            row_b = prev_4q_balance.iloc[i]
            q_label = row_i.get('quarter_label', f"{row_i['date'].year}-Q{row_i['date'].quarter}")
            print(f"  {q_label}: 淨利 {row_i.get('netIncome', 0):,.0f} | 總資產 {row_b.get('TotalAssets', 0):,.0f}")
    
    roa_now = safe_divide(ci.get('netIncome', 0), cb.get('TotalAssets', 1))
    roa_prev = safe_divide(pi.get('netIncome', 0), pb.get('TotalAssets', 1))
    
    print(f"\n🔢 ROA 計算：")
    print(f"  當期 ROA = 淨利(4季加總) / 總資產(4季平均)")
    print(f"           = {ci.get('netIncome', 0):,.0f} / {cb.get('TotalAssets', 1):,.0f} = {roa_now:.4f}")
    print(f"  前期 ROA = {pi.get('netIncome', 0):,.0f} / {pb.get('TotalAssets', 1):,.0f} = {roa_prev:.4f}")
    print(f"  ✓ ROA 正值: {'是' if roa_now > 0 else '否'}")
    print(f"  ✓ ROA 年增: {'是' if roa_now > roa_prev else '否'} (變化: {roa_now-roa_prev:+.4f})")
    
    # 2. 營運現金流品質
    print("\n" + "="*80)
    print("📊 指標 2: 營運現金流品質")
    print("="*80)
    
    print("\n📋 最新4季數據：")
    if df_income is not None and df_cash is not None and len(df_income) >= 4 and len(df_cash) >= 4:
        latest_4q_income = df_income.iloc[:4].copy().sort_values('date', ascending=True)
        latest_4q_cash = df_cash.iloc[:4].copy().sort_values('date', ascending=True)
        for i, (idx_i, row_i) in enumerate(latest_4q_income.iterrows()):
            row_c = latest_4q_cash.iloc[i]
            q_label = row_i.get('quarter_label', f"{row_i['date'].year}-Q{row_i['date'].quarter}")
            ocf = row_c.get('OCF', 0)
            net = row_i.get('netIncome', 0)
            quality = safe_divide(ocf, net)
            print(f"  {q_label}: OCF {ocf:,.0f} | 淨利 {net:,.0f} | 品質比 {quality:.4f}")
    
    print("\n📋 前4季數據：")
    if df_income is not None and df_cash is not None and len(df_income) >= 8 and len(df_cash) >= 8:
        prev_4q_income = df_income.iloc[4:8].copy().sort_values('date', ascending=True)
        prev_4q_cash = df_cash.iloc[4:8].copy().sort_values('date', ascending=True)
        for i, (idx_i, row_i) in enumerate(prev_4q_income.iterrows()):
            row_c = prev_4q_cash.iloc[i]
            q_label = row_i.get('quarter_label', f"{row_i['date'].year}-Q{row_i['date'].quarter}")
            ocf = row_c.get('OCF', 0)
            net = row_i.get('netIncome', 0)
            quality = safe_divide(ocf, net)
            print(f"  {q_label}: OCF {ocf:,.0f} | 淨利 {net:,.0f} | 品質比 {quality:.4f}")
    
    ocf_now = cc.get('OCF', 0)
    ocf_prev = pc.get('OCF', 0)
    net_income_now = ci.get('netIncome', 0)
    net_income_prev = pi.get('netIncome', 0)
    
    print(f"\n🔢 現金流品質計算：")
    print(f"  當期: OCF {ocf_now:,.0f} | 淨利 {net_income_now:,.0f} | 品質比 {safe_divide(ocf_now, net_income_now):.4f}")
    print(f"  前期: OCF {ocf_prev:,.0f} | 淨利 {net_income_prev:,.0f} | 品質比 {safe_divide(ocf_prev, net_income_prev):.4f}")
    print(f"  ✓ OCF 正值: {'是' if ocf_now > 0 else '否'}")
    print(f"  ✓ OCF > 淨利: {'是' if ocf_now > net_income_now else '否'}")
    
    # 3. 流動比率
    print("\n" + "="*80)
    print("📊 指標 3: 流動比率")
    print("="*80)
    
    print("\n📋 最新4季數據：")
    if df_balance is not None and len(df_balance) >= 4:
        latest_4q = df_balance.iloc[:4].copy().sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            ca = row.get('CurrentAssets', 0)
            cl = row.get('CurrentLiabilities', 1)
            cr = safe_divide(ca, cl)
            print(f"  {q_label}: 流動資產 {ca:,.0f} | 流動負債 {cl:,.0f} | 流動比率 {cr:.2f}")
    
    print("\n📋 前4季數據：")
    if df_balance is not None and len(df_balance) >= 8:
        prev_4q = df_balance.iloc[4:8].copy().sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            ca = row.get('CurrentAssets', 0)
            cl = row.get('CurrentLiabilities', 1)
            cr = safe_divide(ca, cl)
            print(f"  {q_label}: 流動資產 {ca:,.0f} | 流動負債 {cl:,.0f} | 流動比率 {cr:.2f}")
    
    ca_now = cb.get('CurrentAssets', 0)
    ca_prev = pb.get('CurrentAssets', 0)
    cl_now = cb.get('CurrentLiabilities', 1)
    cl_prev = pb.get('CurrentLiabilities', 1)
    cr_now = safe_divide(ca_now, cl_now)
    cr_prev = safe_divide(ca_prev, cl_prev)
    
    print(f"\n🔢 流動比率計算（平均）：")
    print(f"  當期 = {ca_now:,.0f} / {cl_now:,.0f} = {cr_now:.2f}")
    print(f"  前期 = {ca_prev:,.0f} / {cl_prev:,.0f} = {cr_prev:.2f}")
    print(f"  ✓ 流動比率改善: {'是' if cr_now > cr_prev else '否'} (變化: {cr_now-cr_prev:+.2f})")
    
    # 4. 長期負債比率
    print("\n" + "="*80)
    print("📊 指標 4: 長期負債比率")
    print("="*80)
    
    print("\n📋 最新4季數據：")
    if df_balance is not None and len(df_balance) >= 4:
        latest_4q = df_balance.iloc[:4].copy().sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            ltd = row.get('longTermDebt', 0)
            ta = row.get('TotalAssets', 1)
            ratio = safe_divide(ltd, ta)
            print(f"  {q_label}: 長期負債 {ltd:,.0f} | 總資產 {ta:,.0f} | 比率 {ratio:.4f}")
    
    print("\n📋 前4季數據：")
    if df_balance is not None and len(df_balance) >= 8:
        prev_4q = df_balance.iloc[4:8].copy().sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            ltd = row.get('longTermDebt', 0)
            ta = row.get('TotalAssets', 1)
            ratio = safe_divide(ltd, ta)
            print(f"  {q_label}: 長期負債 {ltd:,.0f} | 總資產 {ta:,.0f} | 比率 {ratio:.4f}")
    
    ltd_now = cb.get('longTermDebt', 0)
    ltd_prev = pb.get('longTermDebt', 0)
    ltd_now_ratio = safe_divide(ltd_now, cb.get('TotalAssets', 1))
    ltd_prev_ratio = safe_divide(ltd_prev, pb.get('TotalAssets', 1))
    
    print(f"\n🔢 長期負債比率計算（平均）：")
    print(f"  當期 = {ltd_now:,.0f} / {cb.get('TotalAssets', 1):,.0f} = {ltd_now_ratio:.4f}")
    print(f"  前期 = {ltd_prev:,.0f} / {pb.get('TotalAssets', 1):,.0f} = {ltd_prev_ratio:.4f}")
    print(f"  ✓ 長期負債比率改善: {'是' if ltd_now_ratio < ltd_prev_ratio else '否'} (變化: {ltd_now_ratio-ltd_prev_ratio:+.4f})")
    
    # 5. 毛利率
    print("\n" + "="*80)
    print("📊 指標 5: 毛利率")
    print("="*80)
    
    print("\n📋 最新4季數據：")
    if df_income is not None and len(df_income) >= 4:
        latest_4q = df_income.iloc[:4].copy().sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            gp = row.get('grossProfit', 0)
            rev = row.get('revenue', 1)
            gpm = safe_divide(gp, rev)
            print(f"  {q_label}: 毛利 {gp:,.0f} | 營收 {rev:,.0f} | 毛利率 {gpm:.4f} ({gpm*100:.2f}%)")
    
    print("\n📋 前4季數據：")
    if df_income is not None and len(df_income) >= 8:
        prev_4q = df_income.iloc[4:8].copy().sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            gp = row.get('grossProfit', 0)
            rev = row.get('revenue', 1)
            gpm = safe_divide(gp, rev)
            print(f"  {q_label}: 毛利 {gp:,.0f} | 營收 {rev:,.0f} | 毛利率 {gpm:.4f} ({gpm*100:.2f}%)")
    
    gpm_now = safe_divide(ci.get('grossProfit', 0), ci.get('revenue', 1))
    gpm_prev = safe_divide(pi.get('grossProfit', 0), pi.get('revenue', 1))
    
    print(f"\n🔢 毛利率計算（年度）：")
    print(f"  當期 = {ci.get('grossProfit', 0):,.0f} / {ci.get('revenue', 1):,.0f} = {gpm_now:.4f} ({gpm_now*100:.2f}%)")
    print(f"  前期 = {pi.get('grossProfit', 0):,.0f} / {pi.get('revenue', 1):,.0f} = {gpm_prev:.4f} ({gpm_prev*100:.2f}%)")
    print(f"  ✓ 毛利率改善: {'是' if gpm_now > gpm_prev else '否'} (變化: {(gpm_now-gpm_prev)*100:+.2f}個百分點)")
    
    # 6. 資產周轉率
    print("\n" + "="*80)
    print("📊 指標 6: 資產周轉率")
    print("="*80)
    
    print("\n📋 最新4季數據：")
    if df_income is not None and df_balance is not None and len(df_income) >= 4 and len(df_balance) >= 4:
        latest_4q_income = df_income.iloc[:4].copy().sort_values('date', ascending=True)
        latest_4q_balance = df_balance.iloc[:4].copy().sort_values('date', ascending=True)
        for i, (idx_i, row_i) in enumerate(latest_4q_income.iterrows()):
            row_b = latest_4q_balance.iloc[i]
            q_label = row_i.get('quarter_label', f"{row_i['date'].year}-Q{row_i['date'].quarter}")
            rev = row_i.get('revenue', 0)
            ta = row_b.get('TotalAssets', 1)
            ato = safe_divide(rev, ta)
            print(f"  {q_label}: 營收 {rev:,.0f} | 總資產 {ta:,.0f} | 週轉率 {ato:.4f}")
    
    print("\n📋 前4季數據：")
    if df_income is not None and df_balance is not None and len(df_income) >= 8 and len(df_balance) >= 8:
        prev_4q_income = df_income.iloc[4:8].copy().sort_values('date', ascending=True)
        prev_4q_balance = df_balance.iloc[4:8].copy().sort_values('date', ascending=True)
        for i, (idx_i, row_i) in enumerate(prev_4q_income.iterrows()):
            row_b = prev_4q_balance.iloc[i]
            q_label = row_i.get('quarter_label', f"{row_i['date'].year}-Q{row_i['date'].quarter}")
            rev = row_i.get('revenue', 0)
            ta = row_b.get('TotalAssets', 1)
            ato = safe_divide(rev, ta)
            print(f"  {q_label}: 營收 {rev:,.0f} | 總資產 {ta:,.0f} | 週轉率 {ato:.4f}")
    
    ato_now = safe_divide(ci.get('revenue', 0), cb.get('TotalAssets', 1))
    ato_prev = safe_divide(pi.get('revenue', 0), pb.get('TotalAssets', 1))
    
    print(f"\n🔢 資產周轉率計算（年度）：")
    print(f"  當期 = {ci.get('revenue', 0):,.0f} / {cb.get('TotalAssets', 1):,.0f} = {ato_now:.4f}")
    print(f"  前期 = {pi.get('revenue', 0):,.0f} / {pb.get('TotalAssets', 1):,.0f} = {ato_prev:.4f}")
    print(f"  ✓ 資產周轉率改善: {'是' if ato_now > ato_prev else '否'} (變化: {ato_now-ato_prev:+.4f})")
    
    # ===== 組裝評分 =====
    score = {'profitability_scores': [], 'leverage_scores': [], 'efficiency_scores': [], 'total_score': 0}
    
    # 1) 獲利能力（4項）
    score['profitability_scores'] = [
        {'name': 'ROA正值', 'score': int(roa_now > 0), 'current': f"{roa_now:.4f}", 
         'previous': f"{roa_prev:.4f}", 'status': '✓' if roa_now > 0 else '✗'},
        {'name': '營運現金流正值', 'score': int(ocf_now > 0), 'current': f"${ocf_now:,.0f}", 
         'previous': f"${ocf_prev:,.0f}", 'status': '✓' if ocf_now > 0 else '✗'},
        {'name': 'ROA年增', 'score': int(roa_now > roa_prev), 'current': f"{roa_now-roa_prev:.4f}", 
         'previous': "-", 'status': '✓' if roa_now > roa_prev else '✗'},
        {'name': '現金流品質（OCF > 淨利）', 'score': int(ocf_now > net_income_now), 
         'current': f"${ocf_now-net_income_now:,.0f}", 'previous': f"${ocf_prev-net_income_prev:,.0f}", 
         'status': '✓' if ocf_now > net_income_now else '✗'},
    ]
    
    # 2) 槓桿與流動性（3項）
    score['leverage_scores'] = [
        {'name': '長期負債比率改善', 'score': int(ltd_now_ratio < ltd_prev_ratio), 
         'current': f"{ltd_now_ratio:.4f}", 'previous': f"{ltd_prev_ratio:.4f}", 
         'status': '✓' if ltd_now_ratio < ltd_prev_ratio else '✗'},
        {'name': '流動比率改善', 'score': int(cr_now > cr_prev), 'current': f"{cr_now:.2f}", 
         'previous': f"{cr_prev:.2f}", 'status': '✓' if cr_now > cr_prev else '✗'},
        {'name': '股份未稀釋', 'score': int(shares_now <= shares_prev) if (shares_now and shares_prev and not np.isnan(shares_now) and not np.isnan(shares_prev)) else 0, 
         'current': f"{shares_now:,.0f}" if shares_now and not np.isnan(shares_now) else "N/A", 
         'previous': f"{shares_prev:,.0f}" if shares_prev and not np.isnan(shares_prev) else "N/A", 
         'status': '✓' if (shares_now and shares_prev and not np.isnan(shares_now) and not np.isnan(shares_prev) and shares_now <= shares_prev) else '✗'},
    ]
    
    # 3) 營運效率（2項）
    score['efficiency_scores'] = [
        {'name': '毛利率改善', 'score': int(gpm_now > gpm_prev), 'current': f"{gpm_now:.4f}", 
         'previous': f"{gpm_prev:.4f}", 'status': '✓' if gpm_now > gpm_prev else '✗'},
        {'name': '資產周轉率改善', 'score': int(ato_now > ato_prev), 'current': f"{ato_now:.4f}", 
         'previous': f"{ato_prev:.4f}", 'status': '✓' if ato_now > ato_prev else '✗'},
    ]
    
    # 總分
    score['total_score'] = sum(
        item['score']
        for group in (score['profitability_scores'], score['leverage_scores'], score['efficiency_scores'])
        for item in group
    )
    
    print("\n" + "="*80)
    print(f"🎯 F-Score 總分: {score['total_score']}/9")
    print("="*80 + "\n")
    
    return score


def calculate_altman_zscore(df_income: pd.DataFrame, df_balance: pd.DataFrame, market_cap: float) -> dict:
    """
    計算 Altman Z-Score（台股版）
    """
    print("\n" + "="*80)
    print("📊 Altman Z-Score 計算過程")
    print("="*80)
    
    # ⚠️ 確保數據按日期降序排列（最新的在前）
    if df_income is not None and not df_income.empty:
        df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
    if df_balance is not None and not df_balance.empty:
        df_balance = df_balance.sort_values('date', ascending=False).reset_index(drop=True)
    
    income_annual = aggregate_quarterly_to_annual(df_income)
    balance_annual = aggregate_quarterly_to_annual(df_balance)
    
    if not all([income_annual, balance_annual, market_cap]):
        return None
    
    # 打印原始季度數據
    print("\n📅 最新4季資產負債數據（從早到晚顯示）：")
    if df_balance is not None and not df_balance.empty and len(df_balance) >= 4:
        latest_4q = df_balance.iloc[:4].copy()
        latest_4q = latest_4q.sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            ca = row.get('CurrentAssets', 0)
            cl = row.get('CurrentLiabilities', 0)
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 流動資產: {ca:,.0f} | 流動負債: {cl:,.0f} | 營運資金: {ca-cl:,.0f}")
    
    print("\n📅 前4季資產負債數據（從早到晚顯示）：")
    if df_balance is not None and len(df_balance) >= 8:
        prev_4q = df_balance.iloc[4:8].copy()
        prev_4q = prev_4q.sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            ca = row.get('CurrentAssets', 0)
            cl = row.get('CurrentLiabilities', 0)
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 流動資產: {ca:,.0f} | 流動負債: {cl:,.0f} | 營運資金: {ca-cl:,.0f}")
    
    ci = income_annual['current']
    cb = balance_annual['current']
    
    print(f"\n💰 市值: {market_cap:,.0f}")
    
    # 取得必要數據
    ca = cb.get('CurrentAssets', 0)
    cl = cb.get('CurrentLiabilities', 0)
    ta = cb.get('TotalAssets', 1)
    re = cb.get('retainedEarnings', 0)
    oi = ci.get('operatingIncome', 0)
    ie = estimate_interest_expense(df_income)
    tl = cb.get('Liabilities', 1)
    rev = ci.get('revenue', 0)
    
    wc = ca - cl
    ebit = oi + ie
    
    print(f"\n📊 基礎數據：")
    print(f"  營運資金(WC) = 流動資產 - 流動負債 = {ca:,.0f} - {cl:,.0f} = {wc:,.0f}")
    print(f"  總資產(TA) = {ta:,.0f}")
    print(f"  保留盈餘(RE) = {re:,.0f}")
    print(f"  營業利益(OI) = {oi:,.0f}")
    print(f"  估計利息費用(IE) = {ie:,.0f}")
    print(f"  EBIT = OI + IE = {oi:,.0f} + {ie:,.0f} = {ebit:,.0f}")
    print(f"  總負債(TL) = {tl:,.0f}")
    print(f"  營收(Rev) = {rev:,.0f}")
    
    # 計算五個組成要素
    A = safe_divide(wc, ta) * 1.2
    B = safe_divide(re, ta) * 1.4
    C = safe_divide(ebit, ta) * 3.3
    D = safe_divide(market_cap, tl) * 0.6
    E = safe_divide(rev, ta) * 1.0
    
    print(f"\n🔢 Z-Score 組成要素：")
    print(f"  A = (WC/TA) × 1.2 = ({wc:,.0f}/{ta:,.0f}) × 1.2 = {A:.4f}")
    print(f"  B = (RE/TA) × 1.4 = ({re:,.0f}/{ta:,.0f}) × 1.4 = {B:.4f}")
    print(f"  C = (EBIT/TA) × 3.3 = ({ebit:,.0f}/{ta:,.0f}) × 3.3 = {C:.4f}")
    print(f"  D = (MC/TL) × 0.6 = ({market_cap:,.0f}/{tl:,.0f}) × 0.6 = {D:.4f}")
    print(f"  E = (Rev/TA) × 1.0 = ({rev:,.0f}/{ta:,.0f}) × 1.0 = {E:.4f}")
    
    z_score = A + B + C + D + E
    
    print(f"\n🎯 Z-Score = A + B + C + D + E = {A:.4f} + {B:.4f} + {C:.4f} + {D:.4f} + {E:.4f} = {z_score:.4f}")
    
    # 風險等級
    if z_score > 2.99:
        risk_level, risk_emoji = "安全區域", "😊"
    elif z_score >= 1.81:
        risk_level, risk_emoji = "灰色區域", "😐"
    else:
        risk_level, risk_emoji = "危險區域", "😰"
    
    print(f"📈 風險等級: {risk_level} {risk_emoji}")
    print("="*80 + "\n")
    
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


def calculate_dupont_analysis(df_income: pd.DataFrame, df_balance: pd.DataFrame) -> dict:
    """
    杜邦分析（台股版）
    分析最近3年（12季）的ROE三因子
    """
    print("\n" + "="*80)
    print("📊 杜邦分析計算過程")
    print("="*80)
    
    if df_income is None or df_income.empty or df_balance is None or df_balance.empty:
        return None
    
    # ⚠️ 確保數據按日期降序排列（最新的在前）
    df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
    df_balance = df_balance.sort_values('date', ascending=False).reset_index(drop=True)
    
    if len(df_income) < 12 or len(df_balance) < 12:
        print(f"⚠️ 數據不足：損益表 {len(df_income)} 季，資產負債表 {len(df_balance)} 季（需要至少12季）")
        return None
    
    results = []
    
    # 計算最近3年（每年4季）
    for year_idx in range(3):
        start_idx = year_idx * 4
        end_idx = start_idx + 4
        
        print(f"\n📅 第 {year_idx + 1} 年分析（索引 {start_idx}-{end_idx-1}，即 t{start_idx}-t{end_idx-1}）:")
        
        # 打印該年度4季數據（從早到晚）
        print(f"  損益表 4季數據（從早到晚顯示）：")
        df_sorted = df_income.iloc[start_idx:end_idx].copy().sort_values('date', ascending=True)
        for idx, row in df_sorted.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"    {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 營收: {row.get('revenue', 0):,.0f} | 淨利: {row.get('netIncome', 0):,.0f}")
        
        print(f"  資產負債表 4季數據（從早到晚顯示）：")
        df_sorted = df_balance.iloc[start_idx:end_idx].copy().sort_values('date', ascending=True)
        for idx, row in df_sorted.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"    {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 總資產: {row.get('TotalAssets', 0):,.0f} | 權益: {row.get('Equity', 0):,.0f}")
        
        income_data = aggregate_quarterly_to_annual(df_income.iloc[start_idx:end_idx + 4], periods_latest=4, periods_previous=4)
        balance_data = aggregate_quarterly_to_annual(df_balance.iloc[start_idx:end_idx + 4], periods_latest=4, periods_previous=4)
        
        if not income_data or not balance_data:
            continue
        
        ci = income_data['current']
        cb = balance_data['current']
        
        net = ci.get('netIncome', 0)
        rev = ci.get('revenue', 1)
        ta = cb.get('TotalAssets', 1)
        eq = cb.get('Equity', 1)
        
        nm = safe_divide(net, rev)  # 淨利率
        at = safe_divide(rev, ta)   # 資產週轉率
        em = safe_divide(ta, eq)    # 權益乘數
        roe = safe_divide(net, eq)
        
        print(f"\n  💰 年度合計/平均：")
        print(f"    淨利: {net:,.0f}")
        print(f"    營收: {rev:,.0f}")
        print(f"    總資產(平均): {ta:,.0f}")
        print(f"    權益(平均): {eq:,.0f}")
        
        print(f"\n  🔢 ROE三因子：")
        print(f"    淨利率(NM) = 淨利/營收 = {net:,.0f}/{rev:,.0f} = {nm:.4f}")
        print(f"    資產週轉率(AT) = 營收/總資產 = {rev:,.0f}/{ta:,.0f} = {at:.4f}")
        print(f"    權益乘數(EM) = 總資產/權益 = {ta:,.0f}/{eq:,.0f} = {em:.4f}")
        print(f"    ROE = NM × AT × EM = {nm:.4f} × {at:.4f} × {em:.4f} = {nm*at*em:.4f}")
        print(f"    直接ROE = 淨利/權益 = {net:,.0f}/{eq:,.0f} = {roe:.4f}")
        
        # 取最新一季的日期作為年度標記
        date_label = df_income.iloc[start_idx].get('date', '')
        
        results.append({
            'date': date_label,
            'net_margin': nm,
            'asset_turnover': at,
            'equity_multiplier': em,
            'direct_roe': roe
        })
    
    # 計算變化
    changes = None
    if len(results) >= 2:
        changes = {
            'net_margin_change': results[0]['net_margin'] - results[1]['net_margin'],
            'asset_turnover_change': results[0]['asset_turnover'] - results[1]['asset_turnover'],
            'equity_multiplier_change': results[0]['equity_multiplier'] - results[1]['equity_multiplier'],
            'roe_change': results[0]['direct_roe'] - results[1]['direct_roe'],
        }
        
        print(f"\n📈 年度變化（最新年 vs 前一年）：")
        print(f"  淨利率變化: {changes['net_margin_change']:+.4f}")
        print(f"  資產週轉率變化: {changes['asset_turnover_change']:+.4f}")
        print(f"  權益乘數變化: {changes['equity_multiplier_change']:+.4f}")
        print(f"  ROE變化: {changes['roe_change']:+.4f}")
    
    print("="*80 + "\n")
    
    return {'yearly_analysis': results, 'changes': changes}


def calculate_cashflow_analysis(df_income: pd.DataFrame, df_cash: pd.DataFrame) -> dict:
    """
    現金流分析（台股版）
    """
    print("\n" + "="*80)
    print("📊 現金流分析計算過程")
    print("="*80)
    
    # ⚠️ 確保數據按日期降序排列（最新的在前）
    if df_income is not None and not df_income.empty:
        df_income = df_income.sort_values('date', ascending=False).reset_index(drop=True)
    if df_cash is not None and not df_cash.empty:
        df_cash = df_cash.sort_values('date', ascending=False).reset_index(drop=True)
    
    income_annual = aggregate_quarterly_to_annual(df_income)
    cash_annual = aggregate_quarterly_to_annual(df_cash)
    
    if not all([income_annual, cash_annual]):
        return None
    
    # 打印原始季度數據（從早到晚）
    print("\n📅 最新4季現金流數據（從早到晚顯示）：")
    if df_cash is not None and not df_cash.empty and len(df_cash) >= 4:
        latest_4q = df_cash.iloc[:4].copy()
        latest_4q = latest_4q.sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            ocf = row.get('OCF', 0)
            capex = row.get('CapEx', 0)
            fcf = row.get('FCF', 0)
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | OCF: {ocf:,.0f} | CapEx: {capex:,.0f} | FCF: {fcf:,.0f}")
    
    print("\n📅 前4季現金流數據（從早到晚顯示）：")
    if df_cash is not None and len(df_cash) >= 8:
        prev_4q = df_cash.iloc[4:8].copy()
        prev_4q = prev_4q.sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            ocf = row.get('OCF', 0)
            capex = row.get('CapEx', 0)
            fcf = row.get('FCF', 0)
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | OCF: {ocf:,.0f} | CapEx: {capex:,.0f} | FCF: {fcf:,.0f}")
    
    print("\n📅 最新4季淨利數據（從早到晚顯示）：")
    if df_income is not None and not df_income.empty and len(df_income) >= 4:
        latest_4q = df_income.iloc[:4].copy()
        latest_4q = latest_4q.sort_values('date', ascending=True)
        for idx, row in latest_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 淨利: {row.get('netIncome', 0):,.0f}")
    
    print("\n📅 前4季淨利數據（從早到晚顯示）：")
    if df_income is not None and len(df_income) >= 8:
        prev_4q = df_income.iloc[4:8].copy()
        prev_4q = prev_4q.sort_values('date', ascending=True)
        for idx, row in prev_4q.iterrows():
            q_label = row.get('quarter_label', f"{row['date'].year}-Q{row['date'].quarter}")
            print(f"  {q_label} ({row['date'].strftime('%Y-%m-%d')}) | 淨利: {row.get('netIncome', 0):,.0f}")
    
    ci = income_annual['current']
    cc = cash_annual['current']
    
    ocf = cc.get('OCF', 0)
    cfi = cc.get('CFI', 0)
    cff = cc.get('CFF', 0)
    net = ci.get('netIncome', 1)
    capex = cc.get('CapEx', 0)
    
    print(f"\n💰 年度合計數據（4季加總）：")
    print(f"  營運現金流(OCF): {ocf:,.0f}")
    print(f"  投資現金流(CFI): {cfi:,.0f}")
    print(f"  融資現金流(CFF): {cff:,.0f}")
    print(f"  淨利: {net:,.0f}")
    print(f"  資本支出(CapEx): {capex:,.0f}")
    
    # 現金流品質比率
    ocf_quality = safe_divide(ocf, net)
    
    print(f"\n🔢 現金流品質比率：")
    print(f"  OCF品質 = OCF/淨利 = {ocf:,.0f}/{net:,.0f} = {ocf_quality:.4f}")
    
    # 品質評估
    if ocf_quality >= 1.2:
        q, emoji = "優秀", "😊"
    elif ocf_quality >= 1.0:
        q, emoji = "良好", "🙂"
    elif ocf_quality >= 0.8:
        q, emoji = "尚可", "😐"
    else:
        q, emoji = "需關注", "😰"
    
    print(f"  評估: {q} {emoji}")
    
    # 自由現金流（使用絕對值確保 CapEx 為正）
    free_cashflow = ocf - abs(capex)
    
    print(f"\n💵 自由現金流：")
    print(f"  FCF = OCF - |CapEx| = {ocf:,.0f} - {abs(capex):,.0f} = {free_cashflow:,.0f}")
    
    total_cf = ocf + cfi + cff
    
    print(f"\n📊 現金流結構：")
    print(f"  營運現金流: {ocf:,.0f} ({safe_divide(ocf, total_cf)*100:.1f}%)" if total_cf != 0 else f"  營運現金流: {ocf:,.0f}")
    print(f"  投資現金流: {cfi:,.0f} ({safe_divide(cfi, total_cf)*100:.1f}%)" if total_cf != 0 else f"  投資現金流: {cfi:,.0f}")
    print(f"  融資現金流: {cff:,.0f} ({safe_divide(cff, total_cf)*100:.1f}%)" if total_cf != 0 else f"  融資現金流: {cff:,.0f}")
    print(f"  總現金流: {total_cf:,.0f}")
    
    print("="*80 + "\n")
    
    return {
        'ocf_quality': ocf_quality,
        'free_cashflow': free_cashflow,
        'quality_assessment': q,
        'quality_emoji': emoji,
        'structure': {
            'operating': ocf,
            'investing': cfi,
            'financing': cff,
            'total': total_cf
        }
    }

#%%
# ==================== AI 資產負債表分析 ====================
def generate_bs_insights(symbol: str, df_balance: pd.DataFrame, openai_api_key: str, periods: int = 8) -> str:
    """AI 資產負債表分析"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        if df_balance is None or df_balance.empty:
            return "查無資產負債表資料。"
        
        dfb = df_balance.copy()
        if "date" in dfb.columns:
            dfb["date"] = pd.to_datetime(dfb["date"])
            dfb = dfb.sort_values("date")
            
        dfb = dfb.tail(periods)
        
        data_json = dfb.to_json(orient="records", date_format="iso", force_ascii=False)
        
        system_msg = "你是一位嚴謹的財務報表分析師，使用繁體中文，聚焦解讀資料與比率含義"
        
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
def generate_is_insights(symbol: str, df_income: pd.DataFrame, openai_api_key: str, periods: int = 8) -> str:
    """AI 損益表分析"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        if df_income is None or df_income.empty:
            return "查無損益表資料。"
        
        dfi = df_income.copy()
        if "date" in dfi.columns:
            dfi["date"] = pd.to_datetime(dfi["date"])
            dfi = dfi.sort_values("date")
            
        dfi = dfi.tail(periods)
        
        data_json = dfi.to_json(orient="records", date_format="iso", force_ascii=False)
        
        system_msg = "你是一位嚴謹的財務報表分析師，使用繁體中文，聚焦解讀資料與比率含義"
        
        user_prompt = f"""
        以下為近 {periods} 期損益表重點欄位與比率：
        {data_json}

        根據資料內容，依照下列【固定架構】進行分析
        必須用「條列式」清楚列點，每個項目內細分，要有分點符號（如：•）
        每段標題請加粗（用 ** ），並保持簡潔、重點明確

        1 規模與成長（Revenue / GP / OI / Net Income / EPS）
        - 分別列出eps趨勢、各科目的歷史變化與相鄰期變動率，並解說趨勢
        2 獲利能力（Margins）
        - 分別列出毛利率、營業利益率、淨利率歷史變化，並解說趨勢
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
def generate_cf_insights(symbol: str, df_cash: pd.DataFrame, openai_api_key: str, periods: int = 8) -> str:
    """AI 現金流量表分析"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        if df_cash is None or df_cash.empty:
            return "查無現金流量表資料。"
        
        dfc = df_cash.copy()
        if "date" in dfc.columns:
            dfc["date"] = pd.to_datetime(dfc["date"])
            dfc = dfc.sort_values("date")
            
        dfc = dfc.tail(periods)
        
        data_json = dfc.to_json(orient="records", date_format="iso", force_ascii=False)
        
        system_msg = "你是一位嚴謹的財務報表分析師，使用繁體中文，聚焦解讀資料與比率含義"
        
        user_prompt = f"""
            以下為近 {periods} 期現金流量表重點欄位與比率（JSON）：
            {data_json}

            根據資料內容，依照下列【固定架構】進行分析
            必須用「條列式」清楚列點，每個項目內細分，要有分點符號（如：•）
            每段標題請加粗（用 ** ），並保持簡潔、重點明確
            
            1 現金來源與去化
            - 分別列出 OCF / CFI / CFF 歷史變化，並解說趨勢
            2 自由現金流與投資強度
            - 分別列出 FCF / CapEx 歷史變化，並解說趨勢
            3 現金轉換率
            - 分別列出（OCF/淨利） 歷史變化，並解說趨勢
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
        st.error(f"❌ AI 現金流量表分析失敗: {str(e)}")
        return None

#%%
# ==================== AI 財務分析 ======================
def generate_core_metrics_insights(symbol: str, core: pd.DataFrame, openai_api_key: str, periods: int = 8) -> str:
    """AI 財務核心指標分析"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        if core is None or core.empty:
            return "查無核心指標資料。"
        
        dfc = core.copy()
        if "date" in dfc.columns:
            dfc["date"] = pd.to_datetime(dfc["date"])
            dfc = dfc.sort_values("date")
        
        dfc = dfc.tail(periods)
        
        data_json = dfc.to_json(orient="records", date_format="iso", force_ascii=False)
        
        system_msg = "你是一位嚴謹的財務報表分析師，使用繁體中文，聚焦解讀資料與比率含義"
        
        user_prompt = f"""
            以下為近 {periods} 期財務核心指標之資料與比率：
            {data_json}

            根據資料內容，依下列【固定架構】進行分析，必須用「條列式」清楚列點，每個項目內細分，要有分點符號（如：•）
            每段標題請加粗（用 ** ），並保持簡潔、重點明確

            1 ROE / ROA
            - 條列式列出 ROE、ROA 歷史變化，並解說趨勢
            2 資產週轉率
            - 條列式列出資產週轉率，解說趨勢
            3 現金品質
            - 條列式列出現金轉換率、FCF Margin 之歷史變化，並解說
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
        st.error(f"❌ AI 核心指標分析失敗: {str(e)}")
        return None


#%%
# ==================== AI 技術面分析 ====================
def generate_ai_insights(symbol, stock_data, openai_api_key):
    from datetime import datetime
    today_date = datetime.today().strftime("%Y-%m-%d")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        cols = ["date", "open", "high", "low", "close", "volume",
                "MA5", "MA10", "MA20", "MA60",
                "RSI9", "RSI14", "K9", "D9",
                "DIF", "MACD", "OSC",
                "BB_MID", "BB_UPPER", "BB_LOWER"]
        
        use_cols = [c for c in cols if c in stock_data.columns]
        
        if "date" in stock_data.columns:
            stock_data["date"] = pd.to_datetime(stock_data["date"])
            stock_data = stock_data.sort_values("date")
        
        data_json = stock_data[use_cols].tail(30).to_json(orient="records", date_format="iso", force_ascii=False)
        
        system_msg = "你是一位嚴謹的技術面分析師，使用繁體中文，聚焦解讀資料與比率含義"
        
        user_prompt = f"""
            歷史資料：
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
# ==================== AI 四階段財報結果 ====================
def generate_four_stage_ai_analysis(symbol, fscore, zscore, dupont, cashflow, openai_api_key):
    from openai import OpenAI
    client = OpenAI(api_key=openai_api_key)

    # FIX: 輔助格式化，避免 NaN/None 造成 format 崩
    def _fmt(x, nd=4):
        try:
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return "N/A"
            return f"{x:.{nd}f}"
        except Exception:
            return str(x)

    # FIX: 取正確鍵名，並以 score 決定 ✓/✗
    def _lines(items):
        out = []
        for it in items or []:
            name = it.get("name", "")
            cur = _fmt(it.get("current"))
            prev = _fmt(it.get("previous"))
            sc = it.get("score", 0)
            out.append(f"- {name}: {'✓' if sc else '✗'} (當前: {cur}, 前期: {prev})")
        return "\n".join(out)

    p_list = (fscore or {}).get("profitability_scores", [])
    l_list = (fscore or {}).get("leverage_scores", [])
    e_list = (fscore or {}).get("efficiency_scores", [])

    comp = (zscore or {}).get("components", {}) or {}
    A, B, C, D, E = comp.get("A"), comp.get("B"), comp.get("C"), comp.get("D"), comp.get("E")

    # FIX: 組裝文字時避免 KeyError
    analysis_text = f"""
#### 1. Piotroski F-Score 分析
總分: {(fscore or {}).get('total_score', 'N/A')}/9分

##### 獲利能力指標:
{_lines(p_list)}

##### 槓桿與流動性指標:
{_lines(l_list)}

##### 營運效率指標:
{_lines(e_list)}

#### 2. Altman Z-Score 分析
Z-Score: {_fmt((zscore or {}).get('z_score'), 2)}
風險等級: {(zscore or {}).get('risk_level', 'N/A')}

組成要素:
- A項 (營運資本/總資產): {_fmt(A)}
- B項 (保留盈餘/總資產): {_fmt(B)}
- C項 (EBIT/總資產): {_fmt(C)}
- D項 (市值/總負債): {_fmt(D)}
- E項 (營收/總資產): {_fmt(E)}
"""

    if dupont and dupont.get('yearly_analysis'):
        latest = dupont['yearly_analysis'][0]
        analysis_text += f"""
#### 3. 杜邦分析
最新年度ROE: {_fmt(latest.get('direct_roe'))}
- 淨利率: {_fmt(latest.get('net_margin'))}
- 資產週轉率: {_fmt(latest.get('asset_turnover'))}
- 權益乘數: {_fmt(latest.get('equity_multiplier'))}
"""

    cf = cashflow or {}
    # FIX: 兼容 free_cash_flow / free_cashflow 命名
    fcf_val = cf.get('free_cash_flow', cf.get('free_cashflow'))
    qa = cf.get('quality_assessment', 'N/A')
    struct = cf.get('structure', {}) or {}

    analysis_text += f"""
#### 4. 現金流分析
營運現金流品質比率: {_fmt(cf.get('ocf_quality'), 2)}
自由現金流: {format_large_number(fcf_val)}
品質評估: {qa}

現金流結構:
- 營運現金流: {format_large_number(struct.get('operating'))}
- 投資現金流: {format_large_number(struct.get('investing'))}
- 融資現金流: {format_large_number(struct.get('financing'))}
"""

    system_message = "你是一位專業的財務分析師，精通財報分析和投資評估。請基於已計算完成的四階段財務分析結果進行專業解讀。使用繁體中文回答。"
    user_message = f"""請基於以下 {symbol} 的四階段財務分析結果，提供專業的投資評估報告：

{analysis_text}

請按以下結構提供分析：
1. **Piotroski F-Score 解讀**
- 解釋得分的投資意義
- 分析各項指標反映的業務狀況
2. **Altman Z-Score 風險評估**
- 解讀風險等級的含義
- 分析各組成要素的影響
3. **杜邦分析趨勢洞察**
- 分析 ROE 三因子的變化
- 識別主要驅動力
4. **現金流結構深度分析**
- 評估現金流品質
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
        messages=[{"role": "system", "content": system_message},
                  {"role": "user", "content": user_message}],
        temperature=0.1,
        max_tokens=5000
    )
    return response.choices[0].message.content
