import streamlit as st
from supabase import create_client, Client

# 1. 初始化 Supabase
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# 初始化 Session State 用於自動填入
if 'temp_email' not in st.session_state: st.session_state.temp_email = ""
if 'temp_pw' not in st.session_state: st.session_state.temp_pw = ""
if 'user' not in st.session_state: st.session_state.user = None


def login_page():
    # 使用 columns 讓介面縮小置中
    _, center_col, _ = st.columns([1, 1.5, 1])

    with center_col:
        st.markdown("<h2 style='text-align: center;'>🔐 Artale 組隊中心</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["登入帳號", "申請帳號"])

        with tab1:
            with st.form("login_form"):
                # 自動填入註冊成功的資訊
                email = st.text_input("帳號 (Email 格式)", value=st.session_state.temp_email)
                password = st.text_input("密碼", type="password", value=st.session_state.temp_pw)
                if st.form_submit_button("立即登入", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.rerun()
                    except Exception as e:
                        st.error("登入失敗，請檢查帳號密碼")

        with tab2:
            st.caption("提示：帳號請包含 @ 字元，例如：abc@artale.com")
            with st.form("signup_form"):
                new_email = st.text_input("設定帳號")
                new_pw = st.text_input("設定密碼", type="password")
                if st.form_submit_button("提交申請", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": new_email, "password": new_pw})
                        # 儲存到 session_state 供登入頁自動填入
                        st.session_state.temp_email = new_email
                        st.session_state.temp_pw = new_pw
                        st.success("申請成功！資訊已為您自動填入，請切換至「登入帳號」分頁。")
                    except Exception as e:
                        st.error("申請失敗，帳號格式錯誤或已存在")


# --- 主程式頁面 ---
def main_app():
    user = st.session_state.user
    st.sidebar.write(f"👤 帳號: {user.email}")
    if st.sidebar.button("登出系統"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.title("🍁 Artale 線上組隊中心")

    # (以下維持你原本的組隊邏輯...)
    all_targets = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神", "拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王",
                   "蛋龍"]
    categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]
    tabs = st.tabs(categories)

    # 讀取資料並顯示... (略)
    st.info("已成功登入，現在可以開始開團或加入隊伍了！")


# 判斷登入狀態
if st.session_state.user is None:
    login_page()
else:
    main_app()