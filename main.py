# lsof -i :8002
# kill -9 PID
# cd swagger
# uvicorn swagger.main:app --reload --port 8002


from fastapi import FastAPI
import pandas as pd

app = FastAPI()
df_industry = pd.read_json('https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/swagger/industry.json')
df_bs = pd.read_json('https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/swagger/bs_df.json')
df_ci = pd.read_json('https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/swagger/ci_df.json')
df_cfs = pd.read_json('https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/swagger/cfs_df.json')
df_material_usunrate = pd.read_json('https://raw.githubusercontent.com/06Cata/Taiwan_Stock/main/swagger/material_usunrate.json')


@app.get("/industry/{stock_id}")
def get_industry(stock_id: str):
    # Normalize to string to avoid dtype mismatch (e.g., int vs str)
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

# @app.get("/bs/all")
# def get_bs_all():
#     import json
#     json_string = df_bs.to_json(orient="records", force_ascii=False)
#     return json.loads(json_string)

@app.get("/bs/{stock_id}")
def get_bs(stock_id: str):
    import json
    sid = str(stock_id).strip()
    code_series = df_bs['股票代號'].astype(str).str.strip()
    row = df_bs[code_series == sid]
    if row.empty:
        return {"error": "Not found"}
    # 直接回傳該公司所有資產負債表 row（通常是多個會計項目）
    # We use to_json and json.loads to ensure numpy types are converted to standard python types
    json_string = row.to_json(orient="records", force_ascii=False)
    return json.loads(json_string)

# @app.get("/ci/all")
# def get_ci_all():
#     import json
#     json_string = df_ci.to_json(orient="records", force_ascii=False)
#     return json.loads(json_string)


@app.get("/ci/{stock_id}")
def get_ci(stock_id: str):
    import json
    sid = str(stock_id).strip()
    code_series = df_ci['股票代號'].astype(str).str.strip()
    row = df_ci[code_series == sid]
    if row.empty:
        return {"error": "Not found"}
    # 直接回傳該公司所有綜合損益表 row（通常是多個會計項目）
    # We use to_json and json.loads to ensure numpy types are converted to standard python types
    json_string = row.to_json(orient="records", force_ascii=False)
    return json.loads(json_string)


# @app.get("/cfs/all")
# def get_cfs_all():
#     import json
#     json_string = df_cfs.to_json(orient="records", force_ascii=False)
#     return json.loads(json_string)

@app.get("/cfs/{stock_id}")
def get_cfs(stock_id: str):
    import json
    sid = str(stock_id).strip()
    code_series = df_cfs['股票代號'].astype(str).str.strip()
    row = df_cfs[code_series == sid]
    if row.empty:
        return {"error": "Not found"}
    # 直接回傳該公司所有現金流量表 row（通常是多個會計項目）
    # We use to_json and json.loads to ensure numpy types are converted to standard python types
    json_string = row.to_json(orient="records", force_ascii=False)
    return json.loads(json_string)


@app.get("/material_usunrate")
def get_material_usunrated():
    import json
    json_string = df_material_usunrate.to_json(orient="records", force_ascii=False)
    return json.loads(json_string)