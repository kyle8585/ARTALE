import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# 1. 初始化 Supabase
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# 初始化 Session State
if 'temp_acc' not in st.session_state: st.session_state.temp_acc = ""
if 'temp_pw' not in st.session_state: st.session_state.temp_pw = ""
if 'user' not in st.session_state: st.session_state.user = None


# 轉換工具：將純文字轉為內部識別格式
def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 登入介面 ---
def login_page():
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<h2 style='text-align: center;'>🍁 Artale 組隊中心</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["登入系統", "註冊帳號"])

        with tab1:
            with st.form("login_form"):
                acc = st.text_input("帳號", value=st.session_state.temp_acc)
                pwd = st.text_input("密碼", type="password", value=st.session_state.temp_pw