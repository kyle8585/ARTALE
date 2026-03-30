import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# 更新 CSS：讓橘色效果只出現在 Expander 框線上，避免產生橫跨全螢幕的條狀感
st.markdown("""
<style>
    /* 縮減元件間距 */
    [data-testid="stVerticalBlock"] > div {
        padding-top: 0.1rem;
        padding-bottom: 0.1rem;
    }

    /* 已加入隊伍：Expander 標題與框線變橘色 */
    .joined-party [data-testid="stExpander"] {
        border: 2px solid #e67e22 !important;
        background-color: rgba(230, 126, 34, 0.05) !important;
        border-radius: 10px !important;
    }
    .joined-party [data-testid="stExpanderSummary"] {
        color: #e67e22 !important;
        font-weight: bold !important;
    }

    /* 滿員隊伍：深灰色背景 */
    .full-party [data-testid="stExpander"] {
        border: 1px solid #444 !important;
        background-color: rgba(60, 60, 60, 0.3) !important;
        border-radius: 10px !important;
    }

    /* 一般隊伍樣式 */
    .normal-party [data-testid="stExpander"] {
        border: 1px solid #333 !important;
        border-radius: 10px !important;
    }

    /* 移除垃圾桶按鈕的邊框，讓視覺更乾淨 */
    .stButton > button {
        border-radius: 5px;
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
        st.markdown("<h1 style='text-align: center;'>🍁 Artale 組隊中心</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            acc = st.text_input("帳號")
            pwd = st.text_input("密碼", type="password")
            if st.form_submit_button("立即登入", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": to_internal(acc), "password": pwd})
                    st.session_state.user = res.user
                    st.rerun()
                except:
                    st.error("❌ 帳號或密碼錯誤")
else:
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]

    # 讀取使用者角色
    my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data

    # 基本選單定義
    boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "暗黑龍王"]
    pq_list = ["101", "女神", "金勾海賊王", "羅密歐與茱麗葉"]
    grind_list = ["蛋龍"]
    task_options = ["--- Boss ---"] + boss_list + ["--- PQ ---"] + pq_list + ["--- 團練 ---"] + grind_list

    # --- 3. 側邊欄 (包含角色管理與功能) ---
    with st.sidebar:
        st.title(f"👤 {my_acc}")
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out();
            st.session_state.user = None;
            st.rerun()

        st.divider()

        # 🛡️ 角色管理摺疊欄
        with st.expander("🛡️ 角色管理"):
            if my_chars:
                for c in my_chars:
                    c1, c2 = st.columns([3, 1])
                    c1.caption(f"{c['char_name']} (Lv.{c['level']} {c['job']})")
                    if c2.button("🗑️", key=f"side_del_{c['id']}"):
                        supabase.table("user_characters").delete().eq("id", c['id']).execute();
                        st.rerun()
            else:
                st.info("尚無角色，請從下方新增")

            st.write("---")
            st.write("➕ 新增角色")
            new_n = st.text_input("角色名稱", key="add_n")
            new_j = st.selectbox("職業", all_jobs, key="add_j")
            new_l = st.number_input("等級", 1, 200, 100, key="add_l")
            if st.button("儲存新角色", use_container_width=True):
                if new_n:
                    supabase.table("user_characters").insert({
                        "owner_id": str(current_user.id), "char_name": new_n, "job": new_j, "level": new_l
                    }).execute();
                    st.rerun()
                else:
                    st.error("請輸入名稱")

        # 📝 發布功能 (只有在有角色時顯示)
        if my_chars:
            char_map = {f"{c['char_name']} (Lv.{c['level']} {c['job']})": c for c in my_chars}
            char_options = list(char_map.keys())

            with st.expander("📝 我要開團"):
                with st.form("p_form", border=False):
                    target = st.selectbox("目標任務", task_options)
                    title = st.text_input("隊伍標題")
                    sel_char = st.selectbox("使用角色", char_options)
                    if st.form_submit_button("發布組隊", use_container_width=True):
                        if "---" not in target:
                            c = char_map[sel_char]
                            supabase.table("party_posts").insert({
                                "title": title if title else f"{c['char_name']}的團",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": target, "owner_id": str(current_user.id),
                                "members": [], "messages": [], "note": "TYPE_PARTY"
                            }).execute();
                            st.rerun()

            with st.expander("🙋 我要待組"):
                with st.form("w_form", border=False):
                    w_target = st.selectbox("目標任務", task_options, key="wt")
                    w_note = st.text_input("留言/備註", key="wn")
                    w_char = st.selectbox("使用角色", char_options, key="wc")
                    if st.form_submit_button("登錄待組", use_container_width=True):
                        if "---" not in w_target:
                            c = char_map[w_char]
                            supabase.table("party_posts").insert({
                                "title": w_note if w_note else "徵求隊伍中",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": w_target, "owner_id": str(current_user.id), "note": "TYPE_WAITING"
                            }).execute();
                            st.rerun()

    # --- 4. 主頁面內容 ---
    if not my_chars:
        st.info("👋 歡迎！請先在左側「角色管理」建立您的角色，即可開始參與組隊。")
    else:
        tab1, tab2 = st.tabs(["⚔️ 隊伍列表", "🍁 待組佈告欄"])

        # 取得所有貼文
        raw_posts = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
        active_posts = [p for p in raw_posts if get_expiry_info(p['created_at'])]

        with tab1:
            cats = ["全部", "Boss遠征", "組隊任務", "團練"]
            sub_tabs = st.tabs(cats)
            party_only = [p for p in active_posts if p.get('note') != "TYPE_WAITING"]

            for i, cat_name in enumerate(cats):
                with sub_tabs[i]:
                    if cat_name == "全部":
                        filtered = party_only
                    elif cat_name == "Boss遠征":
                        filtered = [p for p in party_only if p['target'] in boss_list]
                    elif cat_name == "組隊任務":
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
                        unique_id = f"{cat_name}_{p['id']}"  # 防止 Duplicate Key

                        st.markdown(f'<div class="{div_class}">', unsafe_allow_html=True)
                        col_main, col_del = st.columns([0.94, 0.06])
                        with col_main:
                            with st.expander(
                                    f"【{p['target']}】 {p['title']}{' (滿員)' if is_full else ''} ｜ 👥 {cur_count}/6"):
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"👑 **隊長**：{p['char_name']} (Lv.{p['level']} {p['job']})")
                                    st.caption(get_expiry_info(p['created_at']))
                                    st.divider()
                                    for idx, m in enumerate(m_list):
                                        mc1, mc2 = st.columns([4, 1])
                                        mc1.caption(f"└ {m['name']} (Lv.{m['level']} {m['job']})")
                                        if (str(p['owner_id']) == str(current_user.id) or is_admin or str(
                                                m.get('owner_id')) == str(current_user.id)):
                                            if mc2.button("退出", key=f"kick_{unique_id}_{idx}"):
                                                m_list.pop(idx);
                                                supabase.table("party_posts").update({"members": m_list}).eq("id", p[
                                                    'id']).execute();
                                                st.rerun()

                                    if st.button("➕ 加入隊伍", key=f"join_{unique_id}", use_container_width=True,
                                                 disabled=(is_full or is_joined)):
                                        tc = my_chars[0]  # 預設使用第一個角色加入
                                        m_list.append({"name": tc['char_name'], "job": tc['job'], "level": tc['level'],
                                                       "owner_id": str(current_user.id)})
                                        supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                     p['id']).execute();
                                        st.rerun()
                                with c2:
                                    st.write("💬 聊天室")
                                    msgs = p.get('messages', [])
                                    for msg in msgs[-5:]: st.caption(f"**{msg['user']}**: {msg['text']}")
                                    with st.form(key=f"chat_{unique_id}", clear_on_submit=True):
                                        it, bt = st.columns([3, 1])
                                        txt = it.text_input("說話", label_visibility="collapsed", key=f"in_{unique_id}")
                                        if bt.form_submit_button("送出"):
                                            if txt:
                                                msgs.append({"user": my_chars[0]['char_name'], "text": txt})
                                                supabase.table("party_posts").update({"messages": msgs}).eq("id", p[
                                                    'id']).execute();
                                                st.rerun()
                        with col_del:
                            if str(p['owner_id']) == str(current_user.id) or is_admin:
                                if st.button("🗑️", key=f"del_{unique_id}"):
                                    supabase.table("party_posts").delete().eq("id", p['id']).execute();
                                    st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.caption("找尋隊伍中的玩家")
            wait_only = [p for p in active_posts if p.get('note') == "TYPE_WAITING"]
            for w in wait_only:
                ci, ca = st.columns([0.9, 0.1])
                with ci:
                    st.markdown(f'''
                    <div style="border:1px solid #444; padding:12px; border-radius:10px; background:#1e1e1e; margin-bottom:8px;">
                        <span style="color:#ffaa00; font-weight:bold;">【{w["target"]}】</span> {w["char_name"]} (Lv.{w["level"]} {w["job"]})<br>
                        <small style="color:#bbb;">{w["title"]}</small>
                    </div>
                    ''', unsafe_allow_html=True)
                with ca:
                    if str(w['owner_id']) == str(current_user.id) or is_admin:
                        if st.button("🗑️", key=f"dw_{w['id']}"):
                            supabase.table("party_posts").delete().eq("id", w['id']).execute();
                            st.rerun()