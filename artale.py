import streamlit as st
from supabase import create_client, Client
import json

# 1. 初始化 Supabase 連線
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")
st.title("🍁 Artale 線上組隊中心")

# --- 定義分類資料 ---
boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
grind_list = ["蛋龍"]
all_targets = pq_list + boss_list + grind_list
all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]

# --- 側邊欄：發布新組隊 ---
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
                    "members": []  # 初始化成員清單
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
        else:
            filtered_posts = [p for p in posts if p['target'] in grind_list]

        if filtered_posts:
            for p in filtered_posts:
                with st.expander(f"【{p['target']}】 {p['char_name']} 的隊伍 - 備註：{p.get('note', '無')}",
                                 expanded=True):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"👑 **隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                        st.code(f"/找人 {p['char_name']}", language="bash")

                        # 顯示已加入成員
                        members = p.get('members', [])
                        if members:
                            st.write("👥 **目前成員:**")
                            for m in members:
                                st.write(f" └ {m['name']} (Lv.{m['level']} {m['job']})")

                        # 加入功能區
                        st.divider()
                        with st.popover("➕ 我要加入此團"):
                            m_name = st.text_input("你的 ID", key=f"mname_{p['id']}")
                            m_job = st.selectbox("你的職業", all_jobs, key=f"mjob_{p['id']}")
                            m_lvl = st.number_input("你的等級", 1, 200, 100, key=f"mlvl_{p['id']}")
                            if st.button("確認加入", key=f"btn_{p['id']}"):
                                if m_name:
                                    new_member = {"name": m_name, "job": m_job, "level": m_lvl}
                                    members.append(new_member)
                                    supabase.table("party_posts").update({"members": members}).eq("id",
                                                                                                  p["id"]).execute()
                                    st.rerun()

                    with col2:
                        if st.button("撤除全團", key=f"del_{p['id']}"):
                            supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                            st.rerun()
        else:
            st.info(f"目前沒有 {cat_name} 的隊伍。")