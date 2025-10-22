import streamlit as st
import random
from pages.profolios_personal_subpages.stock_material import (
    read_and_concat_sqlite_tables,
    read_merged_df_2,
    plotly_material,
    unrated
)

# ========== 1. CACHE 大資料：只抓一次，並設定 TTL（例如 6 小時） ==========
@st.cache_data(show_spinner="載入資料中…", persist=True, ttl=21600)  # 21600 = 6hr
def get_full_df():
    """只讀取全量資料一次，回傳 DataFrame。"""
    return read_and_concat_sqlite_tables()

# ========== 2. CACHE 日期切片：以 'date_range' 當快取鍵 ==========
@st.cache_data(show_spinner=False, ttl=3600)  # 1 小時更新一次，避免 datetime.now() 導致快取不刷新
def filter_df_by_range(date_range: str):
    """根據日期範圍，從全量資料切出子集。"""
    full_df = get_full_df()  # 內部取得全量，避免 DataFrame 成為快取鍵
    return read_merged_df_2(full_df, date_range)

# ========== 3. 主分析功能：只切資料 + 作圖 ==========
def analyze_data():
    date_range = st.select_slider(
        "選擇日期範圍",
        options=['3年', '2年6個月', '2年', '1年6個月', '1年', '6個月', '3個月', '2個月', '1個月'],
        value='3年'
    )
    filtered_df = filter_df_by_range(date_range)

    try:
        st.markdown("#### ★ 大宗商品與主要市場")
        fig, fig2, fig2_2, fig3, summary = plotly_material(filtered_df)
        st.plotly_chart(fig, key="fig_material_main")
        st.plotly_chart(fig2, key="fig_material2_main")
        st.plotly_chart(fig2_2, key="fig_material2-2_main")
        st.plotly_chart(fig3, key="fig_material3_main")
        st.dataframe(summary, key="fig_material_summary")
        st.divider()
    except Exception as e:
        pass
        # st.exception(e)
    st.subheader("")
    
    
    try:
        st.markdown("#### ★ 失業率 vs S&P500（月資料）")
        fig_un = unrated(filtered_df)
        st.plotly_chart(fig_un)
        st.divider()
    except Exception as e:
        pass
        # st.exception(e)
    st.subheader("")

# ========== 4. 主頁面 ==========
def main():
    st.subheader("國際商品與指數參照 Global Commodity Index")
    st.write("""
    - 觀察全球大宗商品（如原油、黃金、農產品）、美國/亞洲/歐洲主要股市指數的同步或分歧走勢
    - 商品價格大幅波動時，通常反映通膨、景氣循環、避險需求或資金流向的重要變化
    - 指數/商品全線大漲，可能意味通膨壓力或景氣轉折；若商品與股市同時下跌，則須留意景氣衰退風險
    """)

    # 不需要輸入 stock_id
    analyze_data()

    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <p>以上觀點僅供參考，並不構成任何交易建議或推薦</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
