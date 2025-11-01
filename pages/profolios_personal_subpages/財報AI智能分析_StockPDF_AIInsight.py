import os
# import re
# import pdfplumber
# import streamlit as st

# # Gemini
# import google.generativeai as genai
# # OpenAI
# import openai

# # =============== PDF => TEXT ===============
# def extract_text_from_pdfs(uploaded_file, max_pages=80) -> str:
#     texts = []
#     try:
#         with pdfplumber.open(uploaded_file) as pdf:
#             pages_txt = []
#             for i, page in enumerate(pdf.pages, start=1):
#                 if i > max_pages:
#                     pages_txt.append(f"[WARNING] 僅提取前 {max_pages} 頁內容...")
#                     break
#                 t = page.extract_text() or ""
#                 pages_txt.append(f"[PAGE {i}]\n{t}")
#             text = "\n\n".join(pages_txt)
#             text = re.sub(r"[ \t]+", " ", text)
#             texts.append(text)
#     except Exception as e:
#         texts.append(f"\n[WARNING] 無法讀取 {getattr(uploaded_file, 'name', 'PDF')}：{e}\n")
#     return "\n\n".join(texts)

# # =============== GEMINI 財務重點分析 ===============
# def get_gemini_analysis(api_key: str, financial_text: str):
#     st.info("正在呼叫 Gemini 進行分析，請稍候...")
#     try:
#         genai.configure(api_key=api_key)
#         model = genai.GenerativeModel(
#             "models/gemini-2.5-pro",
#             generation_config={
#                 "temperature": 0.1
#             }
#         )
#     except Exception as e:
#         st.error(f"初始化 Gemini 失敗：{e}")
#         return None

#     user_prompt = f"""
# 你是一位專業說中文的財報分析師
# 請詳細讀取公司PDF，根據三大財報資料(損益表、資產負債表、現金流量表),協助我進行以下綜合財報分析
# 先列出公司名稱，美股或台股代號，財報涵蓋時間
# 1 高槓桿風險分析
# - 列出pdf中「ROE(股東權益報酬率)」、「權益乘數」與「負債比」等指標, 判斷該公司的高ROE是否來自過高的財務槓桿
# 請具體列出每個指標的數值與判斷依據,協助了解其財務結構是否穩健
# 2 穩健經營能力分析
# - 列出pdf中「營業利益」與「營業活動產生的現金流量」,比較並判斷該公司是否具備穩健的現金流入狀況
# - 若兩者差距明顯,請進一步觀察其投資現金流與自由現金流,協助解釋公司是否處於成長階段或正在大量投資擴張
# 3 成長型 vs 穩健型企業判斷
# - 列出pdf中「營業現金流」、「投資現金流」與「自由現金流」,判斷該公司屬於哪種類型的企業
# - 若為成長型,請指出其現金主要用於哪些活動
# - 若為穩健型,請說明其營運現金的穩定程度與自由現金流狀況
# 4 是否有特別需注意的重點，若有分別條列出
# 5 列出不同的機構對該公司的估值，機構名稱、目標價、評價、需注意點、產業前景
# ---
# 【財報內容】
# {financial_text}
# ---
# 只輸出條列與標題，不要加前言結語
# """
#     try:
#         response = model.generate_content([user_prompt])
#         return response.text
#     except Exception as e:
#         st.error(f"Gemini API 呼叫失敗：{e}")
#         return None

# # =============== OPENAI 財務重點分析 ===============
# def get_openai_analysis(api_key: str, financial_text: str):
#     st.info("正在呼叫 OpenAI 進行分析，請稍候...")
#     openai.api_key = api_key
#     user_prompt = f"""
# 你是一位專業說中文的財報分析師
# 請詳細讀取公司PDF，根據三大財報資料(損益表、資產負債表、現金流量表),協助我進行以下綜合財報分析
# 先列出公司名稱，美股或台股代號，財報涵蓋時間
# 1 高槓桿風險分析
# - 列出pdf中「ROE(股東權益報酬率)」、「權益乘數」與「負債比」等指標, 判斷該公司的高ROE是否來自過高的財務槓桿
# 請具體列出每個指標的數值與判斷依據,協助了解其財務結構是否穩健
# 2 穩健經營能力分析
# - 列出pdf中「營業利益」與「營業活動產生的現金流量」,比較並判斷該公司是否具備穩健的現金流入狀況
# - 若兩者差距明顯,請進一步觀察其投資現金流與自由現金流,協助解釋公司是否處於成長階段或正在大量投資擴張
# 3 成長型 vs 穩健型企業判斷
# - 列出pdf中「營業現金流」、「投資現金流」與「自由現金流」,判斷該公司屬於哪種類型的企業
# - 若為成長型,請指出其現金主要用於哪些活動
# - 若為穩健型,請說明其營運現金的穩定程度與自由現金流狀況
# 4 是否有特別需注意的重點，若有分別條列出
# 5 列出不同的機構對該公司的估值，機構名稱、目標價、評價、需注意點、產業前景
# ---
# 【財報內容】
# {financial_text}
# ---
# 只輸出條列與標題，不要加前言結語
# """
#     try:
#         completion = openai.chat.completions.create(
#             model="gpt-4",
#             messages=[{"role": "system", "content": "你是一位專業說中文的財報分析師"},
#                       {"role": "user", "content": user_prompt}],
#             temperature=0.1
#         )
#         return completion.choices[0].message.content
#     except Exception as e:
#         st.error(f"OpenAI API 呼叫失敗：{e}")
#         return None

# # =============== STREAMLIT APP ===============
# def main():
#     st.set_page_config(
#         page_title="多模型 財報重點分析",
#         layout="wide",
#         initial_sidebar_state="expanded"
#     )

#     st.title("財報自動條列重點分析")
#     st.caption("選擇 Gemini 或 OpenAI，上傳財報 PDF，取得條列重點")

#     # ========= 主頁表單 =========
#     with st.form("main_form", clear_on_submit=False):
#         st.markdown("#### 輸入分析條件")
#         model_source = st.selectbox(
#             "選擇分析模型", options=["Gemini", "OpenAI"]
#         )
#         api_key = st.text_input(f"{model_source} API Key", type="password")
#         uploaded_file = st.file_uploader(
#             "上傳財報 PDF", 
#             type=["pdf"], 
#             accept_multiple_files=False
#         )
#         submitted = st.form_submit_button("條列重點分析")

#     if submitted:
#         if not api_key:
#             st.warning("請輸入 API Key。")
#             return
#         if not uploaded_file:
#             st.warning("請上傳 PDF 檔案。")
#             return

#         with st.spinner("提取 PDF 文字..."):
#             financial_text = extract_text_from_pdfs(uploaded_file)

#         with st.expander("查看提取文字（前 5000 字）"):
#             st.code(financial_text[:5000] + "...", language="markdown")

#         if model_source == "Gemini":
#             analysis_result = get_gemini_analysis(api_key, financial_text)
#         elif model_source == "OpenAI":
#             analysis_result = get_openai_analysis(api_key, financial_text)
#         else:
#             st.error("未支援的模型來源")
#             return

#         if analysis_result:
#             st.success("條列重點分析完成")
#             st.markdown(analysis_result)
#         else:
#             st.error("分析失敗，請檢查 API Key 或檔案內容格式")

#     st.markdown("---")
#     st.markdown("本工具可選擇 Google Gemini 或 OpenAI，僅供參考不構成投資建議")

# if __name__ == "__main__":
#     main()


import os
import re
import pdfplumber
import streamlit as st
import google.generativeai as genai

from pages.profolios_personal_subpages.tw_us_stock_financial_report_pdf_ai_insight import extract_text_from_pdfs, get_financial_analysis


# =============== STREAMLIT APP ===============
def main():
    st.set_page_config(
        page_title="財報重點分析",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.subheader("財報AI智能分析 Stock PDF AI Insight")
    st.write("""
        請自行申請 **[Gemini API Key](https://aistudio.google.com/)**，系統生成一份由 AI 撰寫的財務報告，[參考檔案](https://drive.google.com/drive/folders/1E4BOclNnGn0_ly3a1opP9V6Oku3snT8t?usp=sharing)，以上觀點僅供參考，並不構成任何交易建議或推薦
    """)
    # st.caption("輸入 Gemini API Key，上傳財務報告 PDF，取得條列重點")
    
    # ========= 主頁表單 =========
    with st.form("main_form", clear_on_submit=False):
        st.markdown("###### 分析設定")
        api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
        uploaded_files = st.file_uploader(
            "上傳公司財報 PDF", 
            type=["pdf"], 
            accept_multiple_files=False
        )
        submitted = st.form_submit_button("條列重點分析")

    if submitted:
        if not api_key:
            st.warning("請輸入 Gemini API Key。")
            return
        if not uploaded_files:
            st.warning("請上傳 PDF 檔案。")
            return

        with st.spinner("提取 PDF 文字..."):
            financial_text = extract_text_from_pdfs([uploaded_files])
            
        # 
        st.write(f"財報（{len(financial_text)}字）")
        
        # 
        MAX_CHARS = 120000  # 實測安全長度
        if len(financial_text) > MAX_CHARS:
            st.warning(f"財報內容過長（{len(financial_text)}字），僅分析前 {MAX_CHARS} 字。")
            financial_text = financial_text[:MAX_CHARS]


        with st.expander("查看提取文字（前 5000 字）"):
            st.code(financial_text[:5000] + "...", language="markdown")

        analysis_result = get_financial_analysis(api_key, financial_text)

        if analysis_result:
            st.success("條列重點分析完成")
            st.markdown(analysis_result)
        else:
            st.error("分析失敗，請檢查 API Key 或檔案內容格式")


if __name__ == "__main__":
    main()


