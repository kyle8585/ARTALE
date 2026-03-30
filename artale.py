import streamlit as st
from supabase import create_client, Client

# 1. 初始化 Supabase
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# --- 2. 身份驗證邏輯 ---
if 'user' not in st.session_state:
    st.session_state.user = None


def login_page():
    st.title("🔐 歡迎來到 Artale 組隊中心")
    tab1, tab2 = st.tabs(["登入帳號", "申請帳號"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("電子信箱 (Email)")
            password = st.text_input("密碼", type="password")
            if st.form_submit_button("登入", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception as e:
                    st.error(f"登入失敗: {e}")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("電子信箱 (作為帳號)")
            new_pw = st.text_input("設定密碼", type="password", help="至少 6 位數")
            if st.form_submit_button("立即申請", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": new_email, "password": new_pw})
                    st.success("申請成功！現在可以切換到登入分頁了。")
                except Exception as e:
                    st.error(f"申請失敗: {e}")


# --- 3. 主程式頁面 ---
def main_app():
    user = st.session_state.user
    st.sidebar.write(f"👋 歡迎, {user.email}")
    if st.sidebar.button("登出"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.title("🍁 Artale 線上組隊中心")

    # 定義清單與分類 (與之前相同)
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
    all_targets = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神", "拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王",
                   "蛋龍"]
    categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]

    # 側邊欄：開團 (自動記錄 UID)
    with st.sidebar:
        st.header("📝 我要開團")
        with st.form("party_form", clear_on_submit=True):
            new_title = st.text_input("隊伍標題")
            char_name = st.text_input("遊戲 ID")
            target = st.selectbox("目標", all_targets)
            submit = st.form_submit_button("發布組隊", use_container_width=True)
            if submit and char_name:
                data = {
                    "title": new_title if new_title else f"{char_name} 的組隊",
                    "char_name": char_name,
                    "target": target,
                    "owner_id": user.id,  # 關鍵：記錄是誰開的團
                    "members": [], "messages": []
                }
                supabase.table("party_posts").insert(data).execute()
                st.rerun()

    # 渲染列表
    tabs = st.tabs(categories)
    try:
        posts = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
    except:
        posts = []

    for i, cat_name in enumerate(categories):
        with tabs[i]:
            for p in posts:
                # 只有本人 (owner_id == user.id) 才能看到管理功能
                is_owner = (p.get('owner_id') == user.id)
                m_list = p.get('members', [])

                with st.expander(f"【{p['target']}】 {p['title']} ｜ 👑 {p['char_name']} ｜ 👥 {len(m_list) + 1}/6"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"👑 隊長: {p['char_name']}")
                        if is_owner:
                            st.info("💡 您是隊長，可直接管理隊伍")
                            if st.button("🗑️ 撤除全團", key=f"del_{p['id']}_{cat_name}"):
                                supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                                st.rerun()
                        else:
                            if st.button("➕ 加入隊伍", key=f"join_{p['id']}_{cat_name}"):
                                m_list.append({"name": user.email.split('@')[0], "job": "冒險者"})
                                supabase.table("party_posts").update({"members": m_list}).eq("id", p["id"]).execute()
                                st.rerun()
                    with c2:
                        # 聊天室內容... (略，邏輯同前)
                        st.write("💬 聊天室")


# 判斷登入狀態
if st.session_state.user is None:
    login_page()
else:
    main_app()