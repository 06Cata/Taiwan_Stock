#%%
# 買賣交易計算機、複利計算機、買賣交易計算機

#%%
import pandas as pd
import math
import plotly.graph_objects as go


#%%
# 定期定額複利，年複利
def calculate_future_value_annually(initial_amount, monthly_saving, years, annual_interest_rate):
    
    annual_interest_rate_100 = int(annual_interest_rate)/100
    cumulative_values = []
    cumulative_bank_values = []
    normal_values = []
    future_value = initial_amount
    normal_value = initial_amount
    bank_value = initial_amount
    
    for year in range(years):
        annual_savings = monthly_saving * 12
        future_value += annual_savings
        future_value *= (1 + (annual_interest_rate_100))
        future_value = math.floor(future_value)
        cumulative_values.append(future_value)
        
        annual_savings = monthly_saving * 12
        bank_value += annual_savings
        bank_value *= (1 + (0.02))
        bank_value = math.floor(bank_value)
        cumulative_bank_values.append(bank_value)
        
        normal_value += annual_savings
        normal_value = math.floor(normal_value)
        normal_values.append(normal_value)

    
    years_list = list(range(1, years + 1))
    df = pd.DataFrame({'Year': years_list, 'Investment Compound Total': cumulative_values, 'Fixed Deposit 2% Total': cumulative_bank_values,'No Investment Total': normal_values})

    # 
    fig = go.Figure()


    fig.add_trace(go.Scatter(
        x=df['Year'],
        y=df['Investment Compound Total'],
        mode='lines+markers+text',
        line=dict(color='red', width=2),
        textposition='top center',
        name='Investment Compound Total'
    ))

    fig.add_trace(go.Scatter(
        x=df['Year'],
        y=df['Fixed Deposit 2% Total'],
        mode='lines+markers+text',
        line=dict(color='blue', width=2),
        textposition='top center',
        name='Fixed Deposit 2% Total'
    ))

    fig.add_trace(go.Scatter(
        x=df['Year'],
        y=df['No Investment Total'],
        mode='lines+markers+text',
        line=dict(color='mediumturquoise', width=2),
        textposition='top center',
        name='No Investment Total'
    ))


    
    f_money = df['Investment Compound Total'].iloc[-1]

 
    fig.update_layout(
        title=(
        f"<span style='font-size:18px'>"
        f"每年財產累積折線圖 Wealth Accumulation by Year<br>"
        f"</span>"
        f"<br>"
        f"<span style='font-size:14px'>"
        f"本金 {initial_amount} 元，月存 {monthly_saving} 元，年利率 {annual_interest_rate} %，如果有投資， {years} 年後可以到達 {f_money:,} 元<br>"
        f"Initial principal ${initial_amount}, monthly investment ${monthly_saving}, annual rate{annual_interest_rate}%,<br>"
        f"After {years} years, you can reach ${f_money:,} (with investment)"
        f"</span>"
        ),
        xaxis=dict(title='年 Year'),
        yaxis=dict(title='總額 Total'),
        legend=dict(
            title='',
            x=1.0,
            y=1.4,
            traceorder='normal',
            orientation='v'
        ),
        width=1200,
        height=600,
    )


    # fig.show()
    
    return df, fig




#%%
# 假設我每月投入固定金額 $_，每年帳戶總額*報酬率 %，使用折現率概念，幾年後能到達目標 $?

def calculate_years_to_goal(initial_amount, monthly_saving, annual_interest_rate, goal):
    annual_interest_rate_100 = annual_interest_rate/100
    current_balance = initial_amount
    years = 0
    cumulative_values = []

    while current_balance < goal:
        current_balance += monthly_saving * 12  # 每年投入金額
        current_balance *= (1 + annual_interest_rate_100)
        cumulative_values.append(current_balance)
        years += 1

    df = pd.DataFrame({'年 Year': range(1, years + 1), '累積金額 Accumulated Amount': cumulative_values})
    
    return df, years 



# 假設我希望__年後能到達目標__元，每年帳戶總額*報酬率__(%)，每月要投入多少__元?
def calculate_monthly_savings(initial_amount, target_amount, annual_interest_rate, years):
    # 年報酬率 -> 月報酬率
    # annual_interest_rate_new = annual_interest_rate/100
    # monthly_interest_rate = annual_interest_rate_new / 12

    # monthly_saving = (target_amount - initial_amount) / (((1 + monthly_interest_rate) ** (years * 12) - 1) / (monthly_interest_rate))
    
    annual_interest_rate_decimal = annual_interest_rate / 100  
    total_years = years                                         # 投資總年數
    future_value = target_amount                                # 目標金額（期末希望達到的金額）
    present_value = initial_amount                              # 初始本金

    # 計算每年需要投入的總金額（年金終值公式的反解）
    annual_saving = (future_value - present_value * (1 + annual_interest_rate_decimal) ** total_years) / (((1 + annual_interest_rate_decimal) ** total_years - 1) / annual_interest_rate_decimal)

    # 每月需要投入的金額
    monthly_saving = annual_saving / 12

    return monthly_saving
    
    
    
    
#%%

# 股票"購買手續費"，無條件進位 (1.425% 券商手續費)
def calculate_buying_fee(buying_stock_price, buying_quantity, discount=None):
    if discount is None:
        discount = 10
    total_buying_stock_price = buying_stock_price * buying_quantity
    buying_fee = (buying_stock_price * buying_quantity) * (1.425/1000) * (discount/10)
    buying_fee = round(buying_fee,2)
    return total_buying_stock_price, buying_fee



# 股票"賣出手續費"，無條件進位 (1.425% 券商手續費 + 0.003 證券交易稅 )
def calculate_selling_fee(selling_stock_price, selling_quantity, discount=None):
    if discount is None:
        discount = 10
    total_selling_stock_price = selling_stock_price * selling_quantity
    selling_fee = ((selling_stock_price * selling_quantity) * (1.425/1000) * (discount/10)) 
    selling_fee = round(selling_fee,2)
    selling_fee_2 = ((selling_stock_price * selling_quantity) * (3/1000))
    return total_selling_stock_price, selling_fee, selling_fee_2


# 計算獲利_台股

# def calculate_earning(choice, buy_stock_price, sell_stock_price, quantity, discount=None):
#     tax = 0
#     if choice == 1:
#         tax = 0.3
#     elif choice == 2:
#         tax = 0.1
        
#     if discount is None:
#         discount = 10
        
#     discount_new = discount/10
#     buy_price = round(buy_stock_price * quantity, 2)
#     buy_fee = round(buy_stock_price * quantity * (1.425/1000) * discount_new, 2)
#     buy = round(buy_price + buy_fee, 2)
#     sell_price = round(sell_stock_price * quantity, 2)
#     sell_fee = round(sell_stock_price * quantity * (1.425/1000) * discount_new, 2)
#     sell_fee_p = round(sell_stock_price * quantity * float(tax/100), 2)
#     sell = round(sell_price - sell_fee - sell_fee_p,2)
    
#     if discount == 10:
#         discount_show = 0
#     else: 
#         discount_show = discount_new
    
#     earning_money = round(sell_price - (buy_price + buy_fee + sell_fee + sell_fee_p),2)
#     earning_money_100 = round(((sell - buy) / buy * 100), 2)
    
#     if earning_money_100 > 0:
#         status = "賺了 Made a Profit"
#     else:
#         status = "賠了 Made a Loss"
        
#     stock_choice = ""
#     if choice == 1:
#         stock_choice = "[Stock]"
#     elif choice == 2:
#         stock_choice = "[ETF]"
        
#     return stock_choice, tax, discount_show, buy_price, buy_fee, buy, sell_price, sell_fee, sell_fee_p, sell, earning_money, earning_money_100, status


def calculate_earning(choice, buy_stock_price, sell_stock_price, quantity, discount=None):
    # choice: 1=股票, 2=ETF
    # discount: 幾折（10=無折, 5=5折）

    # 稅率
    tax = 0.3 if choice == 1 else 0.1  # 股票0.3%、ETF0.1%
    if discount is None:
        discount = 10  # 預設無折

    discount_factor = discount / 10.0
    broker_rate = 0.001425  # 0.1425%

    buy_price = round(buy_stock_price * quantity, 2)
    buy_fee = max(round(buy_price * broker_rate * discount_factor), 1)  # 最低1元
    buy = round(buy_price + buy_fee, 2)

    sell_price = round(sell_stock_price * quantity, 2)
    sell_fee = max(round(sell_price * broker_rate * discount_factor), 1)  # 最低1元
    sell_fee_p = round(sell_price * (tax / 100), 2)
    sell = round(sell_price - sell_fee - sell_fee_p, 2)

    discount_show = discount 

    earning_money = round(sell_price - (buy_price + buy_fee + sell_fee + sell_fee_p), 2)
    earning_money_100 = round(((sell - buy) / buy * 100), 2) if buy else 0

    status = "賺了 Made a Profit" if earning_money_100 > 0 else "賠了 Made a Loss"

    stock_choice = "[Stock]" if choice == 1 else "[ETF]"

    return stock_choice, tax, discount_show, buy_price, buy_fee, buy, sell_price, sell_fee, sell_fee_p, sell, earning_money, earning_money_100, status


# 計算獲利_美股
def us_calculate_earning(buy_stock_price, sell_stock_price, quantity, commission=0.0, activity_fee_per_share=0.000145, min_activity_fee=0.01):
    buy_price = round(buy_stock_price * quantity, 2)
    buy_fee = commission  # 多數主流券商0元
    buy = round(buy_price + buy_fee, 2)
    sell_price = round(sell_stock_price * quantity, 2)
    sell_fee = commission
    activity_fee = max(round(quantity * activity_fee_per_share, 4), min_activity_fee)
    sell = round(sell_price - sell_fee - activity_fee, 2)
    
    earning_money = round(sell_price - (buy_price + buy_fee + sell_fee + activity_fee), 2)
    earning_money_100 = round(((sell - buy) / buy * 100), 2) if buy else 0

    if earning_money_100 > 0:
        status = "賺了 Made a Profit"
    else:
        status = "賠了 Made a Loss"
    
    return buy_price, buy_fee, buy, sell_price, sell_fee, activity_fee, sell, earning_money, earning_money_100, status

    