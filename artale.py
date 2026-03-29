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
        # 分類過濾
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
            with st.container(border=True):
                # 標題與基本資訊
                col_head, col_del = st.columns([5, 1])
                with col_head:
                    st.subheader(f"【{p['target']}】 {p.get('title', '無標題')}")
                with col_del:
                    if st.button("撤除全團", key=f"del_{cat_name}_{p['id']}"):
                        supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                        st.rerun()

                col1, col2 = st.columns([1, 1])

                # 左側：隊伍成員資訊
                with col1:
                    st.markdown(f"👑 **隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                    st.caption(f"📝 備註: {p.get('note', '無')}")
                    st.code(f"/找人 {p['char_name']}", language="bash")

                    # 顯示隊員
                    m_list = p.get('members', [])
                    if m_list:
                        st.write("👥 **隊員清單:**")
                        for m in m_list:
                            st.write(f" └ {m['name']} (Lv.{m['level']} {m['job']})")

                    # 修改標題與加入按鈕
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        with st.popover("➕ 加入隊伍", use_container_width=True):
                            m_name = st.text_input("你的 ID", key=f"in_{cat_name}_{p['id']}")
                            m_job = st.selectbox("職業", all_jobs, key=f"ij_{cat_name}_{p['id']}")
                            if st.button("確認加入", key=f"ib_{cat_name}_{p['id']}"):
                                m_list.append({"name": m_name, "job": m_job, "level": 0})
                                supabase.table("party_posts").update({"members": m_list}).eq("id", p["id"]).execute()
                                st.rerun()
                    with c_btn2:
                        with st.popover("✏️ 修改標題", use_container_width=True):
                            edit_t = st.text_input("新標題", value=p.get('title', ''), key=f"et_{cat_name}_{p['id']}")
                            if st.button("儲存修改", key=f"eb_{cat_name}_{p['id']}"):
                                supabase.table("party_posts").update({"title": edit_t}).eq("id", p["id"]).execute()
                                st.rerun()

                # 右側：小聊天室
                with col2:
                    st.write("💬 **隊伍聊天室**")
                    chat_container = st.container(height=150)
                    msg_list = p.get('messages', [])

                    with chat_container:
                        if not msg_list: st.caption("目前尚無訊息...")
                        for m in msg_list:
                            st.markdown(f"**{m['user']}:** {m['text']}")

                    # 傳送訊息
                    with st.form(key=f"chat_form_{cat_name}_{p['id']}", clear_on_submit=True):
                        c_col1, c_col2 = st.columns([3, 1])
                        user_msg = c_col1.text_input("說點什麼...", key=f"mi_{cat_name}_{p['id']}")
                        send_btn = c_col2.form_submit_button("傳送")
                        if send_btn and user_msg:
                            new_msg = {
                                "user": st.session_state.get(f"in_{cat_name}_{p['id']}", "匿名"),
                                "text": user_msg,
                                "time": datetime.now().strftime("%H:%M")
                            }
                            msg_list.append(new_msg)
                            supabase.table("party_posts").update({"messages": msg_list}).eq("id", p["id"]).execute()
                            st.rerun()