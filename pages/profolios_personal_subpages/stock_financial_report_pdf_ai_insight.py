import os
import re
import pdfplumber
import streamlit as st
import google.generativeai as genai

# %%
# =============== PDF => TEXT ===============
def extract_text_from_pdfs(uploaded_files, max_pages=80) -> str:
    texts = []
    for f in uploaded_files:
        try:
            with pdfplumber.open(f) as pdf:
                pages_txt = []
                for i, page in enumerate(pdf.pages, start=1):
                    if i > max_pages:
                        pages_txt.append(f"[WARNING] 僅提取前 {max_pages} 頁內容...")
                        break
                    t = page.extract_text() or ""
                    pages_txt.append(f"[PAGE {i}]\n{t}")
                text = "\n\n".join(pages_txt)
                text = re.sub(r"[ \t]+", " ", text)
                texts.append(text)
        except Exception as e:
            texts.append(f"\n[WARNING] 無法讀取 {getattr(f, 'name', 'PDF')}：{e}\n")
    return "\n\n".join(texts)


# %%
# =============== GEMINI 財務重點分析 ===============
def get_financial_analysis(api_key: str, financial_text: str):
    st.info("正在呼叫 Gemini 進行分析，請稍候...")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "models/gemini-2.5-pro",
            generation_config={
                "temperature": 0.1,  # 這裡調整 0~1，越低越保守，越高越有創意
                # "max_output_tokens": 2048,  # 可選，最大字數
                # "top_p": 1.0,               # 可選
            }
        )
    except Exception as e:
        st.error(f"初始化 Gemini 失敗：{e}")
        return None

    user_prompt = f"""
你是一位專業說中文的財報分析師
請詳細讀取公司PDF，根據三大財報資料(損益表、資產負債表、現金流量表)，協助我進行以下面向的綜合財報分析
1 公司財報基本資料
- 公司名稱、美股或台股代號、財報涵蓋時間
2 高槓桿風險分析
- 列出pdf中「ROE(股東權益報酬率)」、「權益乘數」與「負債比」等指標, 判斷該公司的高ROE是否來自過高的財務槓桿
請具體列出每個指標的數值與判斷依據,協助了解其財務結構是否穩健
3 穩健經營能力分析
- 列出pdf中「營業利益」與「營業活動產生的現金流量」,比較並判斷該公司是否具備穩健的現金流入狀況
- 若兩者差距明顯,請進一步觀察其投資現金流與自由現金流,協助解釋公司是否處於成長階段或正在大量投資擴張
4 成長型 vs 穩健型企業判斷
- 列出pdf中「營業現金流」、「投資現金流」與「自由現金流」,判斷該公司屬於哪種類型的企業
- 若為成長型,請指出其現金主要用於哪些活動
- 若為穩健型,請說明其營運現金的穩定程度與自由現金流狀況
5 是否有特別需注意的重點，若有分別條列出
6 另外列出市面上不同機構，對公司的估值，機構名稱、目標價、評價、需注意點、產業前景
---

【財報內容】
{financial_text}

---
只輸出條列，不要加前言結語

"""
    try:
        response = model.generate_content([user_prompt])
        return response.text
    except Exception as e:
        st.error(f"Gemini API 呼叫失敗：{e}")
        return None

