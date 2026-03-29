import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. 初始化 Supabase 連線 (直接填入你的金鑰)
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")
st.title("🍁 Artale 線上組隊中心")

# --- 定義分類資料 ---
boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
pq_list = ["101 組隊任務", "時空裂縫 (Ludi)", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
grind_list = ["死龍巢穴", "大音響", "烏魯莊園", "洗血團"]
all_targets = pq_list + boss_list + grind_list

# --- 側邊欄：發布新組隊 ---
with st.sidebar:
    st.header("我要開團")
    with st.form("party_form", clear_on_submit=True):
        char_name = st.text_input("角色 ID")
        job = st.selectbox("職業", ["劍士", "英雄", "聖騎士", "黑騎士", "火毒賊", "標賊", "刀賊", "主教", "祭司", "僧侶", "弓箭手", "神射手"])
        level = st.number_input("等級", min_value=1, max_value=200, value=30)
        target = st.selectbox("目標", all_targets)
        channel = st.number_input("頻道", min_value=1, max_value=100, value=1)
        submit = st.form_submit_button("發布組隊")

        if submit:
            if char_name:
                data = {
                    "char_name": char_name,
                    "job": job,
                    "level": level,
                    "target": target,
                    "channel": channel
                }
                try:
                    supabase.table("party_posts").insert(data).execute()
                    st.success("發布成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"發布失敗：{e}")
            else:
                st.error("請輸入角色 ID")

# --- 主頁面：分類顯示 ---
categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]
tabs = st.tabs(categories)

# 從資料庫讀取資料
try:
    response = supabase.table("party_posts").select("*").order("created_at", desc=True).execute()
    posts = response.data
except Exception as e:
    st.error(f"資料讀取失敗：{e}")
    posts = []

for i, cat_name in enumerate(categories):
    with tabs[i]:
        if cat_name == "全部":
            filtered_posts = posts
        elif cat_name == "BOSS遠征":
            filtered_posts = [p for p in posts if p['target'] in boss_list]
        elif cat_name == "組隊任務":
            filtered_posts = [p for p in posts if p['target'] in pq_list]
        else: # 野外團練
            filtered_posts = [p for p in posts if p['target'] in grind_list]

        if filtered_posts:
            for p in filtered_posts:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"### 【{p['target']}】 頻道: {p['channel']}")
                        st.write(f"👤 **ID:** {p['char_name']} | 🎖️ **Lv.{p['level']}** {p['job']}")
                        st.code(f"/找人 {p['char_name']}", language="bash")
                    with col2:
                        if st.button("撤除", key=f"del_{i}_{p['id']}"):
                            supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                            st.rerun()
                    st.divider()
        else:
            st.info(f"目前沒有 {cat_name} 的隊伍。")