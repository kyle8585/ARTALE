import streamlit as st
from supabase import create_client, Client
import json

# 1. 初始化 Supabase 連線 (請確保 URL 和 Key 正確)
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")
st.title("🍁 Artale 線上組隊中心")

# --- 2. 定義資料與清單 (必須放在使用它們的程式碼之前) ---
boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
grind_list = ["蛋龍"]
all_targets = pq_list + boss_list + grind_list
all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]

# --- 3. 側邊欄：發布新組隊 ---
with st.sidebar:
    st.header("📝 我要開團")
    with st.form("party_form", clear_on_submit=True):
        char_name = st.text_input("隊長 ID")
        job = st.selectbox("隊長職業", all_jobs)
        level = st.number_input("隊長等級", min_value=1, max_value=200, value=120)
        target = st.selectbox("目標", all_targets)
        note = st.text_input("備註 (例：缺僧侶、打兩小時)", placeholder="請輸入備註...")
        submit = st.form_submit_button("發布組隊")

        if submit:
            if char_name:
                data = {
                    "char_name": char_name,
                    "job": job,
                    "level": level,
                    "target": target,
                    "note": note,
                    "members": [] # 初始化成員清單為空陣列
                }
                # 從資料庫讀取資料
                try:
                    # 確保這一行結尾是 .execute()
                    response = supabase.table("party_posts").select("*").order("created_at", desc=True).execute()
                    posts = response.data
                except Exception as e:
                    st.error(f"資料讀取失敗：{e}")
                    posts = []

# --- 4. 主頁面：分類顯示 ---
tabs = st.tabs(categories)

# 從資料庫讀取資料
try:
    response = supabase.table("party_posts").select("*").order("created_at", desc=True).execute()