import streamlit as st 

def main():
    st.subheader("好用網站 Useful Websites")

    # st.set_page_config(page_title="Useful Websites", page_icon="🌐", layout="wide")

    st.markdown("""
    <style>
    .section-title {
    font-size: 1.15rem; font-weight: 700; letter-spacing: .3px;
    padding: .4rem .8rem; border-radius: 999px; display: inline-flex;
    align-items: center; gap: .5rem; margin: .25rem 0 1rem 0;
    background: var(--background-color, rgba(0,0,0,.04));
    border: 1px solid rgba(127,127,127,.2);
    }
    .section-title .star {filter: saturate(1.2);}
    .card {
    border: 1px solid rgba(127,127,127,.25);
    border-radius: 16px; padding: 14px 14px; margin-bottom: 12px;
    transition: all .15s ease; background: rgba(127,127,127,.06);
    }
    .card:hover {transform: translateY(-2px); border-color: rgba(127,127,127,.45);}
    .card a {text-decoration: none; font-weight: 600;}
    .card .desc {opacity: .75; font-size: .9rem; margin-top: 4px}
    </style>
    """, unsafe_allow_html=True)
    
    
    # 
    LINKS = {
        "TW STOCK": [
            ("公開資訊觀測站｜財務報告 PDF", "https://mopsov.twse.com.tw/mops/web/t57sb01_q1", "官方財報 PDF 快速入口"),
            ("財報狗 StatementDog", "https://statementdog.com/", "台股美股公司財務與圖表"),
            ("GoodInfo! 台灣股市資訊網",
            "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E7%B4%AF%E8%A8%88%E8%B2%B7%E8%B6%85%E5%BC%B5%E6%95%B8+%E2%80%93+%E7%95%B6%E6%97%A5%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E7%B4%AF%E8%A8%88%E8%B2%B7%E8%B6%85%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E8%B2%B7%E8%B6%85%E5%BC%B5%E6%95%B8+%E2%80%93+%E7%95%B6%E6%97%A5",
            "籌碼、排行與多維度指標"),
            ("證交所ETF專區", "https://www.twse.com.tw/zh/products/securities/etf/products/list.html", "ETF資料查詢"),
        ],
        "US STOCK": [
            ("SEC (U.S. Securities and Exchange Commission)", "https://www.sec.gov/", "10-K/10-Q/8-K 官方查詢"),
            ("WiseSheets", "https://www.wisesheets.io/", "Excel/Sheets 抓財報資料"),
            ("Macrotrends", "https://www.macrotrends.net/?q=googl", "美股財務與指標趨勢圖"),
            ("FINGUIDER", "https://finguider.cc/", "美股基本面與圖表工具"),
            ("gurufocus", "https://www.gurufocus.com/", "美股財報、估值可視化"),
            ("Finviz Heatmap", "https://finviz.com/map.ashx", "類股熱力圖與篩選"),
            ("QUIVER QUANTITATIVE", "https://www.quiverquant.com/", "Trade Like a Insider"),
        ],
        "NEWS": [
            ("鉅亨網 Cnyes", "https://www.cnyes.com/", "台股/美股/外匯即時新聞"),
            ("CNBC World", "https://www.cnbc.com/world/", "國際財經新聞與專題"),
        ],
        "Economic Indicators": [
            ("VIX 指數", "https://finance.yahoo.com/quote/%5EVIX/", "恐慌指數，反映美股市場預期波動性，常用來衡量市場情緒"),
            ("景氣指標查詢", "https://index.ndc.gov.tw/n/zh_tw", "台灣最新景氣燈號圖表")
        ]
    }

    ICONS = {"TW STOCK": "🇹🇼", "US STOCK": "🇺🇸", "NEWS": "📰", "Economic Indicators": "📈"}


    # === render sections 兩欄卡片 ===
    def render_section(title: str, items: list[tuple[str, str, str]]):
        st.markdown(
            f"""<span class="section-title"><span class="star">★</span> {ICONS.get(title,'')} {title}</span>""",
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)
        cols = [c1, c2]
        for i, (name, url, desc) in enumerate(items):
            with cols[i % 2]:
                st.markdown(
                    f"""
                    <div class="card">
                    <a href="{url}" target="_blank">{name} ↗</a>
                    <div class="desc">{desc}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    for section, items in LINKS.items():
        render_section(section, items)
        st.markdown(" ")


    st.markdown("> 小提醒：所有連結將在新分頁開啟。")

if __name__ == '__main__':
    main()
