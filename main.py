# lsof -i :8002
# kill -9 PID
# cd swagger
# uvicorn swagger.main:app --reload --port 8002
# uvicorn main:app --host 0.0.0.0 --port $PORT


# def download_drive_file_gdown(file_id, dest_path):
#     url = f"https://drive.google.com/uc?id={file_id}"
#     gdown.download(url, dest_path, quiet=False)

# def load_df_from_drive_json(file_id, local_path, always_download=False):
#     if always_download or not os.path.exists(local_path):
#         print(f"下載 {file_id} ...")
#         download_drive_file_gdown(file_id, local_path)
#     return pd.read_json(local_path)

# industry_id = "1zIk_CJaMNM9DszWnB82wUV4FIltHGygn"
# bs_ci_cfs_id = "1wCqzSRRhN9iJQxaYRWhsrM0mziVjaeB_"
# material_usunrate_id = "14XMLaPMVeZZVusG2Co1i_69LX35JmU0i"

from fastapi import FastAPI, HTTPException
import pandas as pd
import requests
import os
import json
import uvicorn

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