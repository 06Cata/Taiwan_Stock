# lsof -i :8002
# kill -9 PID
# cd swagger
# uvicorn swagger.main:app --reload --port 8002
# uvicorn main:app --host 0.0.0.0 --port 8000
from fastapi import FastAPI, HTTPException
import pandas as pd
import requests
import os

df_industry = None  # 一開始 None
JSON_URL = 'https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/swagger/industry.json'

def load_df():
    global df_industry
    try:
        r = requests.get(JSON_URL, timeout=10)
        r.raise_for_status()
        df_industry = pd.read_json(r.content)
    except Exception as e:
        print(f"[load_df] Failed: {e}")
        df_industry = None

app = FastAPI()

@app.on_event("startup")
def startup_event():
    load_df()

@app.get("/health")
def health():
    return {"ok": df_industry is not None}

@app.get("/industry/{stock_id}")
def get_industry(stock_id: str):
    if df_industry is None:
        raise HTTPException(status_code=503, detail="資料尚未載入")
    sid = str(stock_id).strip()
    code_series = df_industry['公司代號'].astype(str).str.strip()
    row = df_industry[code_series == sid]
    if row.empty:
        return {"error": "Not found"}
    stock_name = row.iloc[0]['公司名稱']
    cm_otc = row.iloc[0]['上市櫃']
    stock_industry = row.iloc[0]['產業類別提取']
    related = df_industry[df_industry['產業類別提取'] == stock_industry][['公司代號', '公司名稱', '上市櫃']].to_dict('records')
    return {
        "stock_id": sid,
        "stock_name": stock_name,
        "cm_otc": cm_otc,
        "stock_industry": stock_industry,
        "related_data": related
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
