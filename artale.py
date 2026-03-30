import streamlit as st
from supabase import create_client, Client

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()

# 初始化 Session State
if 'user' not in st.session_state: st.session_state.user = None


# 帳號轉換工具 (內部統一使用 @artale.local 格式)
def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 2. 登入/註冊介面 ---
if st.session_state.user is None:
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown("<h1 style='text-align: center;'>🍁 Artale 組隊中心</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 帳號登入", "📝 快速註冊"])

        with t1:
            with st.form("login_form"):
                acc = st.text_input("帳號")
                pwd = st.text_input("密碼", type="password")
                if st.form_submit_button("立即登入", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": to_internal(acc), "password": pwd})
                        st.session_state.user = res.user
                        st.rerun()
                    except:
                        st.error("❌ 登入失敗：請檢查帳號密碼，或確認是否已完成註冊。")

        with t2:
            st.caption("提示：註冊成功後請切換至登入頁面。")
            with st.form("signup_form"):
                new_acc = st.text_input("自訂帳號")
                new_pw = st.text_input("設定密碼 (至少6位)", type="password")
                if st.form_submit_button("註冊帳號", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": to_internal(new_acc), "password": new_pw})
                        st.success(f"✅ 註冊成功！帳號: {new_acc}，現在請切換到登入分頁。")
                    except Exception as e:
                        st.error(f"❌ 註冊失敗: {e}")

# --- 3. 主程式介面 (登入後) ---
else:
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]  # 取得顯示名稱

    st.title("🍁 Art