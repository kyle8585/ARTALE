import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# 1. 初始化 Supabase
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")
st.title("🍁 Artale 線上組隊中心")

# --- 2. 定義清單 ---
all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
grind_list = ["蛋龍"]
all_targets = pq_list + boss_list + grind_list
categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]

# --- 3. 側邊欄：發布新組隊 ---
with st.sidebar:
    st.header("📝 我要開團")
    with st.form("party_form", clear_on_submit=True):
        new_title = st.text_input("隊伍標題", placeholder="例如：101 五場速刷")
        char_name = st.text_input("隊長 ID")
        job = st.selectbox("隊長職業", all_jobs)
        level = st.number_input("隊長等級", 1, 200, 120)
        target = st.selectbox("目標", all_targets)
        note = st.text_input("備註")
        submit = st.form_submit_button("發布組隊")

        if submit and char_name:
            data = {
                "title": new_title if new_title else f"{char_name} 的組隊",
                "char_name": char_name,
                "job": job,
                "level": level,
                "target": target,
                "note": note,
                "members": [],
                "messages": []
            }
            supabase.table("party_posts").insert(data).execute()
            st.success("發布成功！")
            st.rerun()

# --- 4. 主頁面：讀取資料 ---
tabs = st.tabs(categories)
try:
    response = supabase.table("party_posts").select("*").order("created_at", desc=True).execute()
    posts = response.data if response.data else []
except:
    posts = []

# --- 5. 渲染列表 ---
for i, cat_name in enumerate(categories):
    with tabs[i]:
        if cat_name == "全部":
            filtered = posts
        elif cat_name == "BOSS遠征":
            filtered = [p for p in posts if p['target'] in boss_list]
        elif cat_name == "組隊任務":
            filtered = [p for p in posts if p['target'] in pq_list]
        else:
            filtered = [p for p in posts if p['target'] in grind_list]

        if not filtered:
            st.info(f"目前沒有 {cat_name} 的隊伍。")
            continue

        for p in filtered:
            m_list = p.get('members', [])
            member_count = len(m_list) + 1  # 隊員 + 1位隊長

            # 摺疊標題設計
            expander_title = f"【{p['target']}】 {p.get('title', '無標題')} ｜ 👑 {p['char_name']} ｜ 👥 {member_count}/6"

            with st.expander(expander_title, expanded=False):
                # 內部資訊排版
                col_info, col_chat = st.columns([1, 1])

                # 左側：成員與管理
                with col_info:
                    st.markdown(f"**👑 隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                    if p.get('note'):
                        st.caption(f"📝 備註: {p['note']}")
                    st.code(f"/找人 {p['char_name']}", language="bash")

                    st.divider()
                    st.write("👥 **隊員清單:**")
                    if m_list:
                        for idx, m in enumerate(m_list):
                            mc1, mc2 = st.columns([4, 1])
                            mc1.write(f" └ {m['name']} (Lv.{m.get('level', '??')} {m['job']})")
                            if mc2.button("❌", key=f"kick_{cat_name}_{p['id']}_{idx}"):
                                new_m_list = [member for i_m, member in enumerate(m_list) if i_m != idx]
                                supabase.table("party_posts").update({"members": new_m_list}).eq("id",
                                                                                                 p["id"]).execute()
                                st.rerun()
                    else:
                        st.caption("目前尚無隊員")

                    # 功能按鈕
                    st.write("")
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        with st.popover("➕ 加入", use_container_width=True):
                            m_name = st.text_input("你的 ID", key=f"in_{p['id']}")
                            m_job = st.selectbox("職業", all_jobs, key=f"ij_{p['id']}")
                            m_lvl = st.number_input("等級", 1, 200, 100, key=f"il_{p['id']}")
                            if st.button("確認加入", key=f"ib_{p['id']}", use_container_width=True):
                                if m_name:
                                    m_list.append({"name": m_name, "job": m_job, "level": m_lvl})
                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                 p["id"]).execute()
                                    st.rerun()
                    with b2:
                        with st.popover("✏️ 標題", use_container_width=True):
                            edit_t = st.text_input("修改標題", value=p.get('title', ''), key=f"et_{p['id']}")
                            if st.button("儲存", key=f"eb_{p['id']}", use_container_width=True):
                                supabase.table("party_posts").update({"title": edit_t}).eq("id", p["id"]).execute()
                                st.rerun()
                    with b3:
                        if st.button("🗑️ 撤團", key=f"del_{p['id']}", use_container_width=True):
                            supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                            st.rerun()

                # 右側：聊天室
                with col_chat:
                    st.write("💬 **隊伍聊天室**")
                    chat_box = st.container(height=180)
                    msg_list = p.get('messages', [])
                    with chat_box:
                        if not msg_list: st.caption("目前尚無訊息...")
                        for m in msg_list:
                            st.markdown(f"**{m['user']}:** {m['text']}")

                    with st.form(key=f"chat_f_{p['id']}", clear_on_submit=True):
                        c1, c2 = st.columns([4, 1])
                        u_msg = c1.text_input("訊息", placeholder="打聲招呼吧", key=f"msg_in_{p['id']}")
                        if c2.form_submit_button("送出") and u_msg:
                            sender = st.session_state.get(f"in_{p['id']}", "匿名")
                            msg_list.append({"user": sender if sender else "匿名", "text": u_msg})
                            supabase.table("party_posts").update({"messages": msg_list}).eq("id", p["id"]).execute()
                            st.rerun()