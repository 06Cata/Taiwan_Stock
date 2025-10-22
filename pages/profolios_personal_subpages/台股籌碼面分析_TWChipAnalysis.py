import streamlit as st
import random
from pages.profolios_personal_subpages.stock_chip_analysis import (
    get_company_info_all_swagger,
    read_and_concat_sqlite_tables,
    read_merged_df_2,
    plot_latest60_invest_bar,
    plot_latest60_margin_bars
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
    date_range = st.select_slider("選擇日期範圍", options=['3個月', '2個月', '1個月'], value='3個月')
    full_df = get_full_df()  # 只抓一次
    filtered_df = filter_df_by_stock_and_range(full_df, stock_id, date_range)  # 快速切片
    st.write()
    
    
    try:
        st.markdown("#### ★ 三大法人買賣超(合併)張數")
        st.write("""
            - 觀察外資、投信、自營商三大法人的**合計買賣動向**
            - **紅色柱狀**：三大法人買超（資金流入）
            - **綠色柱狀**：三大法人賣超（資金流出）
            - **黑色線條**：五日均線（MA5），反映近期動能變化
            """)
        fig, fig2, fig3, fig4, fig5 = plot_latest60_invest_bar(filtered_df, stock_id, stock_industry, stock_name)
        st.plotly_chart(fig, key="fig_invest_main")
        st.plotly_chart(fig2, key="fig_invest2_main")
        st.plotly_chart(fig3, key="fig_invest3_main")
        st.plotly_chart(fig4, key="fig_invest4_main")
        st.plotly_chart(fig5, key="fig_invest5_main")
        st.divider()
    except:
        pass
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 淨槓桿流（融資買賣超 − 融券買賣超）")
        st.write("""
                - 結合融資、融券變化，觀察市場多空槓桿力道  
                - **正值**：融資增加、融券減少 → 多方加碼  
                - **負值**：融資減少、融券增加 → 空方加碼  
                - **黑色線條**：五日均線（MA5），判斷資金方向轉折
                """)
        fig, fig2, fig3, fig4 = plot_latest60_margin_bars(filtered_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig, key="fig_margin_main")
        st.plotly_chart(fig2, key="fig_margin2_main")
        st.plotly_chart(fig3, key="fig_margin3_main")
        st.plotly_chart(fig4, key="fig_margin4_main")
        st.divider()
    except:
        pass
    st.subheader("")
    
    

# ========== 5. 主頁面 ==========
def main():
    st.subheader("台股籌碼面分析 TW Stock Chip Analysis")
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
