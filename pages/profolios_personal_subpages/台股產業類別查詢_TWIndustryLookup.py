import streamlit as st 
from urllib.parse import quote
from requests.exceptions import HTTPError
import random
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import io
import os
import json
import pandas as pd
import numpy as np
import datetime
import time, random
from datetime import datetime
import random
import sqlite3
import unicodedata
import json
import tempfile

import plotly.figure_factory as ff
import plotly.graph_objects as go
import plotly.express as px


def download_sqlite_from_github(url):
    import requests, tempfile
    r = requests.get(url)
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(r.content)
    f.close()
    return f.name

def main():
    st.subheader("台股產業類別查詢 TW Stock Industry Lookup - On the way")
    industry_db_path = 'https://github.com/06Cata/Taiwan_Stock/raw/main/industry.sqlite3'
    industry_db_path_download = download_sqlite_from_github(industry_db_path)

    industry_table = 'industry'

    with sqlite3.connect(industry_db_path_download) as conn:
        df = pd.read_sql(f"SELECT 公司代號, 公司名稱, 上市櫃, 產業類別提取 FROM {industry_table}", conn)

    # 找出有哪些產業類別
    all_industry = df['產業類別提取'].dropna().unique()
    industry_selected = st.selectbox(
        "請選擇產業類別，或依照近期熱門題材查看\n\n"
        "Please select an industry category, or browse by recent trending topics.",
        all_industry
    )
    st.write(" ")
    
    # 選到產業，分上市/上櫃顯示
    df_filtered = df[df['產業類別提取'] == industry_selected]

    st.write(f"### {industry_selected}（上市）")
    st.dataframe(df_filtered[df_filtered['上市櫃']=='上市'].reset_index(drop=True))
    st.write(" ")
    st.write(" ")
    
    st.write(f"### {industry_selected}（上櫃）")
    st.dataframe(df_filtered[df_filtered['上市櫃']=='上櫃'].reset_index(drop=True))


if __name__ == '__main__':
    main()