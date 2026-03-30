import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# 更新 CSS：針對摺疊面板本身進行變色，而不是在外層放條狀暗示
st.markdown("""
<style>
    /* 基礎容器間距縮減 */
    [data-testid="stVerticalBlock"] > div {
        padding-top: 0.1rem;
        padding-bottom: 0.1rem;
    }

    /* 已加入隊伍的樣式：摺疊面板變橘色 */
    .joined-party [data-testid="stExpander"] {
        border: 2px solid #e67e22 !important;
        background-color: rgba(230, 126, 34, 0.1) !important;
        border-radius: 10px !important;
    }
    .joined-party [data-testid="stExpanderSummary"] {
        color: #e67e22 !important;
    }

    /* 滿員隊伍的樣式：深灰色背景 */
    .full-party [data-testid="stExpander"] {
        border: 1px solid #444 !important;
        background-color: rgba(60, 60, 60, 0.4) !important;
        border-radius: 10px !important;
    }

    /* 一般隊伍樣式 */
    .normal-party [data-testid="stExpander"] {
        border: 1px solid #333 !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"

ADMIN_ACC = "akuy7788"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()

if 'user' not in st.session_state: st.session_state.user = None


def to_internal(acc): return f"{acc.strip()}@artale.local"


def get_expiry_info(created_at_str):
    try:
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        expiry_date = created_at + timedelta(days=7)
        remaining = expiry_date - now
        if remaining.total_seconds() <= 0: return None
        days, hours = remaining.days, remaining.seconds // 3600
        return f"⏳ {days}天{hours}時" if days > 0 else f"⏳ {hours}時"
    except:
        return "⏳ 7天"


# --- 2. 登入介面 ---
if st.session_state.user is None:
    _, center, _ = st.columns([2, 1.2, 2])
    with center:
        st.markdown("<h1 style='text-align: center;'>🍁 Artale 組隊</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            acc = st.text_input("帳號")
            pwd = st.text_input("密碼", type="password")
            if st.form_submit_button("立即登入", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": to_internal(acc), "password": pwd})
                    st.session_state.user = res.user
                    st.rerun()
                except:
                    st.error("❌ 錯誤")
else:
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]

    my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data

    if not my_chars:
        st.warning("請先建立角色");
        st.button("刷新", on_click=st.rerun)
    else:
        boss_list, pq_list, grind_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "暗黑龍王"], ["101", "女神",
                                                                                                  "金勾海賊王",
                                                                                                  "羅密歐與茱麗葉"], [
            "蛋龍"]
        task_options = ["--- Boss ---"] + boss_list + ["--- PQ ---"] + pq_list + ["--- 團練 ---"] + grind_list
        char_map = {f"{c['char_name']} (Lv.{c['level']} {c['job']})": c for c in my_chars}

        # --- 3. 側邊欄 ---
        with st.sidebar:
            st.title(f"👤 {my_acc}")
            if st.button("登出", use_container_width=True):
                supabase.auth.sign_out();
                st.session_state.user = None;
                st.rerun()

            with st.expander("🛡️ 角色管理"):
                for c in my_chars:
                    c1, c2 = st.columns([3, 1])
                    c1.caption(f"{c['char_name']} (Lv.{c['level']})")
                    if c2.button("🗑️", key=f"del_{c['id']}"):
                        supabase.table("user_characters").delete().eq("id", c['id']).execute();
                        st.rerun()

            with st.expander("📝 我要開團"):
                with st.form("p_form", border=False):
                    target = st.selectbox("目標", task_options)
                    title = st.text_input("標題")
                    char = st.selectbox("角色", list(char_map.keys()))
                    if st.form_submit_button("發布", use_container_width=True):
                        if "---" not in target:
                            c = char_map[char]
                            supabase.table("party_posts").insert(
                                {"title": title if title else f"{c['char_name']}團", "char_name": c['char_name'],
                                 "job": c['job'], "level": c['level'], "target": target,
                                 "owner_id": str(current_user.id), "members": [], "messages": [],
                                 "note": "TYPE_PARTY"}).execute();
                            st.rerun()

            with st.expander("🙋 我要待組"):
                with st.form("w_form", border=False):
                    target = st.selectbox("目標", task_options, key="wt")
                    note = st.text_input("留言", key="wn")
                    char = st.selectbox("角色", list(char_map.keys()), key="wc")
                    if st.form_submit_button("登錄", use_container_width=True):
                        if "---" not in target:
                            c = char_map[char]
                            supabase.table("party_posts").insert(
                                {"title": note if note else "待組中", "char_name": c['char_name'], "job": c['job'],
                                 "level": c['level'], "target": target, "owner_id": str(current_user.id),
                                 "note": "TYPE_WAITING"}).execute();
                            st.rerun()

        # --- 4. 主頁面 ---
        tab1, tab2 = st.tabs(["⚔️ 隊伍列表", "🍁 待組佈告欄"])
        raw = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
        active = [p for p in raw if get_expiry_info(p['created_at'])]

        with tab1:
            cats = ["全部", "Boss遠征", "組隊任務", "團練"]
            st_tabs = st.tabs(cats)
            party_only = [p for p in active if p.get('note') != "TYPE_WAITING"]

            for i, cat in enumerate(cats):
                with st_tabs[i]:
                    if cat == "全部":
                        filtered = party_only
                    elif cat == "Boss遠征":
                        filtered = [p for p in party_only if p['target'] in boss_list]
                    elif cat == "組隊任務":
                        filtered = [p for p in party_only if p['target'] in pq_list]
                    else:
                        filtered = [p for p in party_only if p['target'] in grind_list]

                    for p in filtered:
                        m_list = p.get('members', [])
                        cur_count = len(m_list) + 1
                        is_full = cur_count >= 6
                        is_joined = (str(p['owner_id']) == str(current_user.id)) or any(
                            str(m.get('owner_id')) == str(current_user.id) for m in m_list)

                        div_class = "joined-party" if is_joined else ("full-party" if is_full else "normal-party")

                        # 使用 HTML Wrapper 緊貼 Expander
                        st.markdown(f'<div class="{div_class}">', unsafe_allow_html=True)
                        col_main, col_del = st.columns([0.94, 0.06])
                        with col_main:
                            with st.expander(
                                    f"【{p['target']}】 {p['title']}{' (滿員)' if is_full else ''} ｜ 👥 {cur_count}/6"):
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"👑 **隊長**：{p['char_name']} (Lv.{p['level']})")
                                    st.divider()
                                    for idx, m in enumerate(m_list):
                                        mc1, mc2 = st.columns([4, 1])
                                        mc1.caption(f"└ {m['name']} (Lv.{m['level']} {m['job']})")
                                        if (str(p['owner_id']) == str(current_user.id) or is_admin or str(
                                            m.get('owner_id')) == str