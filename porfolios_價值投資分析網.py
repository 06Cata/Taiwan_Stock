import streamlit as st 
import pandas as pd 
import numpy as np 
import plotly.express as px 
try:
    from pages.profolios_personal_subpages import 台股模型預測_TWStockForecast, 台股產業類別查詢_TWIndustryLookup, 台股指標篩選_TWFundamentalScreener,\
        台股基本面財報分析_TWFinancialAnalysis, 台股基本面價值分析_TWValueAnalysis, 台股技術面分析_TWTechnicalAnalysis, 台股籌碼面分析_TWChipAnalysis,\
        國際商品與指數參照_GlobalCommodityIndex, 美股模型預測_USStockForecast, AI智能分析_AIInsight,\
        _為什麼要投資_WhyInvest, _複利計算機_CompoundCalc, _買賣交易計算機_BuySellCalc  
except ModuleNotFoundError as e:
    st.error(f"Error importing modules: {e}")


def main():
    st.title("價值投資分析網 InvestValue")
    st.write('''
            定期自動爬取資產負債表、損益表、現金流量表及盤後資料，存入資料庫。使用者輸入公司代號後，自動繪製相關指標。以上觀點僅供參考，並不構成任何交易建議或推薦
        ''')
    
    st.write('''
             Regularly and automatically scrape balance sheets, income statements, cash flow statements, and post-market data into the database. 
             When a user enters a stock code, automatically generates relevant financial indicators and charts. The above views are for reference only and do not constitute any trading advice or recommendation.
             ''')
    st.write("")
    
    st.sidebar.markdown("""
        <style>
        section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] label {
            line-height: 1.6 !important;
            margin-bottom: 5px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 添加連結到新分頁
    page_selection = st.sidebar.radio("Go to", ["台股模型預測_TWStockForecast", "台股產業類別查詢_TWIndustryLookup", "台股指標篩選_TWFundamentalScreener", 
                                                "台股基本面財報分析_TWFinancialAnalysis", "台股基本面價值分析_TWValueAnalysis", 
                                                "台股技術面分析_TWTechnicalAnalysis",  
                                                "台股籌碼面分析_TWChipAnalysis",
                                                "國際商品與指數參照_GlobalCommodityIndex", 
                                                "美股模型預測_USStockForecast",
                                                "AI智能分析_AIInsight",  
                                                "_為什麼要投資_WhyInvest", 
                                                "_複利計算機_CompoundCalc",
                                                "_買賣交易計算機_BuySellCalc"]) 
    
    if page_selection == "台股模型預測_TWStockForecast":
        台股模型預測_TWStockForecast.main()
        
    elif page_selection == "台股產業類別查詢_TWIndustryLookup":
        台股產業類別查詢_TWIndustryLookup.main()
        
    elif page_selection == "台股指標篩選_TWFundamentalScreener":
        台股指標篩選_TWFundamentalScreener.main()
        
    elif page_selection == "台股基本面財報分析_TWFinancialAnalysis":
        台股基本面財報分析_TWFinancialAnalysis.main()
        
    elif page_selection == "台股基本面價值分析_TWValueAnalysis":
        台股基本面價值分析_TWValueAnalysis.main()
        
    elif page_selection == "台股技術面分析_TWTechnicalAnalysis":
        台股技術面分析_TWTechnicalAnalysis.main()
        
    elif page_selection == "台股籌碼面分析_TWChipAnalysis":
        台股籌碼面分析_TWChipAnalysis.main()
        
    elif page_selection == "國際商品與指數參照_GlobalCommodityIndex":
        國際商品與指數參照_GlobalCommodityIndex.main()
        
    elif page_selection == "美股模型預測_USStockForecast":
        美股模型預測_USStockForecast.main()
        
    elif page_selection == "AI智能分析_AIInsight":
        AI智能分析_AIInsight.main()
    
    elif page_selection == "_為什麼要投資_WhyInvest":
        _為什麼要投資_WhyInvest.main()
    
    elif page_selection == "_複利計算機_CompoundCalc":
        _複利計算機_CompoundCalc.main()
        
    elif page_selection == "_買賣交易計算機_BuySellCalc":
        _買賣交易計算機_BuySellCalc.main()
        
    
        


#%%
if __name__ == '__main__':
    main()
