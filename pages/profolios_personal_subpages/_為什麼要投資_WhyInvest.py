import streamlit as st 
from pages.profolios_personal_subpages.stock_calculator import calculate_future_value_annually

def main():
    st.subheader("為什麼要投資? Why invest?")
    st.write('''很多股票、ETF長期都有年利率 4% 以上，遠遠高於定存的 1-2%。試試看，買零股，複利再投入，一個月只投 3000-5000 也有差別 !''')
    st.write('''Many stocks and ETFs have long-term annual returns over 4%, much higher than fixed deposits. Try buying fractional shares and reinvesting; even investing just 3,000–5,000 a month can add up!''')
    st.write(" ")

#     initial_amount = int(st.text_input("初期本金(元)\n\nInitial Principal", value='0'))
#     monthly_saving = int(st.text_input("每月投資金額(元)\n\nMonthly Investment", value='5000'))
#     years = int(st.text_input("投資年數\n\nInvestment Period(Years)", value='30'))
#     annual_interest_rate = float(st.text_input("年利率(%)\n\nAnnual Interest Rate(%)", value='10'))
#     st.write(" ")
    
#     if st.button("送出 Submit"):
#         try:
#             df, fig = calculate_future_value_annually(initial_amount, monthly_saving, years, annual_interest_rate)
#         except:
#             st.error("請確保所有欄位都是有效的數字 Please ensure all fields contain valid numbers.")
            
#         st.dataframe(df) 
#         st.write(" ")
#         st.plotly_chart(fig) 
    
    col1, col2 = st.columns(2)
    with col1:
        initial_amount_str = st.text_input("初期本金\n\nInitial Principal", value='0')
        monthly_saving_str = st.text_input("每月投資金額\n\nMonthly Investment", value='5000')
    with col2:
        years_str = st.text_input("投資年數\n\nInvestment Period(Years)", value='30')
        annual_interest_rate_str = st.text_input("年利率(%)\n\nAnnual Interest Rate(%)", value='10')
    st.write(" ")

    if st.button("送出 Submit"):
        st.write(" ")
        # 驗證所有欄位都是有效數字（float ok）
        try:
            initial_amount = int(initial_amount_str.replace(",", "").strip())
            monthly_saving = int(monthly_saving_str.replace(",", "").strip())
            years = int(years_str.replace(",", "").strip())
            annual_interest_rate = float(annual_interest_rate_str.replace(",", "").strip())
            df, fig= calculate_future_value_annually(initial_amount, monthly_saving, years, annual_interest_rate)
            st.dataframe(df)
            st.write(" ")
            st.write(" ")
            st.plotly_chart(fig) # , use_container_width=True
        except Exception as e:
            st.error("請確保所有欄位都是有效的數字 Please ensure all fields contain valid numbers")

if __name__ == '__main__':
    main()
