import streamlit as st
from supabase import create_client, Client

# 1. 初始化 Supabase
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# 初始化暫存資訊
if 'temp_acc' not in st.session_state: st.session_state.temp_acc = ""
if 'temp_pw' not in st.session_state: st.session_state.temp_pw = ""
if 'user' not in st.session_state: st.session_state.user = None


# 轉換工具：將純文字轉為內部識別格式
def to_internal(acc):
    return f"{acc.strip()}@artale.local"


def login_page():
    # 縮小介面並置中
    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        st.markdown("<h2 style='text-align: center;'>🍁 Artale 組隊中心</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["登入", "註冊帳號"])

        with tab1:
            with st.form("login_form"):
                acc = st.text_input("帳號", value=st.session_state.temp_acc, placeholder="請輸入您的帳號")
                pwd = st.text_input("密碼", type="password", value=st.session_state.temp_pw, placeholder="請輸入密碼")
                if st.form_submit_button("登入系統", use_container_width=True):
                    try:
                        # 登入時自動轉換為內部格式
                        res = supabase.auth.sign_in_with_password({
                            "email": to_internal(acc),
                            "password": pwd
                        })
                        st.session_state.user = res.user
                        st.rerun()
                    except:
                        st.error("❌ 登入失敗：帳號或密碼錯誤")

        with tab2:
            st.caption("✨ 提示：帳號可使用任何英文、數字或中文，無須 Email。")
            with st.form("signup_form"):
                new_acc = st.text_input("設定帳號", placeholder="例如：楓之谷小戰士")
                new_pw = st.text_input("設定密碼", type="password", placeholder="建議至少 6 位數")
                if st.form_submit_button("確認申請", use_container_width=True):
                    if not new_acc or not new_pw:
                        st.error("⚠️ 帳號與密碼不能為空")
                    else:
                        try:
                            # 註冊時自動轉換為內部格式
                            supabase.auth.sign_up({
                                "email": to_internal(new_acc),
                                "password": new_pw
                            })
                            # 儲存資訊以便自動填入
                            st.session_state.temp_acc = new_acc
                            st.session_state.temp_pw = new_pw
                            st.success(f"✅ 帳號「{new_acc}」申請成功！資訊已自動帶入，請切換至登入頁。")
                        except Exception as e:
                            st.error(f"❌ 申請失敗：帳號可能已存在或格式不符")


# --- 主程式頁面 ---
def main_app():
    user = st.session_state.user
    # 顯示給使用者看時，去掉內部的 @artale.local 後綴
    display_acc = user.email.split('@')[0]

    st.sidebar.write(f"👤 當前帳號：**{display_acc}**")
    if st.sidebar.button("登出系統"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.title("🍁 Artale 組隊中心")
    st.write(f"歡迎回來，{display_acc}！")

    # 這裡放原本的組隊分類、發布、顯示邏輯 (與 owner_id 比對的部分維持不變)
    # ... (後續程式碼)