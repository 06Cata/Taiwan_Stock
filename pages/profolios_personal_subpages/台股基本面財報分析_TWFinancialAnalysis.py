import streamlit as st
import random
from pages.profolios_personal_subpages.stock_fundamental_analysis import (
    get_company_info_all_swagger,
    read_and_concat_sqlite_tables,
    read_and_concat_sqlite_tables_monthly_eps,
    plotly_ocf_icf_fcf, # 011
    plotly_ocf_ni, # 011-2
    plotly_net_free_cash_flow, # 011-3 
    plotly_main_items_trend_from_table, # 002-2
    plotly_shareholders_equity_from_table, # 004
    plotly_cfr_ratio, # 012-014
    plotly_cashncash_equivalents, # 015
    plotly_turnover_trend, # 007
    plotly_fake_new, # 007-2
    plotly_fixed_asset_turnover_ready, # 008
    plotly_roe, # 005
    plotly_roa, # 006
    plotly_3_rate, # 016
    plotly_year_revenue, # 018
    plotly_growth_rates, # 019
    plotly_operating_margin_of_safety, # 017
    plotly_non_operating_earnings, # 020
    plotly_tax_advantage, # 010
    plotly_debt_to_asset_ratio_from_table, # 001
    plotly_long_term_capital_to_ppe_ratio_from_table, # 002
    plotly_equity_multiplier_from_table, # 003
    plotly_debt_paying_ability, # 009
    plotly_eps_monthly, # 021-1
    monthly_eps, # 021-2
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

# # ========== 2. CACHE 資料切片（依股票和時間區間） ==========
# @st.cache_data
# def filter_df_by_stock_and_range(full_df, stock_id, date_range):
#     """從全量資料根據股票和區間切出子集，只要參數不同才重跑。"""
#     # 原本的 read_merged_df_2 已經有做股票+區間篩選，所以直接用
#     df = read_merged_df_2(full_df, stock_id, date_range)
#     return df

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
    full_df = get_full_df()  # 只抓一次
    monthly_eps_df = get_monthly_eps_df()  # 只抓一次
    
    st.write()
    
    st.subheader("【現金流量】")
    try: # 缺去年同期比較
        # 現金流量表 (比氣長，有三長) 
        # 011 包成def
        # ocf icf fcf
        st.markdown("#### ★ 現金流量，現金越多氣越長，更能應對可能的不確定性")
        st.markdown('''
                - 現金流量體現企業實際的資金狀況，有助於觀察營運健康程度  
                - **營業活動現金流（Operating Cash Flow, OCF）**：正值通常代表本業賺錢、現金流入；長期為負需留意經營風險  
                - **投資活動現金流（Investing Cash Flow, ICF）**：負值表示公司持續投資、擴張業務；正值通常是資產變現或縮減投資  
                - **融資活動現金流（Financing Cash Flow, FCF）**：正值為借款或增資、資金流入；負值為還債或發放股利等資金流出  
                ''')
        fig, fig2, df_cashflow = plotly_ocf_icf_fcf(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig) 
        st.plotly_chart(fig2)    
        st.divider()
    except:
        pass
    st.subheader("")
 
 
    try: 
        # 011-2 包成def
        # ocf ni 比較 plotly_ocf_ni
        st.markdown("#### ★ 營業活動現金流量/負債/固定資產 比較")
        st.markdown('''
                - 觀察營業活動現金流（OCF）與流動負債、固定資產的關係，可以快速判斷企業現金流體質與資本結構是否健康
                - **OCF > 0**：營業活動現金流長期為正，代表公司本業持續產生現金，經營穩健
                - **OCF > 流動負債**：本業現金流可完全覆蓋短期債務，資金調度壓力小，不怕被催收帳款
                - **OCF > 固定資產**：公司用本業賺來的現金就能投資固定資產，顯示有能力自主擴張，減少對外部融資依賴
                - 這三項指標搭配觀察，有助於分辨企業是靠「真本事」成長，還是過度舉債、靠外部資金撐大規模
                - 獲利含金量（OCF/NI）指的是公司每賺到 1 元帳面淨利，實際能收到多少現金
                - **公式：**
                - 獲利含金量% = (營業活動現金流 / 淨利) × 100
                ''')
        fig, fig2, fig3, df_ocf_ni = plotly_ocf_ni(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig) 
        st.plotly_chart(fig2)    
        st.plotly_chart(fig3)    
        st.divider()
    except:
        pass
    st.subheader("")
        
        
    try:
        # 011-3 包成def
        # 淨現金流量 net cash flow: ofc+icf+fci (直接反映一間公司錢是流出去多or流進來多)
        # 自由現金流量 Free cash flow : ocf-icf (公司可以自由運用的現金
        # 一間好公司自由現金流量應該要是正的，代表公司擴張，都能帶回營運的現金) 5/8要是正的
        # 銀行業ok不用調
        st.markdown("#### ★ 淨現金流量、自由現金流量")
        st.markdown('''
                - **淨現金流量**：觀察公司整體現金「淨進/淨出」的情況，反映公司這一期現金是流入還是流出較多
                - **自由現金流量（Free Cash Flow, FCF）**：公司在進行資本支出（如擴廠、投資）後，真正能自由運用的現金。自由現金流量高，代表企業在擴張或投資後仍保有較高的現金彈性；反之，若長期為負，可能代表資本支出較大，需進一步檢視資本用途及現金流穩定性
                - **健康狀態判斷**：近八季中有**五季**自由現金流量為正，通常代表現金流穩健，能因應各種不確定風險
                - **公式**：
                - 淨現金流量 = 營業活動現金流 + 投資活動現金流 + 融資活動現金流
                - 自由現金流量 = 營業活動現金流 + 投資活動現金流
                ''')
        fig, fig2, df_out = plotly_net_free_cash_flow(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.divider()
    except:
        pass
    st.subheader("")


    try:
        # 002-2 包成def
        # 現金與約當現金(流動資產)、不動產廠房及設備(非流動資產)、流動負債合計、非流動負債合計、長期資金(非流動負債)趨勢
        # 銀行業不看
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass
        else:
            st.markdown("#### ★ 與下方一起查看")
            st.markdown('''
                    - 建議同時觀察「現金與約當現金」、「不動產、廠房及設備」、「資本公積」等項目的變化
                    - 若發現現金、資本公積同時增加，可能為**現金增資或股本溢價**；如資產重估，則現金、資本公積也可能有同步變動
                    - 若出現現金增加、不動產減少且資本公積增加，可能為**處分固定資產**所致
                    - 觀察「現金」、「不動產、廠房及設備」、「長期借款」是否大幅增加，判斷公司是否藉由**舉債擴張業務**
                    - 綜合這些項目能協助分析公司現金流、資本運作與資產調整狀況
                    ''')
            fig, fig2, df_main_items_trend = plotly_main_items_trend_from_table(full_df, stock_industry, stock_id, stock_name)
            st.plotly_chart(fig) 
            st.plotly_chart(fig2)
            st.divider()
    except:
        pass
    st.subheader("")
    

    try:
        # 004 包成def
        # 股東權益: 股本、保留盈餘、資本公積
        # 銀行業ok 
        st.markdown("#### ★ 股本/保留盈餘/資本公積")
        st.markdown('''
                - **股本**: 公司發行的所有普通股的總額  
                - **保留盈餘**: 從淨利中保留下來的，顯示公司的獲利能力  
                - **資本公積**: 企業收到的資金超過股票面額，代表額外的資本增值，顯示市場上的價值和投資者的信心  
                - 如果有企業用公積配股，要注意是否因為淨利不理想，為了維持股價而進行公積配股
                    ''')
        fig, fig2, df_shareholders_equity = plotly_shareholders_equity_from_table(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig) 
        st.plotly_chart(fig2)
        st.divider()
    except:
        pass
    st.subheader("")
    

    try:
        # 012~014 包成def
        # 現金流量關鍵
        # 現金流量比率 = 營業活動淨現金流量 / 流動負債
        # 現金流量允當比率 = 最近五年度營業活動淨現金流量 / 最近五年度（資本支出 + 存貨增加額 + 現金股利）
        # 現金再投資比率 = （營業活動淨現金流量 - 現金股利） / （不動產、廠房及設備毛額 + 長期投資 + 其他非流動資產 + 營運資金）
        # 銀行業不看
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass
        else:
            st.markdown("#### ★ 現金流量比率") 
            st.markdown('''
                    - **現金流量比率**：衡量公司營業活動產生的現金流入，是否足以應付當期的流動負債（短期債務）
                    - 比率越高，代表短期償債能力越強；**高於 100%** 表示公司本業產生的現金流足以全額覆蓋流動負債，財務體質相對健康
                    - 若 **低於 100%**，與同業比較，評估是否有潛在償債壓力，或需關注現金流來源的穩定性
                    - **公式：**
                    - 現金流量比率（%）= 營業活動淨現金流量 ÷ 流動負債 × 100
                    ''')
            fig, fig2, df_cfr = plotly_cfr_ratio(full_df, stock_industry, stock_id, stock_name)
            st.plotly_chart(fig) 
            st.plotly_chart(fig2)
            st.divider()
    except:
        pass
    st.subheader("")


    try:
        # 015 包成def 
        # 現金佔比趨勢
        # 現金最好佔總資產10~25%，資本密集行業最好更高
        # 銀行業ok
        st.markdown("#### ★ 現金佔比趨勢")
        fig, fig2, df_cashncash_equivalents = plotly_cashncash_equivalents(full_df, stock_industry, stock_id, stock_name)
        st.markdown('''
                - **現金佔比** : 反映公司短期內可動用的現金資產占總資產的比重，是衡量公司資金彈性與短期安全性的指標
                - 通常建議現金佔比維持在 **10%～25%** 之間，資本密集型行業（如製造、科技等）標準可更高；金融業因營運型態不同，現金佔比通常較低
                - 若現金佔比 **低於 10%**，建議與同業或歷史平均比較，評估是否有潛在資金壓力
                - **公式：**
                - 現金佔比（%）= 現金與約當現金 ÷ 資產總額 × 100
                ''')
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.divider()
    except:
        pass
    st.subheader("")
        
        
    st.subheader("【經營能力】")
    try:
        # 007 包成def
        # 應收帳款、存貨周轉、應付帳款、總資產周轉、現金佔比
        # 銀行業不看
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass
        else:
            st.markdown("#### ★ 總資產、存貨、應收、應付帳款週轉率")
            fig_table, fig_asset, fig_turn, fig_days, fig_cash, df_turnover = plotly_turnover_trend(full_df, stock_industry, stock_id, stock_name)
            st.markdown('''
                    - **總資產週轉率**：衡量公司運用全部資產創造營收的效率。週轉率 > 1 表示資產運用有效率，愈高愈佳。若 **< 1**，多見於資本密集或特殊產業（如半導體、精品、網路、金融業）
                    - **現金佔比** : 建議 **10~25%**，或應收帳款天數短（<15天）、存貨天數短（<60天），代表公司現金回收快、資金靈活
                    - **存貨週轉率** : **> 6** 次/年屬於表現良好，說明存貨去化順暢，資金不易卡在庫存
                    - **應收帳款天數** : **< 15** 天為收現金型產業，B2B 通常 60~90 天。與同業比較可了解收現能力是否具優勢
                    - **公式：**
                    - 總資產週轉率 = 營業收入 ÷ 平均資產總額
                    - 存貨週轉率 = 營業成本 ÷ 平均存貨
                    - 應收帳款週轉率 = 營業收入 ÷ 平均應收帳款淨額
                    - 應付帳款週轉率 = 營業成本 ÷ 平均應付帳款淨額
                ''')
            st.plotly_chart(fig_table) 
            st.plotly_chart(fig_asset)
            st.plotly_chart(fig_turn) 
            st.write('''
                    - **應付帳款天數** : 應該維持平穩或緩步上升，代表公司延後付款、有效運用資金，付款週期越長，越能靈活調度現金
                    - **存貨天數** : 建議維持平穩或下降，存貨在庫天數越短越好，代表庫存去化快、資金不易積壓在庫存
                    - **應收帳款天數** : 應該平穩或下降，天數越短代表現金回收速度越快，有助於提升資金周轉率
                    - 若做生意的完整週期（存貨天數 + 應收帳款天數）超過 200 天，企業需有充足現金和較高毛利來支撐運作
                    - **公式：**
                    - 做生意完整週期 = 存貨天數 + 應收帳款天數
                    ''')
            st.plotly_chart(fig_days)
            st.write('''
                    - **現金週轉天數**建議維持平穩或緩慢下降，代表現金回收速度加快、資金壓力減輕
                    - 天數愈短，代表公司從投入資金到回收現金的週期愈快，經營更有效率
                    - **公式：**
                    - 現金週轉天數 = 存貨天數 + 應收帳款天數 - 應付帳款天數
                    ''')
            st.plotly_chart(fig_cash)
            st.divider()
    except:
        pass
    st.subheader("")
    
    
    try:
        # 007-2 包成def
        # (若是有假公司財報，觀察應收帳款天數、應收帳款佔總資產比率、存貨天數、存貨佔總資產比率，是否急遽增加
        # 營業收入、淨利成長，但OCF一直收不到現金，現金與約當現金沒成長)
        # 銀行業不看
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass
        else:
            st.markdown("#### ★ 假設有間假公司財報，如何觀察？")
            st.markdown('''
                    - 觀察「**應收帳款天數**」、「**應收帳款佔總資產比**」、「**存貨天數**」、「**存貨佔總資產比**」是否快速上升，代表資金可能卡在賒帳和庫存，現金流回收慢
                    - 即使營業收入、淨利數字持續成長，若**營業活動現金流（OCF）始終無法收現**，或「現金與約當現金」金額未明顯增加，可能只是帳面獲利，實際現金未進公司
                    - 真正體質好的公司，獲利成長會反映在現金流和現金部位的同步提升；若只是數字成長，現金停滯，要特別小心財報粉飾或潛在經營風險
                    ''')
            fig, fig2, df_fake_new = plotly_fake_new(full_df, stock_industry, stock_id, stock_name)
            st.plotly_chart(fig)
            st.plotly_chart(fig2) 
            st.divider()
    except:
        pass
    st.subheader("")
    
    
    try:
        # 008 包成def
        # 不動產、廠房及設備週轉率 Fixed Asset Turnover Ratio
        # 銀行業ok (改成利息收入/平均不動產、廠房及設備淨額)、沒有不動產就不顯示 # 缺
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass            
        else:
            st.markdown("#### ★ 不動產、廠房及設備週轉率")
            st.markdown('''
                    - **不動產、廠房及設備週轉率** : 愈高，代表公司能更有效率運用固定資產創造營收，有助於提升獲利能力
                    - 指標**緩慢上升**通常表示設備使用效率提高，單位產品成本下降，公司競爭力提升
                    - 但若週轉率大幅上升，需留意是否因設備投資落後於業務成長，可能導致產能不足或無法因應訂單快速增加
                    - 注意：產業差異大，例如電子支付、軟體服務等資產較輕的公司，週轉率本來就會偏高，須搭配產業平均判斷
                    - **公式：**
                    - 不動產、廠房及設備週轉率 = 營業收入 ÷ 平均不動產、廠房及設備
                ''')
            fig, fig2, df_fixed_asset_turnover = plotly_fixed_asset_turnover_ready(full_df, stock_industry, stock_id, stock_name)
            st.plotly_chart(fig)
            st.plotly_chart(fig2) 
            st.divider()
    except:
        pass
    st.subheader("")
    
    
    st.subheader("【獲利能力】")
    try:
        # 005 包成def
        # ROE
        # 銀行業ok
        st.markdown("#### ★ ROE 權益報酬率")
        st.markdown('''
                - **ROE（權益報酬率）** 越高，代表公司越能妥善運用股東資金，為股東創造更多獲利
                - 與同業比較時，通常以「**近四季累積 ROE > 10~15%**」（或連續三到五年平均）作為選股的穩健條件
                - 注意：ROE 高的公司，建議同時檢查「稅後淨利」與「財務槓桿（權益乘數）」來源，有些是因本業獲利強，有些則可能靠高槓桿（股本小、借款多）拉高指標
                - 長期、穩定且高於同業平均的 ROE，通常是企業經營效率與競爭力的象徵
                - **公式：**
                - ROE（%） = 稅後淨利 ÷ 平均權益總額 × 100
                ''')
        table, fig, fig2, fig3, df_roe = plotly_roe(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(table)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.plotly_chart(fig3)
        st.divider()
    except:
        pass
    st.subheader("")


    try:
        # 006 包成def
        # ROA
        # 銀行業ok
        st.markdown("#### ★ ROA 資產報酬率")
        st.markdown('''
                - **ROA（資產報酬率）** 愈高，代表公司運用所有資產（不論自有或舉債）創造獲利的效率愈好，經營能力愈強
                - 負債比率高的產業（如金融、保險業）常以 ROA 作為評價重點指標
                - 與同業相比，通常以「**近四季累積 ROA > 5~7%**」（或三到五年平均、連續五年）為穩健條件
                - 若 ROA 偏低、ROE 卻很高，可能公司主要靠財務槓桿（高負債、股本小）來提升 ROE，這類公司潛在風險較高
                - 長期、穩定且高於同業的 ROA，代表企業整體資產運用效率佳、風險較低
                - **公式：**
                - ROA（%） = 稅後淨利 ÷ 平均資產總額 × 100
                ''')
        table, fig, fig2, fig3, df_roa = plotly_roa(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(table)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.plotly_chart(fig3)
        st.divider()
    except:
        pass   
    st.subheader("")
    

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
        table, fig, fig2, fig3, fig4, df_eps = plotly_eps_monthly(monthly_eps_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(table)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.plotly_chart(fig3)
        st.plotly_chart(fig4)
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
            sum_now, sum_last_year, last_year_eps, predicted_eps, df_prediction2 = monthly_eps(monthly_eps_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig)
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
        # 綜合損益表
        # 016 包成def
        # 財報三率
        # 銀行業ok、有些繼續營業單位稅前損益要改、淨收益要改
        st.markdown("#### ★ 財報三率：毛利率、營益率、淨利率")
        st.markdown('''
                - **毛利率、營益率、淨利率**是判斷公司獲利結構、經營效率的三大核心指標
                - **營益率 > 淨利率**：代表公司本業經營效率佳，營運成本、營業費用控制良好
                - **營益率 < 淨利率**：通常極少見，除非有特殊業外收益，否則可能要檢查數據是否有誤
                - **費用率**（毛利率－營益率）：用來觀察營業費用占比，與同業比較，費用率越低通常代表規模越大或經營效率越高
                - 品牌商費用率常高於 20%；實體通路因需僱用員工、維護門市，費用率通常高於網路通路
                - **公式：**
                - 毛利率（%） = (營業收入－營業成本) ÷ 營業收入 × 100
                - 營益率（%） = 營業利益 ÷ 營業收入 × 100
                - 費用率（%） = 毛利率－營益率
                - 淨利率（%） = 稅後淨利 ÷ 營業收入 × 100
                ''')
        fig_table, fig, fig2, df_out = plotly_3_rate(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig_table)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.divider()
    except:
        pass
    st.subheader("")
        

    try:
        # 018 包成def
        # 營收、盈餘、營益率比較
        # 銀行業ok、有些繼續營業單位稅前損益要改、淨收益要改
        st.markdown("#### ★ 營收、盈餘、營益率比較")
        st.markdown('''
            - 當營收成長時，盈餘、營益率同步成長，才是靠本業賺錢的公司
            ''')
        fig, fig2, df_year_revenue = plotly_year_revenue(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.divider()
    except:
        pass   
    st.subheader("")
    
    
    try:
        # 019 包成def
        # 營收成長率 Revenue Growth Rate
        # 季
        # ocf成長率>營收成長率、營益率成長率>營收成長率、稅後淨利成長率>營收成長率
        # 存貨成長率<(營收成長率/2)
        # bs -> cfs -> is
        # 銀行業ok
        st.markdown("#### ★ 營收成長率比較")
        st.markdown('''
                - **營收成長率**：反映公司營運規模的擴張速度，是觀察企業動能與產業景氣的重要指標
                - **存貨成長率**：若存貨成長率過高，代表公司存貨堆積快速增加，除了可能反映對未來訂單的樂觀預期，更常見的原因包括：銷售不佳（滯銷，貨賣不出去）、公司過度樂觀預期銷量，結果賣不掉，導致資金卡在庫存
                - 注意：遇到存貨快速增加時，需檢查營收成長率是否有跟上，需留意未來現金流與庫存風險
                - **公式：**
                - 營收成長率（%）=（本期營收－去年同期營收）÷ 去年同期營收 × 100
                ''')
        fig, fig1_2, fig2, fig2_2, fig3, fig4, df_growth_rates = plotly_growth_rates(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig)
        st.plotly_chart(fig1_2)
        st.plotly_chart(fig2)
        st.plotly_chart(fig2_2)
        st.plotly_chart(fig3)
        st.plotly_chart(fig4)
        st.divider()
    except:
        pass
    st.subheader("")

    
    try:
        # 017 包成def
        # 經營安全邊際 (越高，抵抗景氣波動能力越大)
        # 銀行業不看
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass
        else:
            st.markdown("#### ★ 經營安全邊際")
            st.markdown('''
                    - **經營安全邊際**：衡量公司營運的穩定性及對景氣波動的抵抗力，數值越高代表公司能有效控制營運費用、抵禦環境變動的能力越強
                    - 通常 **> 60%**，表示本業營運效率佳、成本結構穩健，能較輕鬆因應市場變動
                    - 若 **< 50%**，建議與同業比較，觀察是否費用結構過高或經營效率有待提升
                    - **公式：**
                    - 經營安全邊際（%）= 營業利益 ÷ 營業毛利 × 100
                    ''')
            fig, fig2, df_omos = plotly_operating_margin_of_safety(full_df, stock_industry, stock_id, stock_name)
            st.plotly_chart(fig)
            st.plotly_chart(fig2)
            st.divider()
    except:
        pass
    st.subheader("")
    
   
           
    try:
        # 020 包成def
        # 業內、業外
        # 銀行業不看
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass
        else:
            st.markdown("#### ★ 業內、業外佔比、業外貢獻比")
            st.markdown('''
                    - **公式：**
                    - 業內 = 營業利益 ÷（營業利益 + 營業外收入及支出）
                    - 業外 = 營業外收入及支出 ÷（營業利益 + 營業外收入及支出）
                    - 業外收入對總獲利的貢獻比例 = 稅前淨利 ÷ 營業利益
                    ''')
            fig, fig2, df_non_operating_earnings = plotly_non_operating_earnings(full_df, stock_industry, stock_id, stock_name)
            st.plotly_chart(fig)
            st.plotly_chart(fig2)
            st.divider()
    except:
        pass    
    st.subheader("")
    
    
    try:
        # 010 包成def
        # 賦稅優勢
        # 銀行業ok、有些繼續營業單位稅前損益要改 
        st.markdown("#### ★ 賦稅優勢")
        st.markdown('''
                - **賦稅優勢** : 反映公司有效規劃稅負、提升稅後獲利的能力。與同業相比，數值越高代表公司越能降低實際繳稅比例，提升稅後淨利
                - 建議長期觀察，若顯著高於同業，通常代表公司具備更好的稅務規劃與賦稅效率
                - **公式：**
                - 賦稅優勢（%）= 稅後淨利 ÷ 稅前淨利
                ''')
        fig, fig2, df_tax = plotly_tax_advantage(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.divider()
    except:
        pass
    st.subheader("")

    
    st.subheader("【財務結構】")
    try:
        # 001 包成def
        # 資產負債比率 Debt to Asset Ratio
        # 銀行業ok
        st.markdown("#### ★ 資產負債比率")
        st.markdown('''
                - **負債比率** : 越低，代表公司以自有資金經營、股東權益較高，整體財務風險較小，長期經營更穩健
                - **負債比率** : 越高，表示公司使用較多債務資金，雖可能放大潛在收益，但同時增加了財務槓桿與償債壓力
                - 建議與同業比較，一般產業負債比率不高於 50~60% 為宜；但銀行、保險、壽險、營建等產業因營運特性，負債比率通常較高，需以產業標準為主
                - **公式：**
                - 負債比率（%）= 負債總額 ÷ 資產總額 × 100
                ''')
        fig, fig2, df_debt_to_asset_ratio = plotly_debt_to_asset_ratio_from_table(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.divider()
    except:
        pass
    st.subheader("")
    
    
    try:
        # 002 包成def
        # 長期資金佔不動產、廠房及設備比 Ratio of liabilities to assets
        # 銀行業不看 # 缺
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass
        else:
            st.markdown("#### ★ 長期資金佔不動產、廠房及設備比")
            st.markdown('''
                    - **長期資金佔固定資產比率** : 用來衡量公司是否以穩定的長期資金（自有資本與長期負債）來支應不動產、廠房及設備等固定資產
                    - 比率 **> 1**，表示公司以長期資金購置固定資產，資金來源穩健，財務結構安全
                    - 比率 **< 1**，代表公司有部分固定資產是靠短期資金（如短期借款）支應，若比率過低，可能增加營運風險
                    - **公式：**
                    - 長期資金佔固定資產比率 =（權益總額 + 非流動負債）÷ 不動產、廠房及設備
                    ''')
            fig, fig2, df_long_term_capital_to_ppe_ratio = plotly_long_term_capital_to_ppe_ratio_from_table(full_df, stock_industry, stock_id, stock_name)
            st.plotly_chart(fig)
            st.plotly_chart(fig2)      
            st.divider()
    except:
        pass      
    st.subheader("") 
    
    
    try:
        # 003 包成def
        # 權益乘數(財務槓桿) = 總資產 / 股東權益 
        # 總負債/股東權益比 Total Debt/Equity Ratio = 總負債 / 股東權益
        # 銀行業ok 
        st.markdown("#### ★ 權益乘數（財務槓桿）、總負債/股東權益比")
        st.markdown('''
                - **權益乘數（財務槓桿）**
                - 數字越小，代表公司自有資金比例高、資本結構穩健
                - 數字越大，表示公司利用更多外部資金成長，財務槓桿提高，潛在風險也較高
                - 一般產業建議值約 **1.5～3**，金融業、壽險業等可達 10 以上
                - **總負債／股東權益比**
                - 銀行業、資本密集產業這個比值通常較高，需與同業比較
                - 若比值突然大幅上升，需留意是否因舉債擴張或權益大減（如重大虧損）
                - 數字越小代表財務保守、風險低；數字越大則槓桿越高、擴張性強但風險提升
                - 多數產業介於 **0.5～1.5**，過高要小心，金融業例外
                - **公式：**
                - 權益乘數 = 總資產 ÷ 股東權益
                - 總負債／股東權益比 = 總負債 ÷ 股東權益
                ''')
        fig, fig2, df_equity_multiplier = plotly_equity_multiplier_from_table(full_df, stock_industry, stock_id, stock_name)
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
        st.divider()
    except:
        pass    
    st.subheader("")
    

    st.subheader("【償債能力】")
    try:
        # 009 包成def
        # 償債能力 debt-paying ability 
        # 流動比率 current ratio = 流動資產 / 流動負債 
        # 速動比率 quick ratio = （流動資產 - 存貨 - 預付費用）/ 流動負債 
        # 銀行業不看 # 缺
        if stock_industry == "產業別：金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）" or stock_industry == "產業別：金融業":
            pass
        else:
            st.markdown("#### ★ 流動比率、速動比率")
            st.markdown('''
                    - **流動比率、速動比率**衡量公司短期償債能力。輕資產行業（如科技、服務）通常較高，重資產行業（如製造、營建）則偏低
                    - **流動比率**：公司每 1 元流動負債，有多少元流動資產可用來償還。一般標準為 1 以上，與同業比較，通常建議 **1.5～2.5**
                    - **速動比率**：扣除存貨與預付款後，公司每 1 元流動負債，還有多少元流動資產可立即償還，通常建議 **1～1.5**
                    - 若速動比率偏低，建議同時觀察現金與約當現金占比（>10%）、應收帳款天數（<15天）、總資產週轉率（>1）等其他短期流動性指標
                    - **公式：**
                    - 流動比率 = 流動資產 ÷ 流動負債
                    - 速動比率 =（流動資產－存貨－預付款項）÷  流動負債
                    ''')
            fig, fig2, df_liquidity = plotly_debt_paying_ability(full_df, stock_industry, stock_id, stock_name)
            st.plotly_chart(fig)
            st.plotly_chart(fig2)
            st.divider()
    except:
        pass
    st.subheader("")
                
            

# ========== 5. 主頁面 ==========
def main():
    st.subheader("台股基本面: 財報分析 TW Stock Financial Analysis")
    st.write('''
            巴菲特曾說 "You make your money when you buy, not when you sell."  
            買企業，不是買股票，投資者應該專注於評估企業的基本價值，並長期持有，勝率更大  
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




    st.write("")
    st.write("")
    st.write("")
    # HTML和CSS置中樣式
    st.markdown("""
        <div style="text-align: center; margin-top: 50px;">
            <p>以上觀點僅供參考，並不構成任何交易建議或推薦</p>
        </div>
    """, unsafe_allow_html=True)


# 
if __name__ == '__main__':
    main()
