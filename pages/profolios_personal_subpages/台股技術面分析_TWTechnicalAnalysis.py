import streamlit as st
import pandas as pd
import random
import vectorbt as vbt
print("vectorbt version:", vbt.__version__)
print("vectorbt file:", vbt.__file__)

from pages.profolios_personal_subpages.stock_technical_analysis import (
    get_company_info_all_swagger,
    read_and_concat_sqlite_tables,
    read_merged_df_2,
    adls,
    add_ma_columns,
    plotly_k_ma_with_volume,
    plotly_tec_close_ma_20_vectorbt,
    plotly_tec_ma_20_and_60_vectorbt,
    find_best_sma_cross,
    plotly_tec_best_sma_cross_vectorbt,
    plotly_tec_rsi9_14_vectorbt,
    plotly_tec_kd_vectorbt,
    plotly_tec_macd_vectorbt,
    plotly_tec_ao_ac_vectorbt,
    plotly_bollinger_ma,
    plotly_tec_atr,
    bia
)

# ========== 1. CACHE 大資料，只抓一次 ==========
@st.cache_data
def get_full_df():
    """只讀取全量資料一次，回傳 DataFrame。"""
    return read_and_concat_sqlite_tables()

# ========== 2. CACHE 資料切片（依股票和時間區間） ==========
@st.cache_data
def filter_df_by_stock_and_range(full_df, stock_id, date_range):
    """從全量資料根據股票和區間切出子集，只要參數不同才重跑。"""
    # 原本的 read_merged_df_2 已經有做股票+區間篩選，所以直接用
    df = read_merged_df_2(full_df, stock_id, date_range)
    return df

# ========== 3. 股票基本資料查詢（用不到日期範圍，不需重跑） ==========
@st.cache_data
def fetch_data(stock_id):
    try:
        stock_id, stock_name, cm_otc, stock_cm_otc_date, stock_industry, stock_industry_sub, stock_address, \
        stock_business, stock_amount, stock_common_price, stock_amount_common, stock_amount_special, related_data = get_company_info_all_swagger(stock_id)
    except Exception as e:
        st.error('很抱歉數據庫沒有這隻股票的產業資料、連不上數據庫，或出現其他錯誤')
        st.code(str(e))
        return None

    with st.expander(f"選擇的是 {cm_otc} {stock_id} {stock_name} ，{stock_industry}，同產業的有"):
        st.write(list(related_data))

    return cm_otc, stock_industry, stock_name, stock_id, related_data

# ========== 4. 主分析功能：只切資料+作圖 ==========
def analyze_data(stock_industry, stock_name, stock_id):
    date_range = st.select_slider("選擇日期範圍", options=['3年', '2年6個月', '2年', '1年6個月', '1年', '6個月', '3個月', '2個月'], value='3個月')
    full_df = get_full_df()  # 只抓一次
    filtered_df_raw = filter_df_by_stock_and_range(full_df, stock_id, date_range)  # 快速切片
    filtered_df = add_ma_columns(filtered_df_raw)
    st.write()
    
    
    try:
        st.markdown("#### ★ ADLs（累積廣度線）")
        st.write('''
                - **ADLs（Advance-Decline Line Smoothed）** 是觀察市場整體多空氣勢的指標，透過上漲家數與下跌家數的差值累積，判斷市場內部強弱  
                - 快線與慢線可平滑波動，觀察短中期趨勢變化  
                - **訊號解讀：**
                - 快線（短期）連續高於慢線（中期）→ 市場多頭氣勢增強，資金持續進場  
                - 快線連續低於慢線 → 市場轉弱，資金撤出或觀望  
                - ADLs 持續上升 → 市場整體健康、廣度擴散  
                - ADLs 持續下降 → 市場漲勢集中、內部疲弱  
                - **常見策略：**
                - 快線上穿慢線（黃金交叉）→ **多頭訊號**，可視為加碼或進場時機  
                - 快線下穿慢線（死亡交叉）→ **空頭訊號**，可視為減碼或停利時機  
                - 若 ADLs 創高但指數未創高，出現**背離現象**，代表漲勢可能放緩  
                - **公式：**
                - ADL = 前一日 ADL + （上漲家數 − 下跌家數）  
                - 快線 = ADL 的短期移動平均（如 5 日）  
                - 慢線 = ADL 的長期移動平均（如 20 日）
            ''')
        fig = adls(filtered_df)
        st.plotly_chart(fig)
        st.divider()
    except:
        pass
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 盒鬚圖 + 移動平均線")
        st.write('''
                - **盒鬚圖（K線圖）** 顯示每個交易日的價格變化，包括開盤價、收盤價、最高價、最低價  
                - **紅K（陽線）**：收盤價 > 開盤價，代表股價上漲  
                - **黑K（陰線）**：收盤價 < 開盤價，代表股價下跌  
                - 連續多根紅K → 股價呈上升趨勢；連續多根黑K → 股價呈下降趨勢  
                - **移動平均線（MA）**：顯示一段期間內平均價格，常用 MA5、MA20、MA60  
                - 短期均線向上突破長期均線（黃金交叉）→ 多頭訊號  
                - 短期均線向下跌破長期均線（死亡交叉）→ 空頭訊號  
                - 可觀察 K 線形態與均線方向，判斷趨勢強弱與反轉可能
            ''')
        fig = plotly_k_ma_with_volume(filtered_df, stock_industry, stock_name, stock_id, ma_list=(5, 14, 20, 30, 60, 120, 240), vol_ma_list=(5, 10))
        st.plotly_chart(fig)
        st.divider()
    except:
        pass
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 收盤價 + 20MA（移動平均線）")
        st.write('''
                - 20MA 是過去 20 日收盤價的平均，用來觀察中期趨勢與價格穩定度  
                - 當股價位於 20MA 上方，代表多頭；反之則為空頭
                - **訊號解讀：**
                - 股價長期在 20MA 上方 → 上升趨勢  
                - 股價長期在 20MA 下方 → 下降趨勢  
                - 股價遠離 20MA → 可能超買或超賣，價格常回歸均線  
                - **常見策略：**
                - 短期均線上穿 20MA → **金叉（Golden Cross）**，可能為買入訊號  
                - 短期均線下穿 20MA → **死叉（Death Cross）**，可能為賣出訊號  
                - 股價突破 20MA 並站穩 → 多頭確認；跌破 20MA → 空頭確認  
                - **公式：**
                - 20MA = 最近 20 日收盤價總和 ÷ 20
            ''')
        fig, fig2, fig3, fig4 = plotly_tec_close_ma_20_vectorbt(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig, key="fig_ma_close_20_main")
        # st.plotly_chart(fig2, key="fig_ma_close_20_idx")
        # st.write("fig3型別：", type(fig3), "fig4型別：", type(fig4))
        if fig3 is not None:
            st.plotly_chart(fig3, key="fig_ma_close_20_table")
        if fig4 is not None:
            st.plotly_chart(fig4, key="fig_ma_close_20_equity")
        st.divider()
    except Exception as e:
        st.error("收盤價 + 20MA 區塊出錯！")
        # st.exception(e)
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 20MA + 60MA")
        fig, fig2, fig3, fig4 = plotly_tec_ma_20_and_60_vectorbt(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig, key="fig_ma_20_60_main")
        # st.plotly_chart(fig2, key="fig_ma_20_60_idx")
        # st.write("fig3型別：", type(fig3), "fig4型別：", type(fig4))
        if fig3 is not None:
            st.plotly_chart(fig3, key="fig_ma_20_60_table")
        if fig4 is not None:
            st.plotly_chart(fig4, key="fig_ma_20_60_equity")
        st.divider()
    except Exception as e:
        st.error("20MA + 60MA 區塊出錯！")
        # st.exception(e)
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 最優 MA")
        result = find_best_sma_cross(filtered_df)
        n1, n2 = result['best_n1'], result['best_n2']
        fig, fig2, fig3, fig4 = plotly_tec_best_sma_cross_vectorbt(filtered_df, stock_industry, stock_name, stock_id, n1=n1, n2=n2)
        
        st.plotly_chart(fig, key="fig_ma_best_main")
        # st.plotly_chart(fig2, key="fig_ma_best_idx")
        # st.write("fig3型別：", type(fig3), "fig4型別：", type(fig4))
        if fig3 is not None:
            st.plotly_chart(fig3, key="fig_ma_best_table")
        if fig4 is not None:
            st.plotly_chart(fig4, key="fig_ma_best_equity")
        st.divider()
    except Exception as e:
        st.error("最優 MA 區塊出錯！")
        # st.exception(e)
    st.subheader("")


    try:
        st.markdown("#### ★ 收盤價 + RSI（相對強弱指標）")
        st.write('''
                - RSI（Relative Strength Index）用於衡量股價漲跌的強弱，判斷市場是否過熱或過冷，範圍介於 **0～100**  
                - 常見參數為 **RSI9**（短線靈敏）與 **RSI14**（中期穩定）  
                - **訊號解讀：**
                - RSI > 70 → **超買區**，價格偏高，可能出現回跌  
                - RSI < 30 → **超賣區**，價格偏低，可能反彈  
                - RSI 約 50 → 多空力量平衡  
                - **常見策略：**
                - RSI < 30 往上突破 → 短線買入訊號  
                - RSI > 70 往下跌破 → 短線賣出訊號  
                - RSI 與收盤價同向上升 → 趨勢延續；若出現背離 → 可能反轉  
                - **公式：**
                - RSI = 100 - (100 / (1 + RS))  
                - 其中 **RS = 平均漲幅 / 平均跌幅**（常取 9 或 14 日）
            ''')
        fig, fig2, fig3, fig4, stats = plotly_tec_rsi9_14_vectorbt(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig, key="fig_rsi_main")
        # st.plotly_chart(fig2, key="fig_rsi_idx")
        # st.write("fig3型別：", type(fig3), "fig4型別：", type(fig4))
        if fig3 is not None:
            st.plotly_chart(fig3, key="fig_rsi_table")
        if fig4 is not None:
            st.plotly_chart(fig4, key="fig_rsi_equity")
        if stats is not None:
            st.dataframe(stats)
        st.divider()
    except Exception as e:
        st.error("最優 RSI 區塊出錯！")
        # st.exception(e)
    st.subheader("")

    
    try:
        st.markdown("#### ★ 收盤價 + RSV + KD（隨機指標）")
        st.write('''
                - **RSV（Raw Stochastic Value）** 衡量收盤價在一定期間內的相對位置，用來觀察短期強弱  
                - **K值** 為 RSV 的移動平均，**D值** 為 K 值的移動平均，用於平滑波動  
                - **訊號解讀：**
                - **K值上穿D值（黃金交叉）** → 短線轉強，可能為**買入訊號**  
                - **K值下穿D值（死亡交叉）** → 短線轉弱，可能為**賣出訊號**  
                - **KD值 > 80** → 超買區，股價可能回跌  
                - **KD值 < 20** → 超賣區，股價可能反彈  
                - **常見策略：**
                - K 值由低檔（≤20）向上突破 D 值 → **短線買入訊號**  
                - K 值由高檔（≥80）向下跌破 D 值 → **短線賣出訊號**  
                - KD 與股價背離時（例如股價創新高但 KD 未創新高）→ 可能趨勢反轉  
                - **公式：**
                - RSV = (收盤價 - 最近 N 日最低價) ÷ (最近 N 日最高價 - 最近 N 日最低價) × 100  
                - K = 前一日 K × (2/3) + 當日 RSV × (1/3)  
                - D = 前一日 D × (2/3) + 當日 K × (1/3)
            ''')
        fig, fig2, fig3, fig4, stats  = plotly_tec_kd_vectorbt(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig, key="fig_rsv_kd_main")
        # st.plotly_chart(fig2, key="fig_rsv_kd_idx")
        # st.write("fig3型別：", type(fig3), "fig4型別：", type(fig4))
        if fig3 is not None:
            st.plotly_chart(fig3, key="fig_rsv_kd_table")
        if fig4 is not None:
            st.plotly_chart(fig4, key="fig_rsv_kd_equity")
        if stats is not None:
            st.dataframe(stats)
        st.divider()
    except Exception as e:
        st.error("最優 RSV KD 區塊出錯！")
        # st.exception(e)
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 收盤價 + MACD（平滑異同移動平均線）")
        st.write('''
                - **MACD**（Moving Average Convergence Divergence，平滑異同移動平均線）是常用的趨勢追蹤指標，用來判斷多空趨勢轉換與動能強弱  
                - 由三部分組成：  
                - **DIF（快線）**：短期 EMA（12 日）減去長期 EMA（26 日）  
                - **MACD（慢線）**：DIF 的 9 日 EMA  
                - **OSC（柱狀圖）**：DIF - MACD，顯示多空力量差距  
                - **訊號解讀：**
                - DIF 上穿 MACD → **金叉**，代表多頭轉強，可能為**買入訊號**  
                - DIF 下穿 MACD → **死叉**，代表空頭轉強，可能為**賣出訊號**  
                - 柱狀圖由負轉正 → 多頭動能增強；由正轉負 → 空頭動能增強  
                - **常見策略：**
                - DIF 從下方上穿 MACD → 進場買入訊號  
                - DIF 從上方下穿 MACD → 賣出或減碼訊號  
                - 柱狀圖持續放大 → 趨勢延續；縮小 → 可能反轉  
                - **公式：**
                - DIF = EMA(收盤價, 12) − EMA(收盤價, 26)  
                - MACD = EMA(DIF, 9)  
                - OSC = DIF − MACD
            ''')
        fig, fig2, fig3, fig4, stats  = plotly_tec_macd_vectorbt(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig, key="fig_macd_main")
        # st.plotly_chart(fig2, key="fig_macd_idx")
        # st.write("fig3型別：", type(fig3), "fig4型別：", type(fig4))
        if fig3 is not None:
            st.plotly_chart(fig3, key="fig_macd_table")
        if fig4 is not None:
            st.plotly_chart(fig4, key="fig_macd_equity")
        if stats is not None:
            st.dataframe(stats)
        st.divider()
    except Exception as e:
        st.error("最優 MACD 區塊出錯！")
        # st.exception(e)
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 收盤價 + AO / AC（震盪與加速度指標）")
        st.write('''
                - **AO（Awesome Oscillator）** 用於比較短期與長期的市場動能，判斷多空趨勢轉換  
                - **AC（Acceleration / Deceleration Oscillator）** 衡量動能變化的加速度，用來捕捉趨勢轉折點  
                - **訊號解讀：**
                - AO > 0 且 AC > 0 → 多頭動能強，價格可能持續上漲  
                - AO < 0 且 AC < 0 → 空頭動能強，價格可能持續下跌  
                - AC 由負轉正 → 動能加速向上，可能為**買入訊號**  
                - AC 由正轉負 → 動能減速轉弱，可能為**賣出訊號**  
                - AO、AC 同時在 0 軸上方 → 多方主導；同時在 0 軸下方 → 空方主導  
                - **常見策略：**
                - AC 剛突破 0 軸且 AO > 0 → 視為多頭啟動訊號，**可考慮進場**  
                - AC 剛跌破 0 軸且 AO < 0 → 視為空頭轉弱訊號，**可考慮退場**  
                - AO、AC 同向變化 → 趨勢延續；反向變化 → 可能反轉  
                - **公式：**
                - AO = SMA(中價, 5) − SMA(中價, 34)，其中中價 = (最高價 + 最低價) ÷ 2  
                - AC = AO − SMA(AO, 5)
            ''')
        fig, fig2, fig3, fig4, stats = plotly_tec_ao_ac_vectorbt(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig, key="fig_aoac_main")
        # st.plotly_chart(fig2, key="fig_aoac_idx")
        # st.write("fig3型別：", type(fig3), "fig4型別：", type(fig4))
        if fig3 is not None:
            st.plotly_chart(fig3, key="fig_aoac_table")
        if fig4 is not None:
            st.plotly_chart(fig4, key="fig_aoac_equity")
        if stats is not None:
            st.dataframe(stats)
        st.divider()
    except Exception as e:
        st.error("最優 AO AC 區塊出錯！")
        # st.exception(e)
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 收盤價 + 布林通道（Bollinger Bands 20日）")
        st.write('''
                - **布林通道（Bollinger Bands）** 是一種衡量價格波動區間的技術指標，用於觀察支撐、壓力與突破機會  
                - 由三條線組成：**上軌（UB）**、**中軌（MB）**、**下軌（LB）**  
                - **中軌（MB）** = 20 日移動平均線（MA20）  
                - **上軌（UB）** = MA20 + 2 × 標準差  
                - **下軌（LB）** = MA20 − 2 × 標準差  
                - 當市場波動擴大，通道會變寬；波動縮小，通道會收斂  
                - **訊號解讀：**
                - 價格觸及上軌 → 可能進入**超買區**或出現**突破行情**  
                - 價格觸及下軌 → 可能進入**超賣區**或有**反彈機會**  
                - 通道收斂 → 市場波動減弱，常是大行情啟動前的訊號  
                - 通道擴張 → 波動放大，趨勢可能延續  
                - **常見策略：**
                - 價格跌破下軌 → 可視為反彈觀察點（逢低布局）  
                - 價格突破上軌 → 若量能配合，可能形成突破行情  
                - 結合 RSI 或 MACD 使用，可提高訊號準確度  
                - **公式：**
                - MB = 20 日收盤價移動平均  
                - UB = MB + (2 × 20 日標準差)  
                - LB = MB − (2 × 20 日標準差)
            ''')
        fig = plotly_bollinger_ma(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig)  
        st.divider()
    except:
        pass    
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 收盤價 + ATR（平均真實波動幅度）")
        st.write('''
                - **ATR（Average True Range）** 用於衡量一定期間內價格波動的幅度，是常見的**市場波動率指標**  
                - ATR 數值越大 → 波動劇烈；ATR 越小 → 市場平穩  
                - 常見週期為 **ATR5（短線）**、**ATR14（中線）**  
                - **訊號解讀：**
                - ATR 無方向性，僅反映波動強弱  
                - **ATR 上升** → 市場波動加劇，可能伴隨趨勢啟動或消息事件  
                - **ATR 下降** → 市場進入整理或盤整階段  
                - 高 ATR 時進出風險較高，低 ATR 時市場相對穩定  
                - **常見策略：**
                - 以 ATR 判斷進出場時機：波動放大時觀察是否為趨勢突破  
                - 設定移動停損（Trailing Stop）：止損距離可設定為進場價 ± 1～2 倍 ATR  
                - 結合趨勢指標（如 MA、MACD）使用，以避免單純波動造成誤判  
                - **公式：**
                - TR（True Range） = max(當日最高 − 最低, |當日最高 − 前一日收盤|, |當日最低 − 前一日收盤|)  
                - ATR(n) = 過去 n 日 TR 的移動平均（如 ATR14 為過去 14 日 TR 平均）
            ''')
        fig, fig2 = plotly_tec_atr(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig)  
        st.plotly_chart(fig2) 
        st.divider()
    except:
        pass    
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 收盤價 + 乖離率（Bias 指標）")
        st.write('''
                - **乖離率（Bias）** 用於衡量股價相對於移動平均線的偏離程度，用來判斷股價是否短線過熱或過冷  
                - 正乖離表示股價高於均線，負乖離表示股價低於均線  
                - 常用週期：**Bias5（短線）**、**Bias10（中線）**、**Bias20（中長線）**    
                - **訊號解讀：**
                - **正乖離過高**（如超過 +5%）→ 股價漲多，可能出現**短線回檔**  
                - **負乖離過低**（如低於 −5%）→ 股價跌深，可能出現**短線反彈**  
                - 乖離率絕對值越大，代表價格偏離均線越多，修正機率越高  
                - **常見策略：**
                - 乖離率過高時 → 可考慮**獲利了結或減碼**  
                - 乖離率過低時 → 可觀察**反彈或短線買點**  
                - 結合趨勢判斷：上升趨勢中的小幅正乖離仍可續漲，下跌趨勢中的負乖離可能續跌  
                - **公式：**
                - 乖離率(%) = (收盤價 − n 日移動平均) ÷ n 日移動平均 × 100%
            ''')
        fig = bia(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig)  
        st.divider()
    except:
        pass    
    st.subheader("")
    
    

# ========== 5. 主頁面 ==========
def main():
    st.subheader("台股技術面分析 TW Stock Technical Analysis")
    st.write('''
         市面上常見的技術分析時機點回測，適合用來觀察潛在入場時機
         ''')
    st.write('''資料來源: "公開資訊觀測站"、"台灣證券交易所"、"證券櫃檯買賣中心"。直接點圖例可以隱藏、截圖可以放大、右上角🏛️可以重置''')

    stock_id_input = st.text_input("請輸入股票代碼：", value='2330')
    if st.button("查詢"):
        loading_messages = [
            "這不是煮泡麵，需要一點時間的",
            "放輕鬆，不是等開會，是等待你的資產翻倍~",
            "抓五年資料，不是瞬間魔法，是耐力的魔法！",
            "等一下，這比你對刮刮樂快",
            "沒耐心就像打開冰箱找東西，找不到的時候只會更生氣",
            "等待中...這不是等紅燈，是等待財富的綠燈",
            "就像等待手搖飲料一樣，加點料就能更好喝，我比較喜歡奶蓋",
            "放輕鬆，這不是等考績，是等待你的投資籌碼變成黃金"
        ]

        loading_message = random.choice(loading_messages)
        st.text(loading_message)
        fetch_result = fetch_data(stock_id_input)
        if fetch_result is not None:
            cm_otc, stock_industry, stock_name, stock_id, related_data = fetch_result
            st.session_state.cm_otc = cm_otc
            st.session_state.stock_industry = stock_industry
            st.session_state.stock_name = stock_name
            st.session_state.stock_id = stock_id
            st.session_state.related_data = related_data
            
        #     st.session_state.company_expander_info = {
        #     "cm_otc": cm_otc,  
        #     "stock_id": stock_id,
        #     "stock_name": stock_name,
        #     "stock_industry": stock_industry,
        #     "related_data": related_data,  
        # }

    # 如果 session_state 已經有股票，就直接顯示分析
    if "stock_id" in st.session_state:
        analyze_data(
            st.session_state.stock_industry,
            st.session_state.stock_name,
            st.session_state.stock_id
        )
    # if "company_expander_info" in st.session_state:
    #     info = st.session_state.company_expander_info
    #     with st.expander(f"選擇的是 {info['cm_otc']} {info['stock_id']} {info['stock_name']} ，{info['stock_industry']}，同產業的有"):
    #         st.write(list(info['related_data']))

    # HTML和CSS置中樣式
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <p>以上觀點僅供參考，並不構成任何交易建議或推薦</p>
        </div>
    """, unsafe_allow_html=True)


# 
if __name__ == '__main__':
    main()
