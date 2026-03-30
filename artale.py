import streamlit as st
from supabase import create_client, Client

# --- 1. 初始化 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()

if 'user' not in st.session_state: st.session_state.user = None


# 轉換工具
def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 2. 登入/註冊頁面 ---
if st.session_state.user is None:
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.header("🍁 Artale 組隊中心")
        t1, t2 = st.tabs(["登入", "註冊"])

        with t1:
            with st.form("login"):
                acc = st.text_input("帳號")
                pwd = st.text_input("密碼", type="password")
                if st.form_submit_button("登入", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": to_internal(acc), "password": pwd})
                        st.session_state.user = res.user
                        st.rerun()
                    except Exception as e:
                        st.error(f"登入失敗：{e}")

        with t2:
            with st.form("signup"):
                new_acc = st.text_input("新帳號")
                new_pw = st.text_input("新密碼", type="password")
                if st.form_submit_button("申請帳號", use_container_width=True):
                    try:
                        # 核心診斷點：抓取原始錯誤
                        response = supabase.auth.sign_up({
                            "email": to_internal(new_acc),
                            "password": new_pw
                        })
                        st.success("註冊成功！請切換到登入頁面。")
                    except Exception as e:
                        # 這裡會顯示真正的錯誤，例如 "Signups not allowed" 或 "Invalid email"
                        st.error(f"🔍 系統回報具體原因：{e}")

else:
    # 登入後的簡單介面測試
    st.write(f"✅ 已登入：{st.session_state.user.email}")
    if st.sidebar.button("登出"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()