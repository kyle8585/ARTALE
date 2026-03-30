import streamlit as st
from supabase import create_client, Client

# 1. 初始化 Supabase
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# 初始化 Session State
if 'temp_account' not in st.session_state: st.session_state.temp_account = ""
if 'temp_pw' not in st.session_state: st.session_state.temp_pw = ""
if 'user' not in st.session_state: st.session_state.user = None


# 格式轉換小工具：將自定義帳號轉為虛擬 Email
def to_internal_email(account):
    if "@" in account: return account
    return f"{account}@artale.internal"


def login_page():
    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        st.markdown("<h2 style='text-align: center;'>🔐 Artale 組隊中心</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["登入帳號", "申請帳號"])

        with tab1:
            with st.form("login_form"):
                acc = st.text_input("帳號", value=st.session_state.temp_account)
                pwd = st.text_input("密碼", type="password", value=st.session_state.temp_pw)
                if st.form_submit_button("立即登入", use_container_width=True):
                    try:
                        # 登入時自動轉換格式
                        res = supabase.auth.sign_in_with_password({
                            "email": to_internal_email(acc),
                            "password": pwd
                        })
                        st.session_state.user = res.user
                        st.rerun()
                    except:
                        st.error("登入失敗，請檢查帳號密碼")

        with tab2:
            st.caption("✨ 提示：帳號可以使用任何文字或數字")
            with st.form("signup_form"):
                new_acc = st.text_input("設定帳號")
                new_pw = st.text_input("設定密碼", type="password", help="至少 6 位數")
                if st.form_submit_button("提交申請", use_container_width=True):
                    if len(new_pw) < 6:
                        st.warning("密碼長度建議至少 6 位數")
                    elif new_acc:
                        try:
                            # 註冊時自動轉換格式
                            supabase.auth.sign_up({
                                "email": to_internal_email(new_acc),
                                "password": new_pw
                            })
                            st.session_state.temp_account = new_acc
                            st.session_state.temp_pw = new_pw
                            st.success(f"帳號「{new_acc}」申請成功！資訊已自動填入，請切換至登入分頁。")
                        except:
                            st.error("申請失敗：帳號可能已被使用或格式不符")
                    else:
                        st.error("請輸入帳號名稱")


# --- 主程式頁面 ---
def main_app():
    user = st.session_state.user
    # 顯示給使用者看時，把後綴拿掉，保持美觀
    display_name = user.email.split('@')[0]

    st.sidebar.write(f"👤 當前帳號: **{display_name}**")
    if st.sidebar.button("登出系統"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.title("🍁 Artale 線上組隊中心")
    st.info(f"你好，{display_name}！你現在可以自由發布與管理隊伍。")
    # (後續組隊邏輯代碼...)


if st.session_state.user is None:
    login_page()
else:
    main_app()