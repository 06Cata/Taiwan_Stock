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
    st.markdown("透過觀察籌碼結構的變化，我們可以推測法人、主力的進出動向，找出「悄悄佈局」的蛛絲馬跡，可以查看「_好用網站_UsefulWebsites」選單連結研究，並參考各家法人目標價")
    st.markdown("""
            <div style="overflow-x:auto; white-space:nowrap; font-size:12px;">  
                  
            > 說明：
            
            | 指標         | 來源                  | 含義                                 | 時間層級      |
            | ---------- | ------------------- | ---------------------------------- | --------- |
            | **大戶持股比例** | 集保股權分散表 | 「1000張以上戶數」的持股比例，代表籌碼**長期結構**      | 週級（每週五更新，可以查看每日集保股權分散表） |
            | **主力買賣超**  | 券商分點 | 前幾名主力分點買進 − 賣出張數的差值，代表短線**資金流動方向** | 日級        |
            | **籌碼集中度**  | 券商分點 | 籌碼是否集中於少數券商（主力）                    | 日級        |

            > 簡單判斷：
            
            | 大戶持股變化       | 主力買賣超             | 籌碼集中度變化 | 市場階段                | 主力行為 / 解讀         | 意涵與操作建議             |
            | ------------ | ----------------- | ------- | ------------------- | ----------------- | ------------------- |
            | ↑ 上升         | ↑ 買超              | ↑ 上升    | **主升段啟動**           | 主力強力吸籌、推升股價       | ✅ 偏多操作              |
            | ↑ 上升         | ↓ 賣超              | ↓ 下降    | **吸籌後洗盤**或**假拉抬／出貨初期**      | 主力暫時壓盤洗籌          | ⚙️ 觀察集中度止跌轉正        |
            | ↑ 上升         | ↑ 買超              | ↓ 下降    | **震盪整理**            | 主力吸籌但散戶介入、量擴散     | ⚠️ 籌碼擴散、漲速放緩        |
            | ↑ 上升         | ↓ 賣超              | ↑ 上升    | **吸籌再吸**            | 主力趁跌再撿籌碼          | ✅ 可低接               |
            | ↑ 上升         | ↓ 主力買超（中立或減弱) | ↓ 下降    | **假拉抬／誘多出貨初期**      | 主力邊拉邊出、換手中、尚未全面出貨 | ⚠️ 高檔警訊，逢高減碼觀察集中度續變 |
            | ↓ 小降 (<0.5%) | ↑ 買超              | ↑ 上升    | **主力換手吸籌（健康型）**     | 舊主力出、新主力接手        | ⚙️ 洗盤後再攻，等待確認       |
            | ↓ 小降 (<0.5%) | ↓ 賣超              | ↓ 下降    | **短線洗盤中**           | 主力震倉 / 短線調節       | ⏸️ 暫觀望              |
            | ↓ 大幅下降 (>1%) | ↑ 買超              | ↑ 高集中   | **主力換手 / 中繼吸籌（特例）** | 舊籌出新籌進、主力間換手      | ⚙️ 等大戶止跌、確認換手完成     |
            | ↓ 大幅下降       | ↓ 賣超              | ↓ 下降    | **出貨尾聲**            | 主力撤退、籌碼鬆動         | ❌ 觀望或撤退             |
            | ↓ 大幅下降       | ↑ 買超              | ↑ 上升    | **誘多出貨**            | 主力邊拉邊出、散戶接盤       | ⚠️ 高檔警訊             |
            | ↓ 大幅下降       | ↑ 買超              | ↓ 下降    | **盤頭形成 / 轉弱期**      | 主力反彈出貨或轉弱         | ⚠️ 轉折區              |
            
            </div>
            """, unsafe_allow_html=True)
        
    st.markdown("""
            <div style="overflow-x:auto; white-space:nowrap; font-size:12px;">        
            
            > 洗盤型態：
            
            | 類型 | 集中度變化與特徵 | 主力買賣超 | 大戶變化 | 股價 / 量能表現 | 主力目的 / 行為 | 操作建議 |
            | ---- | ---------------- | ---------- | -------- | --------------- | ---------------- | -------- |
            | **強勢洗盤（暴跌型）** | 集中度暴跌（>8%），股價急跌後止穩 | 小賣 / 中性 | 小降 (<0.5%) | 放量紅黑交錯 | 主力洗短線籌碼 | ⚙️ 觀察止跌 |
            | **穩控洗盤（控制型）** | 集中度急降但股價穩 | 小賣 / 中性 | 穩定 | 量增不破線 | 測試籌碼穩定度 | ⏸️ 等集中度止跌 |
            | **換手吸籌型（特例）** | 集中度高且持續、主力買、大戶降 | 大買 | ↓ 明顯下降 | 量縮價穩 | 新主力接手、舊主力出 | ⚙️ 等止跌確認 |
            | **出貨型（假洗盤）** | 集中度轉負＋大戶大降 | 賣超轉強 | ↓ 大幅下降 | 爆量紅黑、跌破支撐 | 主力拉高出貨 | ❌ 觀望或撤退 |

            > 洗盤階段：
            
            | 階段               | 集中度變化           | 主力買賣超   | 大戶變化       | 股價 / 量能 | 主力行為解讀    | 操作建議        |
            | ---------------- | --------------- | ------- | ---------- | ------- | --------- | ----------- |
            | **① 洗盤初期**       | 由正轉負（急降）        | 小賣 / 中性 | 小降 (<0.5%) | 放量紅黑交錯  | 震倉洗短線     | ⚙️ 暫不進場     |
            | **② 洗盤中期**       | 持續低檔負值（-5～-10%） | 賣超趨緩    | 穩定或小降      | 量縮價穩    | 籌碼沉澱中     | ⏸️ 等止跌轉正    |
            | **②.5 換手吸籌期** | 維持高集中（>20%）     | 大買      | ↓ 大幅下降     | 量縮盤整    | 舊主力出、新主力接 | ⚙️ 觀察大戶止跌   |
            | **③ 洗盤尾聲 / 初吸籌** | 由負轉正            | 剛轉買超    | 持平         | 量縮價穩    | 主力試探性回補   | 🔍 觀察2–3天續強 |
            | **④ 主升段啟動**      | 維持正值且續升         | 連續買超    | 上升         | 放量紅K突破  | 吸籌完成推升    | ✅ 可分批進場     |
            | **⑤ 假拉抬 / 誘多出貨** | 正轉負             | 轉賣超     | 大戶下降       | 爆量紅黑    | 拉高出貨      | ⚠️ 勿追高      |
            | **⑥ 出貨 / 撤退期**   | 持續負值            | 連賣      | 大幅下降       | 跌破支撐    | 主力撤退      | ❌ 減碼觀望      |
            | **⑦ 觀望 / 橫盤期**   | 持平（±2%）         | 中性      | 穩定         | 縮量橫盤    | 主力觀望      | ⏸️ 等方向      |

            </div>
            """, unsafe_allow_html=True)
         
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
