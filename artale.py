import streamlit as st
from supabase import create_client, Client

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# 初始化所有需要的 Session State，防止程式因變數不存在而中斷
if 'temp_acc' not in st.session_state: st.session_state.temp_acc = ""
if 'temp_pw' not in st.session_state: st.session_state.temp_pw = ""
if 'user' not in st.session_state: st.session_state.user = None

# Supabase 連線資訊
URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()


# 轉換工具：將純文字轉為內部識別格式
def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 2. 登入/註冊分頁 (當 user 為 None 時顯示) ---
def show_login_page():
    # 建立三個欄位，讓中間的登入框看起來窄一點，比較美觀
    left, center, right = st.columns([1, 1.2, 1])

    with center:
        st.markdown("<h2 style='text-align: center;'>🍁 Artale 組隊中心</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>請先登入或申請帳號以使用功能</p>",
                    unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 登入系統", "📝 註冊帳號"])

        with tab1:
            with st.form("login_form"):
                acc = st.text_input("帳號", value=st.session_state.temp_acc, placeholder="請輸入帳號")
                pwd = st.text_input("密碼", type="password", value=st.session_state.temp_pw, placeholder="請輸入密碼")
                submit = st.form_submit_button("立即登入", use_container_width=True)

                if submit:
                    if not acc or not pwd:
                        st.warning("請填寫帳號與密碼")
                    else:
                        try:
                            res = supabase.auth.sign_in_with_password({
                                "email": to_internal(acc),
                                "password": pwd
                            })
                            st.session_state.user = res.user
                            st.success("登入成功！頁面跳轉中...")
                            st.rerun()
                        except:
                            st.error("❌ 帳號或密碼錯誤，請重新確認")

        with tab2:
            st.info("提示：帳號可使用任何名稱，密碼需至少 6 位。")
            with st.form("signup_form"):
                new_acc = st.text_input("自訂帳號", placeholder="例如：楓之谷小戰士")
                new_pw = st.text_input("設定密碼", type="password", placeholder="至少 6 位數")
                signup_submit = st.form_submit_button("確認提交申請", use_container_width=True)

                if signup_submit:
                    if not new_acc or len(new_pw) < 6:
                        st.error("⚠️ 帳號不得為空，且密碼至少需 6 位數")
                    else:
                        try:
                            supabase.auth.sign_up({
                                "email": to_internal(new_acc),
                                "password": new_pw
                            })
                            st.session_state.temp_acc = new_acc
                            st.session_state.temp_pw = new_pw
                            st.success(f"✅ 帳號「{new_acc}」申請成功！資訊已自動填入，請點擊上方「登入系統」分頁。")
                        except:
                            st.error("❌ 申請失敗：該帳號可能已被使用")


# --- 3. 主程式頁面 (當 user 登入後顯示) ---
def show_main_app():
    user = st.session_state.user
    display_acc = user.email.split('@')[0]

    # 側邊欄
    with st.sidebar:
        st.title("🍁 管理面板")
        st.write(f"👤 當前帳號：**{display_acc}**")
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
        st.divider()
        st.write("這裡是發布組隊的地方...")
        # (這裡可以放發布表單，邏輯同前)

    st.title("🍁 Artale 組隊中心")
    st.write(f"你好 {display_acc}，歡迎進入組隊系統！")

    # 顯示隊伍清單... (邏輯同前)
    try:
        posts = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
        if not posts:
            st.info("目前尚無任何隊伍。")
        else:
            st.write(f"目前共有 {len(posts)} 個隊伍正在招募中。")
            # 這裡放置渲染隊伍的 Expanders 邏輯
    except Exception as e:
        st.error(f"連線資料庫失敗: {e}")


# --- 4. 執行判斷邏輯 ---
if st.session_state.user is None:
    show_login_page()
else:
    show_main_app()