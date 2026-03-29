import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. 初始化 Supabase 連線 (保持不變)
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁")

st.title("🍁 Artale 線上組隊中心")
st.write("目前正在招募中的隊伍：")

# --- 定義分類資料 ---
# 這裡定義哪些大分類下面有什麼子目標
# 你可以隨時在這裡增加或減少項目
target_data = {
    "BOSS": ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"],
    "組隊任務": ["101 組隊任務", "時空裂縫 (Ludi)", "羅密歐與茱麗葉", "金勾海賊王", "女神"],
    "野外團練": ["死龍巢穴", "大音響", "烏魯莊園"],
    "其他": ["洗血團", "買賣幣"]
}

# 職業清單
jobs = [
    "英雄", "聖騎", "黑騎",
    "火毒", "冰雷", "主教",
    "刀賊", "標賊",
    "弓手", "弩手",
    "拳霸", "槍神"
]

# --- 側邊欄：發布新組隊 ---
with st.sidebar:
    st.header("我要開團")

    # 1. 角色 ID (移到外面，或是留在裡面都可以，建議移到外面可以即時預覽)
    char_name = st.text_input("角色 ID")

    # 2. 職業
    job = st.selectbox("職業", jobs)

    # 3. 等級
    level = st.number_input("等級", min_value=1, max_value=200, value=30)

    # --- 關鍵修改：將目標選擇移出 st.form ---
    # 4. 目標大分類
    main_category = st.selectbox("目標分類", list(target_data.keys()))

    # 5. 子目標 (現在這裡會即時連動了！)
    available_sub_targets = target_data[main_category]
    target = st.selectbox(f"{main_category} 具體項目", available_sub_targets)

    # 6. 頻道
    channel = st.number_input("頻道", min_value=1, max_value=100, value=1)

    # 7. 開打時間
    start_time = st.text_input("開打時間")

    # 提交按鈕：現在只需要一個簡單的 button，不需要 st.form
    if st.button("發布組隊"):
        if not char_name:
            st.error("請輸入角色 ID")
        else:
            data = {
                "char_name": char_name,
                "job": job,
                "level": level,
                "target": target,
                "channel": channel
            }
            supabase.table("party_posts").insert(data).execute()
            st.success("發布成功！")
            st.rerun()

# --- 主頁面：顯示組隊列表 (保持不變) ---
# ... (這裡的程式碼跟原本的一樣，我就不重複貼了)