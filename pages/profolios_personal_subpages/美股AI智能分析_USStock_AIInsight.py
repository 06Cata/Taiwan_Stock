# 美股AI智能分析_USStock_AIInsight.py

import streamlit as st
import os
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from openai import OpenAI
from plotly.subplots import make_subplots

from pages.profolios_personal_subpages.us_stock_ai_insight import (
    # API 數據獲取
    get_balance_ratios, get_income_ratios, get_cashflow_ratios, get_stock_data,
    get_enterprise_values, get_company_profile, get_key_metrics,
    # 財務計算
    compute_core_cross_metrics_from_frames, filter_by_date_range,
    # 四階段分析計算
    calculate_piotroski_fscore, calculate_altman_zscore, 
    calculate_dupont_analysis, calculate_cashflow_analysis,
    safe_divide, format_large_number,
    # 技術指標
    get_moving_averages, add_rsi, add_kd, add_macd, add_bbands,
    # AI 分析
    generate_bs_insights, generate_is_insights, generate_cf_insights, 
    generate_core_metrics_insights, generate_ai_insights, generate_four_stage_ai_analysis
)

# ==================== 頁面設定 ====================
def main():

    st.subheader("美股AI智能分析 US Stock AI Insight")
    st.write("""
        請自行申請 **[FMP API Key](https://site.financialmodelingprep.com/)** 與 **[OpenAI API Key](https://openai.com/api/)**，系統會根據 **技術面**（均線、K線、趨勢等）與 **基本面** 資料，
        生成一份由 AI 撰寫的分析報告，[參考檔案](https://drive.google.com/drive/folders/1E4BOclNnGn0_ly3a1opP9V6Oku3snT8t?usp=sharing)，以上觀點僅供參考，並不構成任何交易建議或推薦
    """)

    # ==================== 頂部輸入表單 ====================
    with st.form("top_controls", clear_on_submit=False):
        st.markdown("###### 分析設定")

        c1, c2, c3 = st.columns([1.2, 1.2, 1])
        with c1:
            symbol = st.text_input("股票代碼 (美股)", value="GOOGL")
        with c2:
            fmp_api_key = st.text_input(
                "FMP API Key", type="password", value=os.getenv("FMP_API_KEY", "")
            )
        with c3:
            openai_api_key = st.text_input(
                "OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", "")
            )
            
        st.markdown("###### 日期範圍")
        d1, d2 = st.columns(2)
        default_start = datetime.now() - timedelta(days=90)
        default_end = datetime.now()
        with d1:
            start_date = st.date_input("起始日期", value=default_start)
        with d2:
            end_date = st.date_input("結束日期", value=default_end)

        analyze_button = st.form_submit_button("開始分析", use_container_width=True)

    st.divider()

    # ==================== 主分析流程 ====================
    if analyze_button:
        if not symbol or not fmp_api_key or not openai_api_key:
            st.error("❌ 請完整輸入股票代碼與 API Key")
        elif start_date >= end_date:
            st.error("❌ 起始日期必須早於結束日期")
        else:
            symbol = symbol.strip().upper()

            with st.spinner(f"正在獲取 {symbol} 股票資料..."):
                stock_data = get_stock_data(symbol, fmp_api_key)
            if stock_data is None:
                st.stop()

            with st.spinner("篩選日期範圍..."):
                filtered_data = filter_by_date_range(stock_data, start_date, end_date)
            if filtered_data is None:
                st.stop()

            with st.spinner("計算資產負債表指標..."):
                df_balance = get_balance_ratios(symbol, fmp_api_key)
            
            with st.spinner("計算損益表指標..."):
                df_income = get_income_ratios(symbol, fmp_api_key)
                
            with st.spinner("計算現金流量表指標..."):
                df_cash = get_cashflow_ratios(symbol, fmp_api_key)
                
            with st.spinner("計算財務指標..."):
                core = compute_core_cross_metrics_from_frames(
                    df_income,   # Income Statement
                    df_balance,  # Balance Sheet
                    df_cash      # Cash Flow Statement
                )
                
            # ==================== 四階段分析 ====================
            with st.spinner("獲取企業價值數據..."):
                df_enterprise = get_enterprise_values(symbol, fmp_api_key)
            
            with st.spinner("獲取公司基本資料..."):
                company_profile = get_company_profile(symbol, fmp_api_key)
            
            # with st.spinner("獲取關鍵指標..."):
            #     df_key_metrics = get_key_metrics(symbol, fmp_api_key)
            
            # ==================== 四階段分析 ====================

            with st.spinner("計算技術指標..."):
                filtered_data = get_moving_averages(filtered_data)
                filtered_data = add_rsi(filtered_data)
                filtered_data = add_kd(filtered_data, period=9, k_smooth=3, d_smooth=3)
                filtered_data = add_macd(filtered_data)  
                filtered_data = add_bbands(filtered_data, window=20, num_std=2.0) 
                
            tab1, tab2, tab3 = st.tabs(["1 - 基本面、技術面分析", "2 - 公司財務評價", "3 - AI分析"])
            
            with tab1:
                # ==== 基本統計 ====
                st.markdown("#### ★ 統計")
                col1, col2, col3 = st.columns(3)
                start_price = filtered_data["close"].iloc[0]
                end_price = filtered_data["close"].iloc[-1]
                price_change = end_price - start_price
                price_pct = (price_change / start_price) * 100
                with col1:
                    st.metric("起始價格", f"${start_price:.2f}")
                with col2:
                    st.metric("結束價格", f"${end_price:.2f}")
                with col3:
                    st.metric("價格變化", f"${price_change:.2f}", delta=f"{price_pct:.2f}%")
                
                st.divider()
                
                # === 資產負債表 ===
                st.markdown("### ★ 資產負債表趨勢")

                dfb = df_balance.copy()
                dfb["date"] = pd.to_datetime(dfb["date"])
                dfb = dfb.sort_values("date")

                # === 規模面：資產 / 負債 / 權益 ===
                fig_bs_size = go.Figure()
                fig_bs_size.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["totalAssets"],
                    name="Total Assets（總資產）", mode="lines", line=dict(width=2)
                ))
                fig_bs_size.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["totalLiabilities"],
                    name="Total Liabilities（總負債）", mode="lines", line=dict(width=2)
                ))
                fig_bs_size.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["totalStockholdersEquity"],
                    name="Shareholders' Equity（股東權益）", mode="lines", line=dict(width=2)
                ))

                fig_bs_size.update_layout(
                    height=360, hovermode="x unified",
                    title=f"{symbol} 資產 / 負債 / 股東權益（規模）",
                    legend=dict(
                        orientation="h",  # 橫向排列
                        yanchor="top",
                        y=-0.25,          # 移到圖表下方
                        xanchor="center",
                        x=0.5,
                        font=dict(size=11)
                    )
                )
                fig_bs_size.update_yaxes(title_text="金額（USD）", rangemode="tozero")
                fig_bs_size.update_xaxes(title_text="日期")
                st.plotly_chart(fig_bs_size, use_container_width=True)


                # === 償債能力：流動比 / 速動比 / 現金比 ===
                fig_bs_liquidity = go.Figure()
                fig_bs_liquidity.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["current_ratio"],
                    name="Current Ratio（流動比率）", mode="lines+markers"
                ))
                fig_bs_liquidity.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["quick_ratio"],
                    name="Quick Ratio（速動比率）", mode="lines+markers"
                ))
                fig_bs_liquidity.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["cash_ratio"],
                    name="Cash Ratio（現金比率）", mode="lines+markers"
                ))

                fig_bs_liquidity.update_layout(
                    height=320, hovermode="x unified",
                    title=f"{symbol} 償債能力指標（Liquidity Ratios）",
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.25,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=11)
                    )
                )
                fig_bs_liquidity.update_yaxes(title_text="倍數（x）", rangemode="tozero")
                fig_bs_liquidity.update_xaxes(title_text="日期")
                st.plotly_chart(fig_bs_liquidity, use_container_width=True)


                # === 槓桿結構：負債比 / 權益比 / 淨負債比 ===
                fig_bs_leverage = go.Figure()
                fig_bs_leverage.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["debt_ratio"],
                    name="Debt Ratio（負債比率）", mode="lines+markers"
                ))
                fig_bs_leverage.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["equity_ratio"],
                    name="Equity Ratio（權益比率）", mode="lines+markers"
                ))
                fig_bs_leverage.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["debt_to_equity"],
                    name="Debt to Equity（負債權益比）", mode="lines+markers"
                ))
                fig_bs_leverage.add_trace(go.Scatter(
                    x=dfb["date"], y=dfb["net_debt_ratio"],
                    name="Net Debt / Assets（淨負債比）", mode="lines+markers"
                ))

                fig_bs_leverage.update_layout(
                    height=340, hovermode="x unified",
                    title=f"{symbol} 槓桿結構指標（Leverage Ratios）",
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.25,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=11)
                    )
                )
                fig_bs_leverage.update_yaxes(title_text="比例（% 或 倍數）", rangemode="tozero")
                fig_bs_leverage.update_xaxes(title_text="日期")
                st.plotly_chart(fig_bs_leverage, use_container_width=True)


                # === bs 財報比率表格 ===
                st.markdown("##### 近期財務比率一覽")
                show_cols = [
                    "date",
                    "current_ratio","quick_ratio","cash_ratio",
                    "debt_ratio","equity_ratio","debt_to_equity","net_debt_ratio"
                ]
                st.dataframe(dfb[show_cols].tail(6).reset_index(drop=True), use_container_width=True)

                st.divider()
                
                
                # === 損益表 ===
                st.markdown("### ★ 損益表趨勢（Income Statement Trends）")
                dfi = df_income.copy()
                dfi["date"] = pd.to_datetime(dfi["date"])
                dfi = dfi.sort_values("date")

                # 3.1 規模：營收/毛利/營業利益/淨利
                fig_is_scale = go.Figure()
                fig_is_scale.add_trace(go.Scatter(x=dfi["date"], y=dfi["revenue"],
                    name="Revenue（營收）", mode="lines"))
                fig_is_scale.add_trace(go.Scatter(x=dfi["date"], y=dfi["grossProfit"],
                    name="Gross Profit（毛利）", mode="lines"))
                fig_is_scale.add_trace(go.Scatter(x=dfi["date"], y=dfi["operatingIncome"],
                    name="Operating Income（營業利益）", mode="lines"))
                fig_is_scale.add_trace(go.Scatter(x=dfi["date"], y=dfi["netIncome"],
                    name="Net Income（淨利）", mode="lines"))

                fig_is_scale.update_layout(
                    height=360, hovermode="x unified",
                    title=f"{symbol} 規模（Scale）",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_is_scale.update_yaxes(title_text="金額（USD）", rangemode="tozero")
                fig_is_scale.update_xaxes(title_text="日期")
                st.plotly_chart(fig_is_scale, use_container_width=True)

                # 3.2 獲利能力：各種利潤率
                fig_is_margin = go.Figure()
                fig_is_margin.add_trace(go.Scatter(x=dfi["date"], y=dfi["gross_margin"],
                    name="Gross Margin（毛利率）", mode="lines+markers"))
                fig_is_margin.add_trace(go.Scatter(x=dfi["date"], y=dfi["operating_margin"],
                    name="Operating Margin（營業利益率）", mode="lines+markers"))
                fig_is_margin.add_trace(go.Scatter(x=dfi["date"], y=dfi["ebitda_margin"],
                    name="EBITDA Margin", mode="lines+markers"))
                fig_is_margin.add_trace(go.Scatter(x=dfi["date"], y=dfi["net_margin"],
                    name="Net Margin（淨利率）", mode="lines+markers"))

                fig_is_margin.update_layout(
                    height=320, hovermode="x unified",
                    title=f"{symbol} 獲利能力（Profitability）",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_is_margin.update_yaxes(title_text="比例（0~1）", rangemode="tozero")
                fig_is_margin.update_xaxes(title_text="日期")
                st.plotly_chart(fig_is_margin, use_container_width=True)

                # 3.3 費用結構：研發 / 銷管 占比
                fig_is_exp = go.Figure()
                fig_is_exp.add_trace(go.Scatter(x=dfi["date"], y=dfi["rnd_ratio"],
                    name="R&D / Revenue（研發比率）", mode="lines+markers"))
                fig_is_exp.add_trace(go.Scatter(x=dfi["date"], y=dfi["sga_ratio"],
                    name="SG&A / Revenue（銷管比率）", mode="lines+markers"))

                fig_is_exp.update_layout(
                    height=300, hovermode="x unified",
                    title=f"{symbol} 費用結構（Expense Mix）",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_is_exp.update_yaxes(title_text="比例（0~1）", rangemode="tozero")
                fig_is_exp.update_xaxes(title_text="日期")
                st.plotly_chart(fig_is_exp, use_container_width=True)

                # 3.4 每股與其他：EPS / Revenue per Share / 稅率 / 利息保障倍數
                fig_is_ps = go.Figure()
                fig_is_ps.add_trace(go.Scatter(x=dfi["date"], y=dfi["epsDiluted"],
                    name="EPS (Diluted)", mode="lines+markers"))
                fig_is_ps.add_trace(go.Scatter(x=dfi["date"], y=dfi["revenue_ps"],
                    name="Revenue per Share（每股營收）", mode="lines+markers"))

                fig_is_ps.update_layout(
                    height=300, hovermode="x unified",
                    title=f"{symbol} 每股指標（Per Share）",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_is_ps.update_yaxes(title_text="金額（USD）")
                fig_is_ps.update_xaxes(title_text="日期")
                st.plotly_chart(fig_is_ps, use_container_width=True)

                fig_is_other = go.Figure()
                fig_is_other.add_trace(go.Scatter(x=dfi["date"], y=dfi["tax_rate"],
                    name="Tax Rate（稅率）", mode="lines+markers"))
                fig_is_other.add_trace(go.Scatter(x=dfi["date"], y=dfi["interest_coverage"],
                    name="Interest Coverage（利息保障倍數）", mode="lines+markers"))

                fig_is_other.update_layout(
                    height=300, hovermode="x unified",
                    title=f"{symbol} 稅率與利息保障倍數",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_is_other.update_yaxes(title_text="比率 / 倍數", rangemode="tozero")
                fig_is_other.update_xaxes(title_text="日期")
                st.plotly_chart(fig_is_other, use_container_width=True)

                # === ci 財報比率表格 ===
                if df_income is not None and not df_income.empty:
                    st.markdown("#### 近期損益一覽")
                    st.dataframe(df_income.tail(8), use_container_width=True)
                    
                st.divider()
                
                
                # === 現金流量表 ===
                st.markdown("### ★ 現金流量表趨勢（Cash Flow Statement Trends）")
                dfc = df_cash.copy()
                dfc["date"] = pd.to_datetime(dfc["date"])
                dfc = dfc.sort_values("date")

                # 3.1 OCF / CFI / CFF（柱狀）
                fig_cf_core = go.Figure()
                fig_cf_core.add_trace(go.Bar(x=dfc["date"], y=dfc["OCF"], name="OCF（營運現金流）"))
                fig_cf_core.add_trace(go.Bar(x=dfc["date"], y=dfc["CFI"], name="CFI（投資現金流）"))
                fig_cf_core.add_trace(go.Bar(x=dfc["date"], y=dfc["CFF"], name="CFF（融資現金流）"))
                fig_cf_core.update_layout(
                    barmode="group",
                    height=360, hovermode="x unified",
                    title=f"{symbol} OCF / CFI / CFF",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_cf_core.update_yaxes(title_text="金額（USD）", zeroline=True, zerolinewidth=1)
                fig_cf_core.update_xaxes(title_text="日期")
                st.plotly_chart(fig_cf_core, use_container_width=True)

                # 3.2 FCF 與 CapEx（折線）
                fig_cf_fcf = go.Figure()
                fig_cf_fcf.add_trace(go.Scatter(x=dfc["date"], y=dfc["FCF"], name="Free Cash Flow（自由現金流）", mode="lines+markers"))
                fig_cf_fcf.add_trace(go.Scatter(x=dfc["date"], y=dfc["CapEx"], name="CapEx（資本支出）", mode="lines+markers"))
                fig_cf_fcf.update_layout(
                    height=320, hovermode="x unified",
                    title=f"{symbol} FCF 與 CapEx",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_cf_fcf.update_yaxes(title_text="金額（USD）")
                fig_cf_fcf.update_xaxes(title_text="日期")
                st.plotly_chart(fig_cf_fcf, use_container_width=True)

                # 3.3 股東回饋 & 槓桿（柱＋線）
                fig_cf_payout = go.Figure()
                fig_cf_payout.add_trace(go.Bar(x=dfc["date"], y=dfc["Dividends"], name="Dividends（股利）"))
                fig_cf_payout.add_trace(go.Bar(x=dfc["date"], y=dfc["Buybacks"],  name="Buybacks（庫藏股）"))
                fig_cf_payout.add_trace(go.Scatter(x=dfc["date"], y=dfc["netDebtIssuance"],
                                                name="Net Debt Issuance（淨舉債）", mode="lines+markers"))
                fig_cf_payout.update_layout(
                    barmode="stack",
                    height=320, hovermode="x unified",
                    title=f"{symbol} 股東回饋與淨舉債",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_cf_payout.update_yaxes(title_text="金額（USD）")
                fig_cf_payout.update_xaxes(title_text="日期")
                st.plotly_chart(fig_cf_payout, use_container_width=True)

                # 3.4 營運資金變動 / SBC / D&A（柱＋線）
                fig_cf_wc = go.Figure()
                fig_cf_wc.add_trace(go.Bar(x=dfc["date"], y=dfc["changeInWorkingCapital"], name="Δ Working Capital（營運資金變動）"))
                fig_cf_wc.add_trace(go.Scatter(x=dfc["date"], y=dfc["stockBasedCompensation"],
                                            name="SBC（股權給付費用）", mode="lines+markers"))
                fig_cf_wc.add_trace(go.Scatter(x=dfc["date"], y=dfc["depreciationAndAmortization"],
                                            name="D&A（折舊攤銷）", mode="lines+markers"))
                fig_cf_wc.update_layout(
                    height=320, hovermode="x unified",
                    title=f"{symbol} 營運資金/SBC/D&A",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_cf_wc.update_yaxes(title_text="金額（USD）")
                fig_cf_wc.update_xaxes(title_text="日期")
                st.plotly_chart(fig_cf_wc, use_container_width=True)

                # 3.5 現金存量（期末現金）
                fig_cf_cash = go.Figure()
                fig_cf_cash.add_trace(go.Scatter(x=dfc["date"], y=dfc["cashAtEndOfPeriod"],
                                                name="Cash at End（期末現金）", mode="lines+markers"))
                fig_cf_cash.update_layout(
                    height=300, hovermode="x unified",
                    title=f"{symbol} 期末現金",
                    legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                )
                fig_cf_cash.update_yaxes(title_text="金額（USD）")
                fig_cf_cash.update_xaxes(title_text="日期")
                st.plotly_chart(fig_cf_cash, use_container_width=True)

                # === cfs 財報比率表格 ===
                if df_cash is not None and not df_cash.empty:
                    st.markdown("#### 近期現金流摘要")
                    st.dataframe(df_cash.tail(8), use_container_width=True)

                st.divider()
                
                # === 財務指標 ===
                st.markdown("### ★ 財務核心指標")

                if core is not None and not core.empty:
                    core["date"] = pd.to_datetime(core["date"])
                    core = core.sort_values("date")

                    # 1. ROE / ROA
                    fig_core_roe_roa = go.Figure()
                    fig_core_roe_roa.add_trace(go.Scatter(
                        x=core["date"], y=core["ROE"],
                        name="ROE（股東權益報酬率）", mode="lines+markers"
                    ))
                    fig_core_roe_roa.add_trace(go.Scatter(
                        x=core["date"], y=core["ROA"],
                        name="ROA（資產報酬率）", mode="lines+markers"
                    ))
                    fig_core_roe_roa.update_layout(
                        height=300, hovermode="x unified",
                        title=f"{symbol} ROE / ROA",
                        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                    )
                    fig_core_roe_roa.update_yaxes(title_text="比率", rangemode="tozero")
                    fig_core_roe_roa.update_xaxes(title_text="日期")
                    st.plotly_chart(fig_core_roe_roa, use_container_width=True)

                    # 2. 資產週轉率（Asset Turnover）
                    fig_core_turnover = go.Figure()
                    fig_core_turnover.add_trace(go.Scatter(
                        x=core["date"], y=core["asset_turnover"],
                        name="Asset Turnover（資產週轉率）", mode="lines+markers"
                    ))
                    fig_core_turnover.update_layout(
                        height=280, hovermode="x unified",
                        title=f"{symbol} 資產週轉率（Asset Turnover）",
                        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                    )
                    fig_core_turnover.update_yaxes(title_text="倍數", rangemode="tozero")
                    fig_core_turnover.update_xaxes(title_text="日期")
                    st.plotly_chart(fig_core_turnover, use_container_width=True)

                    # 3. 現金品質（Cash Conversion, FCF Margin）
                    fig_core_cash = go.Figure()
                    fig_core_cash.add_trace(go.Scatter(
                        x=core["date"], y=core["cash_conversion"],
                        name="OCF / Net Income（現金轉換率）", mode="lines+markers"
                    ))
                    fig_core_cash.add_trace(go.Scatter(
                        x=core["date"], y=core["fcf_margin"],
                        name="FCF Margin（自由現金流率）", mode="lines+markers"
                    ))
                    fig_core_cash.update_layout(
                        height=280, hovermode="x unified",
                        title=f"{symbol} 現金品質與自由現金流率",
                        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                    )
                    fig_core_cash.update_yaxes(title_text="比率", rangemode="tozero")
                    fig_core_cash.update_xaxes(title_text="日期")
                    st.plotly_chart(fig_core_cash, use_container_width=True)

                    # 4. 資本支出與股東回饋對 OCF
                    fig_core_capex = go.Figure()
                    fig_core_capex.add_trace(go.Scatter(
                        x=core["date"], y=core["capex_to_ocf"],
                        name="CapEx / OCF（資本支出強度）", mode="lines+markers"
                    ))
                    fig_core_capex.add_trace(go.Scatter(
                        x=core["date"], y=core["payout_to_ocf"],
                        name="Payout / OCF（股東回饋比）", mode="lines+markers"
                    ))
                    fig_core_capex.update_layout(
                        height=260, hovermode="x unified",
                        title=f"{symbol} 資本支出與股東回饋對 OCF",
                        legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11))
                    )
                    fig_core_capex.update_yaxes(title_text="比率", rangemode="tozero")
                    fig_core_capex.update_xaxes(title_text="日期")
                    st.plotly_chart(fig_core_capex, use_container_width=True)

                    # 5. 指標表格
                    st.markdown("#### 近期財務核心指標")
                    show_cols = [
                        "date", "ROE", "ROA", "asset_turnover", "cash_conversion", "fcf_margin", "capex_to_ocf", "payout_to_ocf"
                    ]
                    st.dataframe(core[show_cols].tail(8).reset_index(drop=True), use_container_width=True)
                else:
                    st.info("查無財務核心指標資料。")

                st.divider()
                
                # ==== 技術面，畫 K 線圖 ====
                st.markdown(f"#### ★ {symbol} 盒鬚圖 + 移動平均線")
                fig = go.Figure()
                # 成交量移動平均
                # 成交量均線
                filtered_data["VolMA5"]  = filtered_data["volume"].rolling(5,  min_periods=1).mean()
                filtered_data["VolMA10"] = filtered_data["volume"].rolling(10, min_periods=1).mean()

                # 依漲跌著色（與你的 K 線顏色一致：收>=開 → 紅，上漲；否則綠）
                bar_colors = np.where(filtered_data["close"] >= filtered_data["open"], "red", "green")

                fig = make_subplots(
                    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f"{symbol} K 線與均線", "成交量（含均線）")
                )

                # ── 上方：K線
                fig.add_trace(
                    go.Candlestick(
                        x=filtered_data["date"],
                        open=filtered_data["open"],
                        high=filtered_data["high"],
                        low=filtered_data["low"],
                        close=filtered_data["close"],
                        name="K棒",
                        increasing_line_color="red",   # 依你原本設定
                        decreasing_line_color="green"
                    ),
                    row=1, col=1
                )

                # 均線
                for n, color in zip([5, 10, 20, 60], ["purple", "blue", "orange", "brown"]):
                    fig.add_trace(
                        go.Scatter(
                            x=filtered_data["date"],
                            y=filtered_data[f"MA{n}"],
                            name=f"MA{n}",
                            line=dict(color=color, width=1.5)
                        ),
                        row=1, col=1
                    )

                # ── 下方：成交量柱
                fig.add_trace(
                    go.Bar(
                        x=filtered_data["date"],
                        y=filtered_data["volume"],
                        name="成交量",
                        marker_color=bar_colors,
                        opacity=0.85
                    ),
                    row=2, col=1
                )

                # 成交量均線（虛線）
                fig.add_trace(
                    go.Scatter(
                        x=filtered_data["date"], y=filtered_data["VolMA5"],
                        name="成交量MA5", mode="lines",
                        line=dict(width=1.5, dash="dash")
                    ),
                    row=2, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=filtered_data["date"], y=filtered_data["VolMA10"],
                        name="成交量MA10", mode="lines",
                        line=dict(width=1.5, dash="dash")
                    ),
                    row=2, col=1
                )

                # 版面與座標
                fig.update_layout(
                    xaxis_rangeslider_visible=False,
                    hovermode="x unified",
                    height=720,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig.update_yaxes(title_text="價格", row=1, col=1)
                fig.update_yaxes(title_text="成交量", row=2, col=1)

                st.plotly_chart(fig, use_container_width=True)


                # ==== RSI(9,14) 圖 ====
                st.markdown("#### ★ RSI 指標（9 / 14）")
                fig2 = go.Figure()

                fig2.add_trace(go.Scatter(
                    x=filtered_data["date"], y=filtered_data["RSI9"],
                    name="RSI9", mode="lines"
                ))
                fig2.add_trace(go.Scatter(
                    x=filtered_data["date"], y=filtered_data["RSI14"],
                    name="RSI14", mode="lines"
                ))

                # 70/30 參考線
                fig2.add_hline(y=70, line_dash="dot")
                fig2.add_hline(y=30, line_dash="dot")

                fig2.update_yaxes(range=[0, 100], title_text="RSI")
                fig2.update_xaxes(title_text="日期")
                fig2.update_layout(height=320, hovermode="x unified",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

                st.plotly_chart(fig2, use_container_width=True)


                # ==== KD (K9 / D9) 圖 ====
                st.markdown("#### ★ KD 指標（K9 / D9）")
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(
                    x=filtered_data["date"], y=filtered_data["K9"],
                    name="K9", mode="lines"
                ))
                fig3.add_trace(go.Scatter(
                    x=filtered_data["date"], y=filtered_data["D9"],
                    name="D9", mode="lines"
                ))
                # 80 / 20 參考線
                fig3.add_hline(y=80, line_dash="dot")
                fig3.add_hline(y=20, line_dash="dot")

                fig3.update_yaxes(range=[0, 100], title_text="KD")
                fig3.update_xaxes(title_text="日期")
                fig3.update_layout(height=320, hovermode="x unified",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig3, use_container_width=True)


                # ==== MACD 圖 ====
                st.markdown("#### ★ MACD 指標（含 OSC 紅綠柱）")

                fig4 = go.Figure()

                # 紅綠柱 (OSC)：紅表示多方，綠表示空方
                osc_colors = np.where(filtered_data["OSC"] >= 0, "red", "green")
                fig4.add_trace(go.Bar(
                    x=filtered_data["date"],
                    y=filtered_data["OSC"],
                    name="OSC",
                    marker_color=osc_colors,
                    opacity=0.7
                ))

                # DIF / MACD 線
                fig4.add_trace(go.Scatter(
                    x=filtered_data["date"], y=filtered_data["DIF"],
                    name="DIF", mode="lines", line=dict(color="orange", width=1.5)
                ))
                fig4.add_trace(go.Scatter(
                    x=filtered_data["date"], y=filtered_data["MACD"],
                    name="MACD", mode="lines", line=dict(color="blue", width=1.5)
                ))

                fig4.update_layout(
                    height=320,
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig4.update_yaxes(title_text="MACD / OSC")
                fig4.update_xaxes(title_text="日期")

                st.plotly_chart(fig4, use_container_width=True)


                # ── 布林通道（上/中/下軌，彩色版）
                st.markdown("#### ★ 布林通道（上/中/下軌）")

                fig5 = go.Figure()

                # === 彩色陰影區（填滿上軌與下軌之間） ===
                fig5.add_trace(
                    go.Scatter(
                        x=filtered_data["date"],
                        y=filtered_data["BB_UPPER"],
                        name="BB Upper",
                        mode="lines",
                        line=dict(color="rgba(255,0,0,0.8)", width=1.2),  # 🔴 上軌紅線
                    )
                )
                fig5.add_trace(
                    go.Scatter(
                        x=filtered_data["date"],
                        y=filtered_data["BB_LOWER"],
                        name="BB Lower",
                        mode="lines",
                        line=dict(color="rgba(0,0,255,0.8)", width=1.2),  # 🔵 下軌藍線
                        fill="tonexty",  # 填滿與上一條線（上軌）之間
                        fillcolor="rgba(135,206,250,0.25)"  # 淡藍色陰影
                    )
                )

                # === 中軌線 ===
                fig5.add_trace(
                    go.Scatter(
                        x=filtered_data["date"],
                        y=filtered_data["BB_MID"],
                        name="BB Mid(20)",
                        mode="lines",
                        line=dict(color="orange", width=1.2, dash="dot")  # 🟠 中軌虛線
                    )
                )

                # === 收盤價線（方便對照） ===
                fig5.add_trace(
                    go.Scatter(
                        x=filtered_data["date"],
                        y=filtered_data["close"],
                        name="收盤價",
                        mode="lines",
                        line=dict(color="black", width=1.2)
                    )
                )

                fig5.update_layout(
                    height=360,
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    title_text=f"{symbol} 布林通道（BBands）"
                )
                fig5.update_yaxes(title_text="價格")
                fig5.update_xaxes(title_text="日期")

                st.plotly_chart(fig5, use_container_width=True)
                st.divider()
                

                # # ==== AI 基本面分析 ====
                # # bs
                # st.markdown("#### ★ AI 基本面_資產負債表分析")
                # with st.spinner("AI 資產負債表正在分析中..."):
                #     bs_text = generate_bs_insights(symbol, df_balance, openai_api_key, periods=8)
                # if bs_text:
                #     st.markdown(bs_text)
                # st.divider()
                    
                # # ci
                # st.markdown("#### ★ AI 基本面_損益表分析")
                # with st.spinner("AI 損益表正在分析中..."):
                #     is_text = generate_is_insights(symbol, df_income, openai_api_key, periods=8)
                # if is_text:
                #     st.markdown(is_text)
                # st.divider()
                    
                # # cfs
                # st.markdown("#### ★ AI 基本面分析_現金流量表")
                # with st.spinner("AI 現金流量表正在分析中..."):
                #     cf_text = generate_cf_insights(symbol, df_cash, openai_api_key, periods=8)
                # if cf_text:
                #     st.markdown(cf_text)
                # st.divider()
                
                # # 財務分析
                # st.markdown("#### ★ AI 財務核心指標分析")
                # with st.spinner("AI 財務核心指標正在分析中..."):
                #     core_text = generate_core_metrics_insights(symbol, core, openai_api_key, periods=8)
                # if core_text:
                #     st.markdown(core_text)
                # st.divider()



                # # ==== AI 技術面分析 ====
                # st.markdown("#### ★ AI 技術面分析")
                # with st.spinner("AI 技術面正在分析中..."):
                #     ai_text = generate_ai_insights(symbol, filtered_data, openai_api_key)
                # if ai_text:
                #     st.markdown(ai_text)
                #     # st.success("AI 技術面分析完成")
                # st.divider()


                # ==== 最近表格 ====
                st.subheader("最近10筆交易資料")
                disp = filtered_data.tail(10).sort_values("date", ascending=False).copy()
                disp["date"] = disp["date"].dt.strftime("%Y-%m-%d")
                disp = disp.rename(
                    columns={
                        "date": "日期",
                        "open": "開盤價",
                        "high": "最高價",
                        "low": "最低價",
                        "close": "收盤價",
                        "volume": "成交量",
                    }
                )
                st.dataframe(disp, use_container_width=True, hide_index=True)
                st.divider()
                
            with tab2:    
                # ==================== 四階段財報分析 ====================
                if df_enterprise is not None and not df_enterprise.empty:
                    latest_ent = df_enterprise.sort_values('date', ascending=False).iloc[0]
                    market_cap = latest_ent.get('marketCapitalization', None)
                else:
                    market_cap = None
        
                if company_profile:
                    st.markdown("#### ★ 公司簡介")
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.image(company_profile.get('image', ""), width=80)
                    with col2:
                        st.subheader(company_profile.get('companyName', ''))
                        st.write(f"產業類別：{company_profile.get('sector', '')}")
                        st.write(f"行業分類：{company_profile.get('industry', '')}")
                        st.write(f"CEO：{company_profile.get('ceo', '')}")
                        st.write(f"員工數：{company_profile.get('fullTimeEmployees', '')}")
                        st.write(f"創立日期：{company_profile.get('ipoDate', '')}")
                        st.write(f"公司網站：[點我前往]({company_profile.get('website', '')})")
                        st.write(company_profile.get('description', ''))
                st.divider()
                
                # if df_key_metrics is not None and not df_key_metrics.empty:
                #     km = df_key_metrics.iloc[0]  # 取最新一筆
                #     metrics_table = [
                #         {"指標": "市值",         "數值": format_large_number(km.get("marketCap"))},
                #         {"指標": "本益比",       "數值": f"{km.get('peRatio', None):.2f}" if km.get("peRatio") is not None else "N/A"},
                #         {"指標": "ROE",         "數值": f"{km.get('returnOnEquity', 0)*100:.2f}%"},
                #         {"指標": "ROA",         "數值": f"{km.get('returnOnAssets', 0)*100:.2f}%"},
                #         {"指標": "自由現金流殖利率", "數值": f"{km.get('freeCashFlowYield', 0)*100:.2f}%"},
                #         {"指標": "現金流品質",    "數值": f"{km.get('incomeQuality', 0):.2f}"},
                #         {"指標": "負債/權益比",   "數值": f"{km.get('debtToEquity', 0):.2f}"},
                #         {"指標": "流動比率",      "數值": f"{km.get('currentRatio', 0):.2f}"},
                #         {"指標": "資產周轉率",    "數值": f"{km.get('assetTurnover', 0):.2f}"},
                #         {"指標": "毛利率",        "數值": f"{km.get('grossProfitMargin', 0)*100:.2f}%"},
                #         {"指標": "淨利率",        "數值": f"{km.get('netProfitMargin', 0)*100:.2f}%"},
                #     ]
                #     # 建議用 pd.DataFrame 展示
                #     st.markdown("#### ★ 關鍵比率")
                #     st.dataframe(pd.DataFrame(metrics_table), use_container_width=True, hide_index=True)
                # st.divider()
                
                st.markdown("#### ★ 四階段財報分析")
                st.info("此分析整合資產負債表、損益表、現金流量表，提供專業的財務健康度評估")
                
                # df_enterprise
                if df_enterprise is not None and not df_enterprise.empty:
                    latest_ent = df_enterprise.sort_values('date', ascending=False).iloc[0]
                    market_cap = latest_ent.get('marketCapitalization', None)
                    # 或 enterprise_value = latest_ent.get('enterpriseValue', None)
                else:
                    market_cap = None
                                
                
                # 計算四階段分析
                with st.spinner("計算 Piotroski F-Score..."):
                    fscore = calculate_piotroski_fscore(df_income, df_balance, df_cash)
                
                with st.spinner("計算 Altman Z-Score..."):
                    zscore = calculate_altman_zscore(df_income, df_balance, market_cap)
                
                with st.spinner("計算杜邦分析..."):
                    dupont = calculate_dupont_analysis(df_income, df_balance)
                
                with st.spinner("計算現金流分析..."):
                    cashflow_analysis = calculate_cashflow_analysis(df_income, df_cash)
                
                # 顯示四階段分析結果
                if fscore:
                    st.markdown("#### ★ 階段一：Piotroski F-Score")
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # 獲利能力指標
                        st.write("**獲利能力指標**")
                        prof_df = pd.DataFrame(fscore['profitability'])
                        st.dataframe(
                            prof_df[['name', 'current', 'previous', 'score', 'status']].rename(columns={
                                'name': '指標',
                                'current': '當前值',
                                'previous': '前期值',
                                'score': '得分',
                                'status': '狀態'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # 槓桿與流動性指標
                        st.write("**槓桿與流動性指標**")
                        lev_df = pd.DataFrame(fscore['leverage'])
                        st.dataframe(
                            lev_df[['name', 'current', 'previous', 'score', 'status']].rename(columns={
                                'name': '指標',
                                'current': '當前值',
                                'previous': '前期值',
                                'score': '得分',
                                'status': '狀態'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # 營運效率指標
                        st.write("**營運效率指標**")
                        eff_df = pd.DataFrame(fscore['efficiency'])
                        st.dataframe(
                            eff_df[['name', 'current', 'previous', 'score', 'status']].rename(columns={
                                'name': '指標',
                                'current': '當前值',
                                'previous': '前期值',
                                'score': '得分',
                                'status': '狀態'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        # F-Score總分
                        total_score = fscore['total_score']
                        if total_score >= 7:
                            rating = "優秀 😊"
                        elif total_score >= 5:
                            rating = "良好 🙂"
                        elif total_score >= 3:
                            rating = "中等 😐"
                        else:
                            rating = "較弱 😰"
                        
                        st.metric("F-Score總分", f"{total_score}/9", rating)
                        
                        # 通過率圓餅圖
                        passed = total_score
                        failed = 9 - total_score
                        
                        fig_fscore = go.Figure(data=[go.Pie(
                            labels=['通過', '未通過'],
                            values=[passed, failed],
                            marker=dict(colors=['#2E8B57', '#DC143C']),
                            hole=0.3
                        )])
                        fig_fscore.update_layout(
                            title='F-Score通過率',
                            height=300
                        )
                        st.plotly_chart(fig_fscore, use_container_width=True)
                
                st.divider()
                
                # z-score
                if zscore:
                    st.markdown("#### ★ 階段二：Altman Z-Score")
                    col1, col2 = st.columns([2, 1])

                    st.write(
                        f"**Z-Score：** {zscore['z_score']:.2f}　　"
                        f"**風險等級：** {zscore['risk_level']} {zscore['risk_emoji']}"
                    )
                    
                    with col1:
                        st.write("**Z-Score 組成要素**")
                        z_components = pd.DataFrame([
                            {
                                '要素': 'A項：營運資本/總資產',
                                '比率值': f"{safe_divide(zscore['base_data']['working_capital'], zscore['base_data']['total_assets']):.4f}",
                                '權重後': f"{zscore['components']['A']:.4f}"
                            },
                            {
                                '要素': 'B項：保留盈餘/總資產',
                                '比率值': f"{safe_divide(zscore['base_data']['retained_earnings'], zscore['base_data']['total_assets']):.4f}",
                                '權重後': f"{zscore['components']['B']:.4f}"
                            },
                            {
                                '要素': 'C項：EBIT/總資產',
                                '比率值': f"{safe_divide(zscore['base_data']['ebit'], zscore['base_data']['total_assets']):.4f}",
                                '權重後': f"{zscore['components']['C']:.4f}"
                            },
                            {
                                '要素': 'D項：市值/總負債',
                                '比率值': f"{safe_divide(zscore['base_data']['market_cap'], zscore['base_data']['total_liabilities']):.4f}",
                                '權重後': f"{zscore['components']['D']:.4f}"
                            },
                            {
                                '要素': 'E項：營收/總資產',
                                '比率值': f"{safe_divide(zscore['base_data']['revenues'], zscore['base_data']['total_assets']):.4f}",
                                '權重後': f"{zscore['components']['E']:.4f}"
                            }
                        ])
                        st.dataframe(z_components, use_container_width=True, hide_index=True)
                    
                    with col2:
                        fig_zscore = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=zscore['z_score'],
                            title={'text': 'Z-Score'},
                            gauge={
                                'axis': {'range': [None, 5]},
                                'bar': {'color': "#4682B4"},
                                'steps': [
                                    {'range': [0, 1.81], 'color': "#DC143C"},
                                    {'range': [1.81, 2.99], 'color': "#DAA520"},
                                    {'range': [2.99, 5], 'color': "#2E8B57"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': zscore['z_score']
                                }
                            }
                        ))
                        fig_zscore.update_layout(height=320)
                        st.plotly_chart(fig_zscore, use_container_width=True)

                
                # 杜邦分析
                if dupont and dupont['yearly_analysis']:
                    st.markdown("#### ★ 階段三：杜邦分析")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # 年度杜邦分析
                        st.write("**年度杜邦分析**")
                        dupont_df = pd.DataFrame(dupont['yearly_analysis'])
                        dupont_df['date'] = pd.to_datetime(dupont_df['date']).dt.strftime('%Y-%m-%d')
                        display_dupont = dupont_df[[
                            'date', 'net_margin', 'asset_turnover', 
                            'equity_multiplier', 'direct_roe'
                        ]].rename(columns={
                            'date': '日期',
                            'net_margin': '淨利率',
                            'asset_turnover': '資產周轉率',
                            'equity_multiplier': '權益乘數',
                            'direct_roe': '直接ROE'
                        })
                        st.dataframe(display_dupont, use_container_width=True, hide_index=True)
                        
                        # 趨勢變化
                        if dupont['changes']:
                            st.write("**趨勢變化分析**")
                            changes_df = pd.DataFrame([
                                {
                                    '項目': '淨利率變化',
                                    '變化量': f"{dupont['changes']['net_margin_change']:.4f}"
                                },
                                {
                                    '項目': '資產周轉率變化',
                                    '變化量': f"{dupont['changes']['asset_turnover_change']:.4f}"
                                },
                                {
                                    '項目': '權益乘數變化',
                                    '變化量': f"{dupont['changes']['equity_multiplier_change']:.4f}"
                                },
                                {
                                    '項目': 'ROE變化',
                                    '變化量': f"{dupont['changes']['roe_change']:.4f}"
                                }
                            ])
                            st.dataframe(changes_df, use_container_width=True, hide_index=True)
                    
                    with col2:
                        # 當前ROE
                        current_roe = dupont['yearly_analysis'][0]['direct_roe']
                        st.metric("當前ROE", f"{current_roe:.2%}")
                
                st.divider()
                
                # 現金流分析
                if cashflow_analysis:
                    st.markdown("#### ★ 階段四：現金流分析")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # 現金流關鍵指標
                        st.write("**現金流關鍵指標**")
                        cf_metrics = pd.DataFrame([
                            {
                                '指標': '營運現金流品質比率',
                                '數值': f"{cashflow_analysis['ocf_quality']:.2f}"
                            },
                            {
                                '指標': '自由現金流',
                                '數值': format_large_number(cashflow_analysis['free_cashflow'])
                            },
                            {
                                '指標': '現金流品質評估',
                                '數值': f"{cashflow_analysis['quality_assessment']} {cashflow_analysis['quality_emoji']}"
                            }
                        ])
                        st.dataframe(cf_metrics, use_container_width=True, hide_index=True)
                        
                        # 現金流結構
                        st.write("**現金流結構分析**")
                        structure_df = pd.DataFrame([
                            {
                                '類型': '營運現金流',
                                '金額': format_large_number(cashflow_analysis['structure']['operating'])
                            },
                            {
                                '類型': '投資現金流',
                                '金額': format_large_number(cashflow_analysis['structure']['investing'])
                            },
                            {
                                '類型': '融資現金流',
                                '金額': format_large_number(cashflow_analysis['structure']['financing'])
                            }
                        ])
                        st.dataframe(structure_df, use_container_width=True, hide_index=True)
                    
                    with col2:
                        # 現金流品質指標
                        st.metric(
                            "現金流品質比率",
                            f"{cashflow_analysis['ocf_quality']:.2f}",
                            f"{cashflow_analysis['quality_assessment']} {cashflow_analysis['quality_emoji']}"
                        )
                
                st.divider()
                
                # AI 四階段分析解讀
                st.markdown("#### ★ AI 四階段財報分析解讀")
                if fscore and zscore and dupont and cashflow_analysis:
                    with st.spinner("AI 正在進行四階段財報分析..."):
                        four_stage_ai_text = generate_four_stage_ai_analysis(
                            symbol, fscore, zscore, dupont, cashflow_analysis, openai_api_key
                        )
                    if four_stage_ai_text:
                        st.markdown(four_stage_ai_text)
                else:
                    st.warning("部分四階段分析數據不足，無法進行完整的 AI 解讀")
                    
            with tab3:
                # ==== AI 基本面分析 ====
                # bs
                st.markdown("#### ★ AI 基本面_資產負債表分析")
                with st.spinner("AI 資產負債表正在分析中..."):
                    bs_text = generate_bs_insights(symbol, df_balance, openai_api_key, periods=8)
                if bs_text:
                    st.markdown(bs_text)
                st.divider()
                    
                # ci
                st.markdown("#### ★ AI 基本面_損益表分析")
                with st.spinner("AI 損益表正在分析中..."):
                    is_text = generate_is_insights(symbol, df_income, openai_api_key, periods=8)
                if is_text:
                    st.markdown(is_text)
                st.divider()
                    
                # cfs
                st.markdown("#### ★ AI 基本面分析_現金流量表")
                with st.spinner("AI 現金流量表正在分析中..."):
                    cf_text = generate_cf_insights(symbol, df_cash, openai_api_key, periods=8)
                if cf_text:
                    st.markdown(cf_text)
                st.divider()
                
                # 財務分析
                st.markdown("#### ★ AI 財務核心指標分析")
                with st.spinner("AI 財務核心指標正在分析中..."):
                    core_text = generate_core_metrics_insights(symbol, core, openai_api_key, periods=8)
                if core_text:
                    st.markdown(core_text)
                st.divider()



                # ==== AI 技術面分析 ====
                st.markdown("#### ★ AI 技術面分析")
                with st.spinner("AI 技術面正在分析中..."):
                    ai_text = generate_ai_insights(symbol, filtered_data, openai_api_key)
                if ai_text:
                    st.markdown(ai_text)
                    # st.success("AI 技術面分析完成")
                st.divider()


                    

    if __name__ == "__main__":
        main()
