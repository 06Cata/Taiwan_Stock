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
df_info = pd.read_json('https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/swagger/company_info.json')

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
    
@app.get("/company-info/{stock_id}")
def get_company_info(stock_id: str):
    sid = str(stock_id).strip()
    code_series = df_info['股票代號'].astype(str).str.strip()
    row = df_info[code_series == sid]
    if row.empty:
        return {"error": "Not found"}

    # 主要欄位
    stock_id = row.iloc[0].get('股票代號', '')
    stock_name = row.iloc[0].get('公司簡稱', '')
    cm_otc = row.iloc[0].get('上市櫃', '')
    stock_cm_otc_date = row.iloc[0].get('上市櫃日期', '')
    stock_industry = row.iloc[0].get('產業類別', '')
    stock_address = row.iloc[0].get('公司地址', '')
    stock_business = row.iloc[0].get('營業項目', '')
    stock_amount = row.iloc[0].get('資本額', '')
    stock_common_price = row.iloc[0].get('普通股每股面額', '')
    stock_amount_common = row.iloc[0].get('已發行普通股數', '')
    stock_amount_special = row.iloc[0].get('特別股股數', '')
    

    # 同產業相關公司 (如果需要也可排除自己)
    related = (
        df_info[df_info['產業類別'] == stock_industry][
            ['股票代號', '公司名稱', '上市櫃', '上市櫃日期', '產業類別', '公司地址', '營業項目', '資本額', '普通股每股面額', '已發行普通股數', '特別股股數']
        ]
        .astype(str)
        .to_dict('records')
    )

    return {
        "stock_id": sid,
        "stock_name": stock_name,
        "cm_otc": cm_otc,
        "stock_cm_otc_date": stock_cm_otc_date,
        "stock_industry": stock_industry,
        "stock_address": stock_address,
        "stock_business": stock_business,
        "stock_amount": stock_amount,
        "stock_common_price": stock_common_price,
        "stock_amount_common": stock_amount_common,
        "stock_amount_special": stock_amount_special,
        "related_data": related
    }
