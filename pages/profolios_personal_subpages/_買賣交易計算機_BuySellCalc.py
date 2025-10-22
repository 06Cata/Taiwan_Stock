import streamlit as st 
import math
from pages.profolios_personal_subpages.stock_calculator import calculate_earning, us_calculate_earning

def main():
    # --- 台股 ---
    st.subheader("台股買賣交易計算機 TW Stock Buy/Sell Calculator")
    st.write('''購買股票 : 0.1425% 券商手續費  
                賣出股票 : 0.1425% 券商手續費 + 0.3% 證券交易稅 (ETF 0.1%)''')
    st.write('''Buying Stocks: 0.1425% broker fee   
                Selling Stocks: 0.1425% broker fee + 0.3% transaction tax (ETF: 0.1%)''')
    st.write(" ")

    # choice = float(st.text_input("股票:1、ETF:2", value='1'))
    choice_label = st.selectbox("請選擇商品", ["股票 Stock", "ETF"])
    choice = 1 if choice_label == "股票 Stock" else 2

    # buy_stock_price_str = st.text_input("買入金額\n\nBuy Amount", value='10')
    # quantity_str = st.text_input("股數\n\nShares", value='1000')
    # sell_stock_price_str = st.text_input("賣出金額\n\nSell Amount", value='15')
    # discount_str = st.text_input("券商折扣_(折)，沒有則放置10\n\nBroker Discount (e.g. 10 for none)", value='10')
    col1, col2 = st.columns(2)
    with col1:
        buy_stock_price_str = st.text_input("買入金額(TWD)\n\nBuy Amount (TWD)", value='10')
        quantity_str = st.text_input("股數\n\nShares", value='1000')
    with col2:
        sell_stock_price_str = st.text_input("賣出金額(TWD)\n\nSell Amount (TWD)", value='15')
        discount_str = st.text_input("券商折扣_(折)，沒有則放置10\n\nBroker Discount (e.g. 10 for none)", value='10')

    st.write(" ")
            
    if st.button("送出 Submit (TW)"):
        st.write(" ")
        # 處理字串，去掉 , 跟空白
        buy_stock_price_val = buy_stock_price_str.replace(",", "").replace("%", "").strip()
        quantity_val = quantity_str.replace(",", "").replace("%", "").strip()
        sell_stock_price_val = sell_stock_price_str.replace(",", "").replace("%", "").strip()
        discount_val = discount_str.replace(",", "").replace("%", "").strip()

        # 判斷每個欄位是否全都是數字
        if not (buy_stock_price_val.isdigit() and quantity_val.isdigit() and sell_stock_price_val.isdigit() and discount_val.isdigit()):
            st.error("請確保所有欄位都是有效的數字 Please ensure all fields contain valid numbers")
        else:
            buy_stock_price_amount = int(buy_stock_price_val)
            quantity_amount = int(quantity_val)
            sell_stock_price_amount = int(sell_stock_price_val)
            discount_amount = int(discount_val)
                
            try:
                stock_choice, tax, discount_show, buy_price, buy_fee, buy, sell_price, sell_fee, sell_fee_p, sell, earning_money, earning_money_100, status = calculate_earning(
                    choice, buy_stock_price_amount, sell_stock_price_amount, quantity_amount, discount_amount
                )
                
                if earning_money_100 < 0:
                    status_color = "green"
                elif earning_money_100 > 0:
                    status_color = "red"
                else:
                    status_color = "black"
            
                status_text = f"{status} {earning_money_100}%"
                colored_status_text = f"<font color='{status_color}'>{status_text}</font>"

                st.markdown(f'''<h6>{stock_choice} 券商折扣{discount_show}折，證交稅為{tax}%</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>買入股票淨值為 ${buy_price}，買進手續費為 ${buy_fee}，買入所需為 ${buy}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>賣出股票淨值為 ${sell_price}，賣出手續費為 ${sell_fee}，證交稅為 ${sell_fee_p}，賣出所得為 ${sell}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>利潤(虧損) ${earning_money}，{colored_status_text}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''''')
                st.markdown(f'''<h6>{stock_choice} Broker Discount: {discount_show}, Transaction Tax: {tax}%</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>Buy Stock Net Value: ${buy_price}, Buy Fee: ${buy_fee}, Total Buy Cost: ${buy}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>Sell Stock Net Value: ${sell_price}, Sell Fee: ${sell_fee}, Transaction Tax: ${sell_fee_p}, Total Sell Proceeds: ${sell}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>Profit (Loss): ${earning_money}, {colored_status_text}</h6>''', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"運算發生錯誤 An error occurred during calculation : {e}")


    st.subheader("")
        
    ## --- 美股 ---
    st.subheader("美股買賣交易計算機 US Stock Buy/Sell Calculator")
    st.markdown('''
    美股主流券商無手續費，僅收監管費  
    賣出端每股 \\$0.000145，最低 \\$0.01  
    買賣股票、ETF算法完全一致  
    不含匯費、平台費、ADR費等  
    ''')
    st.markdown('''
    US major brokers offer zero commission trades  
    Regulatory fee: \\$0.000145 per share when selling, minimum \\$0.01  
    Stocks and ETFs use the same calculation method  
    Currency/ADR/platform fees not included  
    ''')

    st.write(" ")

    col5, col6 = st.columns(2)
    with col5:
        us_buy_stock_price_str = st.text_input("買入金額(USD)\n\nBuy Price (USD)", value='10', key="us_buy")
        us_quantity_str = st.text_input("股數\n\nShares", value='100', key="us_qty")
    with col6:
        us_sell_stock_price_str = st.text_input("賣出金額(USD)\n\nSell Price (USD)", value='12', key="us_sell")

    if st.button("送出 Submit (US)"):
        st.write(" ")
        # 處理字串，去掉 , 跟空白
        us_buy_stock_price_val = us_buy_stock_price_str.replace(",", "").replace("%", "").strip()
        us_quantity_val = us_quantity_str.replace(",", "").replace("%", "").strip()
        us_sell_stock_price_val = us_sell_stock_price_str.replace(",", "").replace("%", "").strip()

        if not (us_buy_stock_price_val.replace('.', '', 1).isdigit() and
                us_quantity_val.replace('.', '', 1).isdigit() and
                us_sell_stock_price_val.replace('.', '', 1).isdigit()):
            st.error("請確保所有欄位都是有效的數字 Please ensure all fields contain valid numbers")
            st.stop()
        else:
            us_buy_stock_price = float(us_buy_stock_price_val)
            us_quantity = float(us_quantity_val)
            us_sell_stock_price = float(us_sell_stock_price_val)
            
            try:
                buy_price, buy_fee, buy, sell_price, sell_fee, activity_fee, sell, earning_money, earning_money_100, status = us_calculate_earning(
                    us_buy_stock_price, us_sell_stock_price, us_quantity)
            
                status_color = "red" if earning_money_100 > 0 else "green" if earning_money_100 < 0 else "black"
                status_text = f"{status} {earning_money_100}%"
                colored_status_text = f"<font color='{status_color}'>{status_text}</font>"

                st.markdown(f'''<h6>買入股票總額 ${buy_price}，買進手續費 ${buy_fee}，買入所需 ${buy}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>賣出股票總額 ${sell_price}，賣出手續費 ${sell_fee}，監管費 ${activity_fee}，賣出所得 ${sell}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>利潤(虧損) ${earning_money}，{colored_status_text}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''''')
                st.markdown(f'''<h6>Buy Stock Net Value: ${buy_price}, Buy Fee: ${buy_fee}, Total Buy Cost: ${buy}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>Sell Stock Net Value: ${sell_price}, Sell Fee: ${sell_fee}, Regulatory Fee: ${activity_fee}, Total Sell Proceeds: ${sell}</h6>''', unsafe_allow_html=True)
                st.markdown(f'''<h6>Profit (Loss): ${earning_money}, {colored_status_text}</h6>''', unsafe_allow_html=True)

            except Exception as e:
                st.error("運算發生錯誤 An error occurred during calculation : {e}")
                st.stop()

if __name__ == '__main__':
    main()
