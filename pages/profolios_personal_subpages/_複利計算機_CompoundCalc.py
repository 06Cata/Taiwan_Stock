import streamlit as st 
from pages.profolios_personal_subpages.stock_calculator import calculate_years_to_goal,calculate_monthly_savings
    

def main():
    
    st.subheader("複利計算機 Compound Interest Calculator - 1")
    st.markdown('''##### 假設我每月投入固定金額__元，每年帳戶總額*報酬率__(%)，幾年後能到達目標__元?''')
    st.markdown('''##### If I invest __ per month at an annual return of __%, how many years will it take to reach __?''')
    st.write(" ")

    col1, col2 = st.columns(2)
    with col1:
        initial_amount_str = st.text_input("初期本金\n\nInitial Principal - 1", value='0')
        monthly_saving_str = st.text_input("每月投資金額\n\nMonthly Investment - 1", value='15000')
    with col2:
        annual_interest_rate_str = st.text_input("年利率(%)\n\nAnnual Interest Rate(%) - 1", value='10')
        goal_str = st.text_input("目標金額\n\nTarget Amount - 1", value='30000000')
    st.write(" ")
    
    if st.button("送出 Submit - 1"):
        st.write(" ")
        # 先去掉 , 跟 % 跟空白
        initial_amount_val = initial_amount_str.replace(",", "").replace("%", "").strip()
        monthly_saving_val = monthly_saving_str.replace(",", "").replace("%", "").strip()
        annual_interest_rate_val = annual_interest_rate_str.replace(",", "").replace("%", "").strip()
        goal_val = goal_str.replace(",", "").replace("%", "").strip()

        # 判斷每一格是否都是「純數字」
        if not (initial_amount_val.isdigit() and monthly_saving_val.isdigit() and annual_interest_rate_val.isdigit() and goal_val.isdigit()):
            st.error("請確保所有欄位都是有效的數字 Please ensure all fields contain valid numbers")
        else:
            initial_amount = int(initial_amount_val)
            monthly_saving = int(monthly_saving_val)
            annual_interest_rate = int(annual_interest_rate_val)
            goal = int(goal_val)
            try:
                df, years = calculate_years_to_goal(initial_amount, monthly_saving, annual_interest_rate, goal)
                last_years = int(years) - 1
                st.markdown(f'''<h6>需要 {last_years}-{years} 年能累積到 {goal} 元的目標</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>You’ll need {last_years}-{years} years to accumulate your goal of {goal}</h6>''', unsafe_allow_html=True)
                st.dataframe(df)
            except Exception as e:
                st.error("運算發生錯誤 An error occurred during calculation : " + str(e))
        
        
    st.subheader("")
    

    st.subheader("複利計算機 Compound Interest Calculator - 2")
    st.markdown('''##### 假設我希望__年後能到達目標__元，每年帳戶總額*報酬率__(%)，每月要投入多少__元?''')
    st.markdown('''##### If I want to reach __ in __ years at an annual return of __%, how much should I invest per month?''')
    st.write(" ")
    
    col3, col4 = st.columns(2)
    with col3:
        initial_amount_str = st.text_input("初期本金\n\nInitial Principal - 2", value='0')
        target_amount_str = st.text_input("目標金額\n\nTarget Amount - 2", value='30000000')
    with col4:
        annual_interest_rate_str = st.text_input("年利率(%)\n\nAnnual Interest Rate(%) - 2", value='10')
        years_str = st.text_input("投資年數\n\nInvestment Period(Years) - 2", value='30')
    st.write(" ")
    
    if st.button("送出 Submit - 2"):
        st.write(" ")
        # 處理字串，去掉 , 跟空白
        initial_amount_val = initial_amount_str.replace(",", "").replace("%", "").strip()
        target_amount_val = target_amount_str.replace(",", "").replace("%", "").strip()
        annual_interest_rate_val = annual_interest_rate_str.replace(",", "").replace("%", "").strip()
        years_val = years_str.replace(",", "").replace("%", "").strip()

        # 判斷每個欄位是否全都是數字
        if not (initial_amount_val.isdigit() and target_amount_val.isdigit() and annual_interest_rate_val.isdigit() and years_val.isdigit()):
            st.error("請確保所有欄位都是有效的數字 Please ensure all fields contain valid numbers")
        else:
            initial_amount = int(initial_amount_val)
            target_amount = int(target_amount_val)
            annual_interest_rate = int(annual_interest_rate_val)
            years = int(years_val)
            try:
                monthly_saving = calculate_monthly_savings(initial_amount, target_amount, annual_interest_rate, years)
                st.markdown(f'''<h6>每月需要存入 {monthly_saving:.2f} 元</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6> Amount Needed Per Month ${monthly_saving:.2f} </h6>''', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"運算發生錯誤 An error occurred during calculation : {e}")


if __name__ == '__main__':
    main()


 