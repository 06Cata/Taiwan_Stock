import streamlit as st
import random

from pages.profolios_personal_subpages.stock_fundamental_analysis import (
    plotly_eps_monthly, # 021-1
    monthly_eps, # 021-2
)

from pages.profolios_personal_subpages.stock_value_analysis import (
    get_company_info_all_swagger,
    read_and_concat_sqlite_tables,
    read_and_concat_sqlite_tables_monthly_eps,
    merge_daily_index_pepb_value,
    read_merged_df_2,
    plotly_yield,
    plotly_pb,
    plotly_pe,
    valuation_summary
)



# ========== 1. CACHE 大資料，只抓一次 ==========
@st.cache_data
def get_full_df():
    """只讀取全量資料一次，回傳 DataFrame。"""
    return read_and_concat_sqlite_tables()

@st.cache_data
def get_monthly_eps_df():
    """只讀取全量資料一次，回傳 DataFrame。"""
    return read_and_concat_sqlite_tables_monthly_eps()

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
    date_range = st.select_slider("選擇日期範圍", options=['3年', '2年6個月', '2年', '1年6個月', '1年', '6個月', '3個月', '2個月'], value='3年')
    df_concat = get_full_df()  # 只抓一次
    df_monthly_eps = get_monthly_eps_df()  # 只抓一次
    full_df = merge_daily_index_pepb_value(df_concat, df_monthly_eps)  # 合併
    filtered_df = filter_df_by_stock_and_range(full_df, stock_id, date_range)  # 快速切片
    st.write()
    
    
    try:
        # 月報寫法，有最新一季預測的EPS
        # 021-1 包成def
        # EPS Earning Per Share 每股盈餘
        # 每股盈餘EPS = (本期稅後淨利 – 特別股股利) ÷ 加權平均流通在外的普通股股數
        # 每股盈餘EPS = 稅後淨利/在外流通股數
        st.markdown("#### ★ 月營收比較")
        st.markdown('''
                    - 在季報尚未公布時，可先觀察每月營收，並與去年同期營收比較，推估 EPS、稅後淨利
                    - 若出現月營收與 EPS 都偏低，但營業活動現金流（OCF）仍高，可能原因包括：營業成本下降、資本支出減少、或應收帳款週轉加快等
                    ''')
        table, fig, fig2, fig3, fig4, df_eps = plotly_eps_monthly(df_monthly_eps, stock_industry, stock_id, stock_name)
        st.plotly_chart(table, key="fig_eps_table")
        st.plotly_chart(fig, key="fig_eps_main")
        st.plotly_chart(fig2, key="fig_eps2_main")
        st.plotly_chart(fig3, key="fig_eps3_main")
        st.plotly_chart(fig4, key="fig_eps4_main")
        st.divider()
    except:
        pass
    st.subheader("")
    
    
    try:
        # 021-2 包成def
        # 月報＋EPS
        # EPS Earning Per Share 每股盈餘
        # 每股盈餘EPS = (本期稅後淨利 – 特別股股利) ÷ 加權平均流通在外的普通股股數
        # 每股盈餘EPS = 稅後淨利/在外流通股數
        st.markdown("#### ★ EPS")
        st.markdown('''
                - **每股盈餘（Earnings Per Share, EPS）** : 是衡量公司盈利能力的核心指標，反映公司每一股普通股帶來的獲利水準
                - EPS 數字愈高，代表公司為股東創造的獲利愈多，常用於評估企業獲利趨勢與同業比較
                - **公式：**
                - EPS（每股盈餘）= 損益表中的「基本每股盈餘」
                ''')
        fig, latest_year, latest_month, latest_quarter, current_months, sum_now, sum_last_year, last_year_Q季度, last_year_eps,\
            sum_now, sum_last_year, last_year_eps, predicted_eps, df_prediction2 = monthly_eps(df_monthly_eps, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig, key="fig_monthly_eps_main")
        st.markdown(f'''
                    - **最新資料區間**：{latest_year}年{latest_month}月
                    - **本季度已發布月數**：{current_months}
                    - 本季度累積營收：{sum_now:,.0f}
                    - 去年同期累積營收：{sum_last_year:,.0f}
                    - **去年同期EPS ({last_year_Q季度}）**：{last_year_eps}
                    - 根據 {latest_year} 年第 {latest_quarter} 已發布月份（{', '.join(map(str, current_months))} 月）營收，相較於去年同期（{latest_year-1} 年同月），推估本季EPS約為 {predicted_eps}            
                    ''')
        st.divider()
    except:
        pass   
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 收盤價 + 殖利率")
        st.write('''
                - **殖利率（Dividend Yield）**：用來衡量股票配息相對於股價的比率，反映投資股票能獲得多少現金回報
                - 通常以近一年配發現金股息為主，與現行股價相比較
                - **殖利率高**，表示每投入一元股價可獲得較多現金回饋，常被視為防禦型投資參考指標
                - 但殖利率過高，需留意公司是否因股價大跌或配息不可持續，避免「高殖利率陷阱」
                - **訊號解讀：**
                - 穩定高殖利率的公司，通常現金流穩健、經營較保守
                - 若殖利率遠高於同業或歷史平均，應進一步檢查配息來源與未來可持續性
                - **公式：**
                - 殖利率（%） = 每股現金股息 ÷ 收盤價 × 100%
            ''')
        fig = plotly_yield(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig, key="fig_yield_main")
        st.divider()
    except:
        pass  
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 收盤價 + 股價淨值比")        
        st.write('''
                - **股價淨值比（P/B, Price-to-Book Ratio）**：衡量公司股價相對於每股淨值的高低，用來評估股價是否被**高估或低估**
                - 通常以 **1 倍淨值** 為基準：P/B 小於 1 表示股價低於帳面價值，P/B 大於 1 則代表股價高於帳面價值
                - **訊號解讀：** 
                - **P/B < 1** → 股價低於公司帳面淨值，可能被**低估**（但也需注意公司體質是否不佳）
                - **P/B > 1** → 市場願意給予溢價，反映**成長性或獲利能力佳**
                - **P/B 明顯高於歷史平均** → 股價可能**過熱或高估**。  
                - **P/B 明顯低於歷史平均** → 可能為**長期投資或反彈機會**。  
                - **常見策略：** 
                - 長期投資者可觀察 **P/B < 1 或低於同業平均** 的標的，尋找被低估機會 
                - 成長型公司通常會有較高 P/B，需搭配 **ROE（股東權益報酬率）** 一起判斷 
                - 若 **P/B 上升同時 ROE 下滑**，可能意味估值過高。  
                - **公式：** 
                - 股價淨值比（P/B） = 股價 ÷ 每股淨值（Book Value per Share）
            ''')        
        fig = plotly_pb(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig, key="fig_pb_main")
        st.divider()
    except:
        pass  
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 本益比河流圖（PE Band）")
        st.write('''
                - cheap_pe：同期間**最低**本益比（便宜帶）
                - low_pe：介於 cheap_pe 與 reasonable_pe 的**中低**帶
                - reasonable_pe：同期間**中位數**本益比（合理帶中線）
                - high_pe：介於 reasonable_pe 與 expensive_pe 的**中高**帶
                - expensive_pe：同期間**最高**本益比（昂貴帶）
                - **訊號解讀：**
                - 低於 cheap_pe 附近 → 估值落入**極便宜/壓力出清**區，多觀察基本面與籌碼
                - 介於 low_pe～high_pe → 多屬**合理區**，可搭配趨勢與籌碼做加減碼
                - 高於 expensive_pe 附近 → 估值**昂貴/過熱**風險升高，留意回檔
                - **常見策略：**    
                - 觀察個股長期本益比**河流圖區間**
                - 成長股可接受**長期抬升的合理/昂貴帶**，但需同步驗證 **EPS/ROE** 是否隨之提升
                - 估值帶僅反映「市場給的倍數」，請**同時檢查 EPS 是否下修**以避免「越跌越貴」
                - **公式：**
                - 本益比（PE） = 股價 ÷ 每股盈餘（EPS，近四季或年度）
                - 本益成長比（PEG） = 本益比（PE）÷ 盈餘成長率（EPS 成長率，通常取年複合成長率）
                ''')
        fig2, fig3 = plotly_pe(filtered_df, stock_industry, stock_name, stock_id)
        st.plotly_chart(fig2, key="fig_pe_main")
        st.plotly_chart(fig3, key="fig_pe2_main")
        st.divider()
    except:
        pass  
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 價值評估")
        valuation = valuation_summary(filtered_df, stock_id)
        
        st.markdown('''
            估值方法僅供參考：
            每季若有月報公布，EPS、稅後淨利為去年同期推估   
            若估值結果為負值，通常代表 EPS 為負（公司虧損）或獲利暫時下滑，請特別注意！  
            1. **EPS × 合理本益比法** : 適合大多數電子、科技、成長型公司，主流市場普遍採用
            2. **PEG法** : 屬於保守評價，適合小型高成長或景氣循環早段公司，用在成熟大型公司容易「嚴重低估」合理價值
            3. **PB法**：僅適用資產型、銀行、壽險、傳產等產業，對電子、AI、品牌、軟體公司參考價值低，通常不可用
            ''')
        st.write('')
        st.markdown(f'''
            - **股票代號**：{valuation['股票代號']}                
            - **評價日期**：{valuation['評價日期']}        
            - **評價日股價**：{valuation['評價日股價']}
            - **本益比(現)**：{valuation['本益比(現)']}
            - **近四季累積EPS**：{valuation['近四季累積EPS']}
            - **近四季稅後淨利年增率(%)**：{valuation['近四季稅後淨利年增率(%)']}
            - **合理本益比**：{valuation['合理本益比']}
            - **EPS估值法(偏低PE*EPS)**：{valuation['- EPS估值法(偏低PE*EPS)']}
            - **EPS估值法(合理PE*EPS)**：{valuation['- EPS估值法(合理PE*EPS)']}
            - **EPS估值法(偏高PE*EPS)**：{valuation['- EPS估值法(偏高PE*EPS)']}
            - **PEG估值法(PEG=1)**：{valuation['- PEG估值法(PEG=1)']}
            - **PB估值法(1倍PB)**：{valuation['- PB估值法(1倍PB)']}
            ''')
        st.divider()
    except:
        pass  
    st.subheader("")
    
    
    

# ========== 5. 主頁面 ==========
def main():
    st.subheader("台股基本面: 價值分析 TW Stock Value Analysis")
    st.write('''
            選擇好的股票只是投資的第一步，更重要的是在適當的時間，以合理的價格買進  
            價值投資者通常專注於股票的內在價值，尋找被低估的股票，以便在未來獲得良好的回報
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
