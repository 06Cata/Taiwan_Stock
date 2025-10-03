from fastapi import FastAPI
import pandas as pd

app = FastAPI()
df = pd.read_json('https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/swagger/industry.json')

@app.get("/industry/{stock_id}")
def get_industry(stock_id: str):
    # Normalize to string to avoid dtype mismatch (e.g., int vs str)
    sid = str(stock_id).strip()
    code_series = df['公司代號'].astype(str).str.strip()
    row = df[code_series == sid]
    if row.empty:
        return {"error": "Not found"}
    stock_name = row.iloc[0]['公司名稱']
    cm_otc = row.iloc[0]['上市櫃']
    stock_industry = row.iloc[0]['產業類別提取']
    related = df[df['產業類別提取'] == stock_industry][['公司代號', '公司名稱', '上市櫃']].to_dict('records')
    return {
        "stock_id": sid,
        "stock_name": stock_name,
        "cm_otc": cm_otc,
        "stock_industry": stock_industry,
        "related_data": related
    }
