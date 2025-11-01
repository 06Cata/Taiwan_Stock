import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from plotly.subplots import make_subplots

from pages.profolios_personal_subpages.tw_stock_ai_insight import (
    # API 資料獲取
    get_balance_ratios, get_income_ratios, get_cashflow_ratios, get_stock_data,
    get_company_profile, get_company_per,
    # 財務計算（仍保留核心與技術）
    compute_core_cross_metrics_from_frames, filter_by_date_range,
    # 技術指標
    get_moving_averages, add_rsi, add_kd, add_macd, add_bbands,
    # 
    safe_divide, format_large_number, 
    calculate_market_cap, calculate_piotroski_fscore, calculate_altman_zscore, 
    calculate_dupont_analysis, calculate_cashflow_analysis, 
    # AI 分析
    generate_bs_insights, generate_is_insights, generate_cf_insights,
    generate_core_metrics_insights, generate_ai_insights, generate_four_stage_ai_analysis
)


# ==================== 頁面設定 ====================
def main():
    st.subheader("台股AI智能分析 TW Stock AI Insight")
    st.write("""
        請自行申請 **FinMind API Token** 與 **OpenAI API Key**，
        系統會根據 **技術面** 與 **基本面** 資料，
        生成由 AI 撰寫的分析報告（僅供參考，不構成投資建議）
    """)

    # ==================== 頂部輸入表單 ====================
    with st.form("top_controls", clear_on_submit=False):
        st.markdown("###### 分析設定")

        c1, c2, c3 = st.columns([1.2, 1.2, 1])
        with c1:
            stock_id = st.text_input("股票代碼 (台股)", value="2330", help="例如：2330 (台積電)")
        with c2:
            finmind_token = st.text_input(
                "FinMind API Token", type="password", value=os.getenv("FINMIND_TOKEN", ""),
                help="可選，有 token 可獲取更多歷史資料"
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
        if not stock_id or not openai_api_key:
            st.error("❌ 請完整輸入股票代碼與 OpenAI API Key")
            st.stop()
        if start_date >= end_date:
            st.error("❌ 起始日期必須早於結束日期")
            st.stop()

        stock_id = stock_id.strip()

        # === 獲取股價資料 ===
        with st.spinner(f"正在獲取 {stock_id} 股價資料..."):
            stock_data = get_stock_data(finmind_token, stock_id)  # 一定回傳 DataFrame

        if stock_data.empty:
            st.error(f"❌ 無法獲取 {stock_id} 的股價資料，請檢查股票代碼")
            st.stop()

        with st.spinner("篩選日期範圍..."):
            filtered_data = filter_by_date_range(stock_data, start_date, end_date)

        if filtered_data is None or filtered_data.empty:
            st.stop()

        # === 獲取財報資料 ===
        with st.spinner("計算資產負債表指標..."):
            df_balance = get_balance_ratios(finmind_token, stock_id)

        with st.spinner("計算損益表指標..."):
            df_income = get_income_ratios(finmind_token, stock_id)

        with st.spinner("計算現金流量表指標..."):
            df_cash = get_cashflow_ratios(finmind_token, stock_id)

        with st.spinner("計算財務核心指標..."):
            core = compute_core_cross_metrics_from_frames(df_income, df_balance, df_cash)

        # === 獲取公司基本資料 ===
        with st.spinner("獲取公司基本資料..."):
            company_profile_df = get_company_profile(finmind_token, stock_id)  
            pbr_df = get_company_per(finmind_token, stock_id)  
             
        # === 計算技術指標 ===
        with st.spinner("計算技術指標..."):
            filtered_data = get_moving_averages(filtered_data)
            filtered_data = add_rsi(filtered_data)
            filtered_data = add_kd(filtered_data, period=9, k_smooth=3, d_smooth=3)
            filtered_data = add_macd(filtered_data)
            filtered_data = add_bbands(filtered_data, window=20, num_std=2.0)
        
        
        # ==================== 分頁顯示 ====================
        tab1, tab2, tab3 = st.tabs(["1 - 基本面、技術面分析", "2 - 公司財務評價", "3 - AI分析"])

        # ------------- Tab 1 -------------
        with tab1:
            # 基本統計
            st.markdown("### ★ 統計")
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

            # 資產負債表趨勢
            if df_balance is not None and not df_balance.empty:
                st.markdown("### ★ 資產負債表趨勢")
                dfb = df_balance.copy()
                dfb["date"] = pd.to_datetime(dfb["date"])
                dfb = dfb.sort_values("date")

                # 規模
                fig_bs_size = go.Figure()
                if "TotalAssets" in dfb.columns:
                    fig_bs_size.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["TotalAssets"], name="總資產", mode="lines+markers", line=dict(width=2)))
                if "Liabilities" in dfb.columns:
                    fig_bs_size.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["Liabilities"], name="總負債", mode="lines+markers", line=dict(width=2)))
                if "Equity" in dfb.columns:
                    fig_bs_size.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["Equity"], name="股東權益", mode="lines+markers", line=dict(width=2)))
                fig_bs_size.update_layout(height=360, hovermode="x unified", title=f"{stock_id} 資產 / 負債 / 股東權益（規模）",
                                          legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_bs_size.update_yaxes(title_text="金額（TWD）", rangemode="tozero")
                fig_bs_size.update_xaxes(title_text="季度")
                st.plotly_chart(fig_bs_size, use_container_width=True)

                # 償債能力
                fig_bs_liquidity = go.Figure()
                if "current_ratio" in dfb.columns:
                    fig_bs_liquidity.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["current_ratio"], name="流動比率", mode="lines+markers"))
                if "quick_ratio" in dfb.columns:
                    fig_bs_liquidity.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["quick_ratio"], name="速動比率", mode="lines+markers"))
                if "cash_ratio" in dfb.columns:
                    fig_bs_liquidity.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["cash_ratio"], name="現金比率", mode="lines+markers"))
                fig_bs_liquidity.update_layout(height=320, hovermode="x unified", title=f"{stock_id} 償債能力指標",
                                               legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_bs_liquidity.update_yaxes(title_text="倍數（x）", rangemode="tozero")
                fig_bs_liquidity.update_xaxes(title_text="季度")
                st.plotly_chart(fig_bs_liquidity, use_container_width=True)

                # 槓桿結構
                fig_bs_leverage = go.Figure()
                if "debt_ratio" in dfb.columns:
                    fig_bs_leverage.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["debt_ratio"], name="負債比率", mode="lines+markers"))
                if "equity_ratio" in dfb.columns:
                    fig_bs_leverage.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["equity_ratio"], name="權益比率", mode="lines+markers"))
                if "debt_to_equity" in dfb.columns:
                    fig_bs_leverage.add_trace(go.Scatter(x=dfb["quarter_label"], y=dfb["debt_to_equity"], name="負債權益比", mode="lines+markers"))
                fig_bs_leverage.update_layout(height=340, hovermode="x unified", title=f"{stock_id} 槓桿結構指標",
                                              legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_bs_leverage.update_yaxes(title_text="比例", rangemode="tozero")
                fig_bs_leverage.update_xaxes(title_text="季度")
                st.plotly_chart(fig_bs_leverage, use_container_width=True)

                st.markdown("##### 近期財務比率一覽")
                show_cols = [c for c in ["date", "quarter_label", "current_ratio", "quick_ratio", "cash_ratio",
                                         "debt_ratio", "equity_ratio", "debt_to_equity", "net_debt_ratio"] if c in dfb.columns]
                if show_cols:
                    display_df = dfb[show_cols].tail(6).reset_index(drop=True)
                    display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%Y-%m-%d")
                    st.dataframe(display_df, use_container_width=True)

            st.divider()

            # 損益表趨勢
            if df_income is not None and not df_income.empty:
                st.markdown("### ★ 損益表趨勢")
                dfi = df_income.copy()
                dfi["date"] = pd.to_datetime(dfi["date"])
                dfi = dfi.sort_values("date")

                fig_is_scale = go.Figure()
                if "revenue" in dfi.columns:
                    fig_is_scale.add_trace(go.Scatter(x=dfi["quarter_label"], y=dfi["revenue"], name="營收", mode="lines+markers"))
                if "grossProfit" in dfi.columns:
                    fig_is_scale.add_trace(go.Scatter(x=dfi["quarter_label"], y=dfi["grossProfit"], name="毛利", mode="lines+markers"))
                if "operatingIncome" in dfi.columns:
                    fig_is_scale.add_trace(go.Scatter(x=dfi["quarter_label"], y=dfi["operatingIncome"], name="營業利益", mode="lines+markers"))
                if "netIncome" in dfi.columns:
                    fig_is_scale.add_trace(go.Scatter(x=dfi["quarter_label"], y=dfi["netIncome"], name="淨利", mode="lines+markers"))
                fig_is_scale.update_layout(height=360, hovermode="x unified", title=f"{stock_id} 規模（Scale）",
                                           legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_is_scale.update_yaxes(title_text="金額（TWD）", rangemode="tozero")
                fig_is_scale.update_xaxes(title_text="季度")
                st.plotly_chart(fig_is_scale, use_container_width=True)

                fig_is_margin = go.Figure()
                if "gross_margin" in dfi.columns:
                    fig_is_margin.add_trace(go.Scatter(x=dfi["quarter_label"], y=dfi["gross_margin"], name="毛利率", mode="lines+markers"))
                if "operating_margin" in dfi.columns:
                    fig_is_margin.add_trace(go.Scatter(x=dfi["quarter_label"], y=dfi["operating_margin"], name="營業利益率", mode="lines+markers"))
                if "net_margin" in dfi.columns:
                    fig_is_margin.add_trace(go.Scatter(x=dfi["quarter_label"], y=dfi["net_margin"], name="淨利率", mode="lines+markers"))
                fig_is_margin.update_layout(height=320, hovermode="x unified", title=f"{stock_id} 獲利能力",
                                            legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_is_margin.update_yaxes(title_text="比例", rangemode="tozero")
                fig_is_margin.update_xaxes(title_text="季度")
                st.plotly_chart(fig_is_margin, use_container_width=True)
                
                fig_is_eps = go.Figure()
                if "eps" in dfi.columns:
                    fig_is_eps.add_trace(go.Scatter(x=dfi["quarter_label"], y=dfi["eps"], name="EPS", mode="lines+markers"))
                fig_is_eps.update_layout(height=320, hovermode="x unified", title=f"{stock_id} EPS",
                                            legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_is_eps.update_yaxes(title_text="比例", rangemode="tozero")
                fig_is_eps.update_xaxes(title_text="季度")
                st.plotly_chart(fig_is_eps, use_container_width=True)

                st.markdown("#### 近期損益一覽")
                display_dfi = dfi.tail(8).copy()
                if "date" in display_dfi.columns:
                    display_dfi["date"] = pd.to_datetime(display_dfi["date"]).dt.strftime("%Y-%m-%d")
                st.dataframe(display_dfi, use_container_width=True)

            st.divider()

            # 現金流量表趨勢
            if df_cash is not None and not df_cash.empty:
                st.markdown("### ★ 現金流量表趨勢")

                dfc = df_cash.copy()
                dfc["date"] = pd.to_datetime(dfc["date"])
                dfc = dfc.sort_values("date")

                fig_cf_core = go.Figure()
                if "OCF" in dfc.columns:
                    fig_cf_core.add_trace(go.Bar(x=dfc["quarter_label"], y=dfc["OCF"], name="營運現金流"))
                if "CFI" in dfc.columns:
                    fig_cf_core.add_trace(go.Bar(x=dfc["quarter_label"], y=dfc["CFI"], name="投資現金流"))
                if "CFF" in dfc.columns:
                    fig_cf_core.add_trace(go.Bar(x=dfc["quarter_label"], y=dfc["CFF"], name="融資現金流"))
                fig_cf_core.update_layout(barmode="group", height=360, hovermode="x unified",
                                          title=f"{stock_id} OCF / CFI / CFF",
                                          legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_cf_core.update_yaxes(title_text="金額（TWD）", zeroline=True, zerolinewidth=1)
                fig_cf_core.update_xaxes(title_text="季度")
                st.plotly_chart(fig_cf_core, use_container_width=True)

                fig_cf_fcf = go.Figure()
                if "FCF" in dfc.columns:
                    fig_cf_fcf.add_trace(go.Scatter(x=dfc["quarter_label"], y=dfc["FCF"], name="自由現金流", mode="lines+markers"))
                if "CapEx" in dfc.columns:
                    fig_cf_fcf.add_trace(go.Scatter(x=dfc["quarter_label"], y=dfc["CapEx"], name="資本支出", mode="lines+markers"))
                fig_cf_fcf.update_layout(height=320, hovermode="x unified", title=f"{stock_id} FCF 與 CapEx",
                                         legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_cf_fcf.update_yaxes(title_text="金額（TWD）")
                fig_cf_fcf.update_xaxes(title_text="季度")
                st.plotly_chart(fig_cf_fcf, use_container_width=True)

                st.markdown("#### 近期現金流摘要")
                display_dfc = dfc.tail(8).copy()
                if "date" in display_dfc.columns:
                    display_dfc["date"] = pd.to_datetime(display_dfc["date"]).dt.strftime("%Y-%m-%d")
                st.dataframe(display_dfc, use_container_width=True)

            st.divider()

            # 財務核心指標
            if core is not None and not core.empty:
                st.markdown("### ★ 財務核心指標")
                core["date"] = pd.to_datetime(core["date"])
                core = core.sort_values("date")

                fig_core_roe_roa = go.Figure()
                if "ROE" in core.columns:
                    fig_core_roe_roa.add_trace(go.Scatter(x=core["quarter_label"], y=core["ROE"], name="ROE", mode="lines+markers"))
                if "ROA" in core.columns:
                    fig_core_roe_roa.add_trace(go.Scatter(x=core["quarter_label"], y=core["ROA"], name="ROA", mode="lines+markers"))
                fig_core_roe_roa.update_layout(height=300, hovermode="x unified", title=f"{stock_id} ROE / ROA",
                                               legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_core_roe_roa.update_yaxes(title_text="比率(%)", rangemode="tozero")
                fig_core_roe_roa.update_xaxes(title_text="季度")
                st.plotly_chart(fig_core_roe_roa, use_container_width=True)

                fig_core_turnover = go.Figure()
                if "asset_turnover" in core.columns:
                    fig_core_turnover.add_trace(go.Scatter(x=core["quarter_label"], y=core["asset_turnover"], name="資產週轉率", mode="lines+markers"))
                fig_core_turnover.update_layout(height=280, hovermode="x unified", title=f"{stock_id} 資產週轉率",
                                                legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_core_turnover.update_yaxes(title_text="倍數", rangemode="tozero")
                fig_core_turnover.update_xaxes(title_text="季度")
                st.plotly_chart(fig_core_turnover, use_container_width=True)

                fig_core_cash = go.Figure()
                if "cash_conversion" in core.columns:
                    fig_core_cash.add_trace(go.Scatter(x=core["quarter_label"], y=core["cash_conversion"], name="現金轉換率", mode="lines+markers"))
                if "fcf_margin" in core.columns:
                    fig_core_cash.add_trace(go.Scatter(x=core["quarter_label"], y=core["fcf_margin"], name="FCF Margin", mode="lines+markers"))
                fig_core_cash.update_layout(height=280, hovermode="x unified", title=f"{stock_id} 現金品質",
                                            legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=11)))
                fig_core_cash.update_yaxes(title_text="比率", rangemode="tozero")
                fig_core_cash.update_xaxes(title_text="季度")
                st.plotly_chart(fig_core_cash, use_container_width=True)

                st.markdown("#### 近期財務核心指標")
                show_cols = [c for c in ["date", "quarter_label", "ROE", "ROA", "asset_turnover", "cash_conversion", "fcf_margin"] if c in core.columns]
                if show_cols:
                    display_core = core[show_cols].tail(8).reset_index(drop=True)
                    if "date" in display_core.columns:
                        display_core["date"] = pd.to_datetime(display_core["date"]).dt.strftime("%Y-%m-%d")
                    st.dataframe(display_core, use_container_width=True)

            st.divider()

            # 技術面圖表（K、RSI、KD、MACD、BB）
            st.markdown(f"### ★ {stock_id} K 線圖 + 移動平均線")
            filtered_data["VolMA5"] = filtered_data["volume"].rolling(5, min_periods=1).mean()
            filtered_data["VolMA10"] = filtered_data["volume"].rolling(10, min_periods=1).mean()
            bar_colors = np.where(filtered_data["close"] >= filtered_data["open"], "red", "green")

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.7, 0.3],
                                subplot_titles=(f"{stock_id} K線與均線", "成交量（含均線）"))
            fig.add_trace(go.Candlestick(x=filtered_data["date"], open=filtered_data["open"], high=filtered_data["high"],
                                         low=filtered_data["low"], close=filtered_data["close"], name="K棒",
                                         increasing_line_color="red", decreasing_line_color="green"),
                          row=1, col=1)
            for n, color in zip([5, 10, 20, 60], ["purple", "blue", "orange", "brown"]):
                if f"MA{n}" in filtered_data.columns:
                    fig.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data[f"MA{n}"], name=f"MA{n}", line=dict(color=color, width=1.5)), row=1, col=1)
            fig.add_trace(go.Bar(x=filtered_data["date"], y=filtered_data["volume"], name="成交量", marker_color=bar_colors, opacity=0.85), row=2, col=1)
            fig.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["VolMA5"], name="成交量MA5", mode="lines", line=dict(width=1.5, dash="dash")), row=2, col=1)
            fig.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["VolMA10"], name="成交量MA10", mode="lines", line=dict(width=1.5, dash="dash")), row=2, col=1)
            fig.update_layout(xaxis_rangeslider_visible=False, hovermode="x unified", height=720,
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_yaxes(title_text="價格", row=1, col=1)
            fig.update_yaxes(title_text="成交量", row=2, col=1)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### ★ RSI 指標（9 / 14）")
            fig2 = go.Figure()
            if "RSI9" in filtered_data.columns:
                fig2.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["RSI9"], name="RSI9", mode="lines"))
            if "RSI14" in filtered_data.columns:
                fig2.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["RSI14"], name="RSI14", mode="lines"))
            fig2.add_hline(y=70, line_dash="dot")
            fig2.add_hline(y=30, line_dash="dot")
            fig2.update_yaxes(range=[0, 100], title_text="RSI")
            fig2.update_xaxes(title_text="日期")
            fig2.update_layout(height=320, hovermode="x unified",
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("### ★ KD 指標（K9 / D9）")
            fig3 = go.Figure()
            if "K9" in filtered_data.columns:
                fig3.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["K9"], name="K9", mode="lines"))
            if "D9" in filtered_data.columns:
                fig3.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["D9"], name="D9", mode="lines"))
            fig3.add_hline(y=80, line_dash="dot")
            fig3.add_hline(y=20, line_dash="dot")
            fig3.update_yaxes(range=[0, 100], title_text="KD")
            fig3.update_xaxes(title_text="日期")
            fig3.update_layout(height=320, hovermode="x unified",
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown("### ★ MACD 指標（含 OSC 紅綠柱）")
            fig4 = go.Figure()
            if "OSC" in filtered_data.columns:
                osc_colors = np.where(filtered_data["OSC"] >= 0, "red", "green")
                fig4.add_trace(go.Bar(x=filtered_data["date"], y=filtered_data["OSC"], name="OSC", marker_color=osc_colors, opacity=0.7))
            if "DIF" in filtered_data.columns:
                fig4.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["DIF"], name="DIF", mode="lines", line=dict(color="orange", width=1.5)))
            if "MACD" in filtered_data.columns:
                fig4.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["MACD"], name="MACD", mode="lines", line=dict(color="blue", width=1.5)))
            fig4.update_layout(height=320, hovermode="x unified",
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig4.update_yaxes(title_text="MACD / OSC")
            fig4.update_xaxes(title_text="日期")
            st.plotly_chart(fig4, use_container_width=True)

            st.markdown("### ★ 布林通道（上/中/下軌）")
            fig5 = go.Figure()
            if "BB_UPPER" in filtered_data.columns:
                fig5.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["BB_UPPER"], name="BB Upper", mode="lines",
                                          line=dict(color="rgba(255,0,0,0.8)", width=1.2)))
            if "BB_LOWER" in filtered_data.columns:
                fig5.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["BB_LOWER"], name="BB Lower", mode="lines",
                                          line=dict(color="rgba(0,0,255,0.8)", width=1.2), fill="tonexty", fillcolor="rgba(135,206,250,0.25)"))
            if "BB_MID" in filtered_data.columns:
                fig5.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["BB_MID"], name="BB Mid(20)", mode="lines",
                                          line=dict(color="orange", width=1.2, dash="dot")))
            fig5.add_trace(go.Scatter(x=filtered_data["date"], y=filtered_data["close"], name="收盤價", mode="lines", line=dict(color="black", width=1.2)))
            fig5.update_layout(height=360, hovermode="x unified",
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                               title_text=f"{stock_id} 布林通道")
            fig5.update_yaxes(title_text="價格")
            fig5.update_xaxes(title_text="日期")
            st.plotly_chart(fig5, use_container_width=True)

            st.divider()

            # 最近交易資料表格
            st.markdown("### 最近10筆交易資料")
            disp = filtered_data.tail(10).sort_values("date", ascending=False).copy()
            disp["date"] = disp["date"].dt.strftime("%Y-%m-%d")
            disp = disp.rename(columns={"date": "日期", "open": "開盤價", "high": "最高價", "low": "最低價", "close": "收盤價", "volume": "成交量"})
            st.dataframe(disp, use_container_width=True, hide_index=True)

        # ------------- Tab 2 -------------
        with tab2:
            if company_profile_df is not None and not company_profile_df.empty:
                st.markdown("### ★ 公司簡介")
                row = company_profile_df.iloc[0]
                code = row.get("stock_id", "")
                name = row.get("stock_name", row.get("company_name", ""))
                st.write(f"**股票代碼：** {code}")
                st.write(f"**公司名稱：** {name}")
            
            st.divider()
            
            # ===== 四階段財報分析 =====
            st.markdown("### ★ 四階段財報分析")
            st.info("此分析整合最新4季 vs 前4季的年度比較，提供財務健康度評估")
            
            # 計算市值（用於 Z-Score）
            market_cap = calculate_market_cap(df_balance, pbr_df)
            
            # === 計算四階段分析 ===
            with st.spinner("計算 Piotroski F-Score..."):
                fscore = calculate_piotroski_fscore(df_income, df_balance, df_cash)
            
            with st.spinner("計算 Altman Z-Score..."):
                zscore = calculate_altman_zscore(df_income, df_balance, market_cap)
            
            with st.spinner("計算杜邦分析..."):
                dupont = calculate_dupont_analysis(df_income, df_balance)
            
            with st.spinner("計算現金流分析..."):
                cashflow_analysis = calculate_cashflow_analysis(df_income, df_cash)
            
            # === 顯示結果 ===
            if fscore:
                st.markdown("#### ★ 階段一：Piotroski F-Score")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**獲利能力指標**")
                    prof_df = pd.DataFrame(fscore['profitability_scores'])
                    st.dataframe(prof_df[['name', 'current', 'previous', 'score', 'status']].rename(columns={
                        'name': '指標', 'current': '當前值', 'previous': '前期值', 'score': '得分', 'status': '狀態'
                    }), use_container_width=True, hide_index=True)
                    
                    st.write("**槓桿與流動性指標**")
                    lev_df = pd.DataFrame(fscore['leverage_scores'])
                    st.dataframe(lev_df[['name', 'current', 'previous', 'score', 'status']].rename(columns={
                        'name': '指標', 'current': '當前值', 'previous': '前期值', 'score': '得分', 'status': '狀態'
                    }), use_container_width=True, hide_index=True)
                    
                    st.write("**營運效率指標**")
                    eff_df = pd.DataFrame(fscore['efficiency_scores'])
                    st.dataframe(eff_df[['name', 'current', 'previous', 'score', 'status']].rename(columns={
                        'name': '指標', 'current': '當前值', 'previous': '前期值', 'score': '得分', 'status': '狀態'
                    }), use_container_width=True, hide_index=True)
                
                with col2:
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
                    
                    # 圓餅圖
                    passed = total_score
                    failed = 9 - total_score
                    fig_fscore = go.Figure(data=[go.Pie(
                        labels=['通過', '未通過'],
                        values=[passed, failed],
                        marker=dict(colors=['#2E8B57', '#DC143C']),
                        hole=0.3
                    )])
                    fig_fscore.update_layout(title='F-Score通過率', height=300)
                    st.plotly_chart(fig_fscore, use_container_width=True)
            
            st.divider()
            
            if zscore:
                st.markdown("#### ★ 階段二：Altman Z-Score")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write("**Z-Score 組成要素**")
                    z_components = pd.DataFrame([
                        {'要素': 'A項：營運資本/總資產', '比率值': f"{safe_divide(zscore['base_data']['working_capital'], zscore['base_data']['total_assets']):.4f}", '權重後': f"{zscore['components']['A']:.4f}"},
                        {'要素': 'B項：保留盈餘/總資產', '比率值': f"{safe_divide(zscore['base_data']['retained_earnings'], zscore['base_data']['total_assets']):.4f}", '權重後': f"{zscore['components']['B']:.4f}"},
                        {'要素': 'C項：EBIT/總資產', '比率值': f"{safe_divide(zscore['base_data']['ebit'], zscore['base_data']['total_assets']):.4f}", '權重後': f"{zscore['components']['C']:.4f}"},
                        {'要素': 'D項：市值/總負債', '比率值': f"{safe_divide(zscore['base_data']['market_cap'], zscore['base_data']['total_liabilities']):.4f}", '權重後': f"{zscore['components']['D']:.4f}"},
                        {'要素': 'E項：營收/總資產', '比率值': f"{safe_divide(zscore['base_data']['revenues'], zscore['base_data']['total_assets']):.4f}", '權重後': f"{zscore['components']['E']:.4f}"},
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
                        }
                    ))
                    fig_zscore.update_layout(height=320)
                    st.plotly_chart(fig_zscore, use_container_width=True)
                    
                
                st.write(f"**Z-Score：** {zscore['z_score']:.2f}　　**風險等級：** {zscore['risk_level']} {zscore['risk_emoji']}")
            
            st.divider()
            
            if dupont and dupont['yearly_analysis']:
                st.markdown("#### ★ 階段三：杜邦分析")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**杜邦分析**")
                    st.caption("數據為滾動4季（TTM）年度化計算，日期為該年度最後一季")
                    dupont_df = pd.DataFrame(dupont['yearly_analysis'])
                    if 'date' in dupont_df.columns:
                        dupont_df['date'] = pd.to_datetime(dupont_df['date']).dt.strftime('%Y-%m-%d')
                    display_dupont = dupont_df[['date', 'net_margin', 'asset_turnover', 'equity_multiplier', 'direct_roe']].rename(columns={
                        'date': '日期', 'net_margin': '淨利率', 'asset_turnover': '資產週轉率', 'equity_multiplier': '權益乘數', 'direct_roe': '直接ROE'
                    })
                    st.dataframe(display_dupont, use_container_width=True, hide_index=True)
                    
                    if dupont['changes']:
                        st.write("**趨勢變化分析**")
                        changes_df = pd.DataFrame([
                            {'項目': '淨利率變化', '變化量': f"{dupont['changes']['net_margin_change']:.4f}"},
                            {'項目': '資產週轉率變化', '變化量': f"{dupont['changes']['asset_turnover_change']:.4f}"},
                            {'項目': '權益乘數變化', '變化量': f"{dupont['changes']['equity_multiplier_change']:.4f}"},
                            {'項目': 'ROE變化', '變化量': f"{dupont['changes']['roe_change']:.4f}"},
                        ])
                        st.dataframe(changes_df, use_container_width=True, hide_index=True)
                
                with col2:
                    current_roe = dupont['yearly_analysis'][0]['direct_roe']
                    st.metric("當前ROE", f"{current_roe:.2%}")
            
            st.divider()
            
            if cashflow_analysis:
                st.markdown("#### ★ 階段四：現金流分析")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**現金流關鍵指標**")
                    cf_metrics = pd.DataFrame([
                        {'指標': '營運現金流品質比率', '數值': f"{cashflow_analysis['ocf_quality']:.2f}"},
                        {'指標': '自由現金流', '數值': format_large_number(cashflow_analysis['free_cashflow'])},
                        {'指標': '現金流品質評估', '數值': f"{cashflow_analysis['quality_assessment']} {cashflow_analysis['quality_emoji']}"},
                    ])
                    st.dataframe(cf_metrics, use_container_width=True, hide_index=True)
                    
                    st.write("**現金流結構分析**")
                    structure_df = pd.DataFrame([
                        {'類型': '營運現金流', '金額': format_large_number(cashflow_analysis['structure']['operating'])},
                        {'類型': '投資現金流', '金額': format_large_number(cashflow_analysis['structure']['investing'])},
                        {'類型': '融資現金流', '金額': format_large_number(cashflow_analysis['structure']['financing'])},
                    ])
                    st.dataframe(structure_df, use_container_width=True, hide_index=True)
                
                with col2:
                    st.metric("現金流品質比率", f"{cashflow_analysis['ocf_quality']:.2f}", 
                            f"{cashflow_analysis['quality_assessment']} {cashflow_analysis['quality_emoji']}")
            
            st.divider()
            
            # === AI 四階段綜合分析 ===
            st.markdown("#### ★ AI 四階段財報分析解讀")
            if fscore and zscore and dupont and cashflow_analysis:
                with st.spinner("AI 正在進行四階段財報分析..."):
                    four_stage_ai_text = generate_four_stage_ai_analysis(
                        stock_id, fscore, zscore, dupont, cashflow_analysis, openai_api_key
                    )
                if four_stage_ai_text:
                    st.markdown(four_stage_ai_text)
            else:
                st.warning("部分四階段分析數據不足，無法進行完整的 AI 解讀")
                
                

        # ------------- Tab 3 -------------
        with tab3:
            if df_balance is not None and not df_balance.empty:
                st.markdown("### ★ AI 基本面_資產負債表分析")
                with st.spinner("AI 資產負債表正在分析中..."):
                    bs_text = generate_bs_insights(stock_id, df_balance, openai_api_key, periods=8)
                if bs_text:
                    st.markdown(bs_text)
                st.divider()

            if df_income is not None and not df_income.empty:
                st.markdown("### ★ AI 基本面_損益表分析")
                with st.spinner("AI 損益表正在分析中..."):
                    is_text = generate_is_insights(stock_id, df_income, openai_api_key, periods=8)
                if is_text:
                    st.markdown(is_text)
                st.divider()

            if df_cash is not None and not df_cash.empty:
                st.markdown("### ★ AI 基本面_現金流量表分析")
                with st.spinner("AI 現金流量表正在分析中..."):
                    cf_text = generate_cf_insights(stock_id, df_cash, openai_api_key, periods=8)
                if cf_text:
                    st.markdown(cf_text)
                st.divider()

            if core is not None and not core.empty:
                st.markdown("### ★ AI 財務核心指標分析")
                with st.spinner("AI 財務核心指標正在分析中..."):
                    core_text = generate_core_metrics_insights(stock_id, core, openai_api_key, periods=8)
                if core_text:
                    st.markdown(core_text)
                st.divider()

            st.markdown("### ★ AI 技術面分析")
            with st.spinner("AI 技術面正在分析中..."):
                ai_text = generate_ai_insights(stock_id, filtered_data, openai_api_key)
            if ai_text:
                st.markdown(ai_text)
            st.divider()


if __name__ == "__main__":
    main()
