import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# CSS 注入：自定義 Expander 的顏色
st.markdown("""
<style>
    /* 滿員的樣式 (深灰) */
    .full-party {
        background-color: #2d2d2d !important;
        border-radius: 5px;
        padding: 2px 10px;
    }
    /* 已加入的樣式 (橘色) */
    .joined-party {
        background-color: #e67e22 !important;
        color: white !important;
        border-radius: 5px;
        padding: 2px 10px;
    }
    .joined-party p, .joined-party span {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"

ADMIN_ACC = "akuy7788"
REG_SECRET = "artale"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()

if 'user' not in st.session_state: st.session_state.user = None


def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 2. 工具函式 ---
def get_expiry_info(created_at_str):
    try:
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        expiry_date = created_at + timedelta(days=7)
        remaining = expiry_date - now
        if remaining.total_seconds() <= 0: return None
        days = remaining.days
        hours = remaining.seconds // 3600
        return f"⏳ 剩餘 {days}天 {hours}小時" if days > 0 else f"⏳ 剩餘 {hours}小時"
    except:
        return "⏳ 期限一週"


def handle_login():
    acc = st.session_state.get("login_acc")
    pwd = st.session_state.get("login_pwd")
    if acc and pwd:
        try:
            res = supabase.auth.sign_in_with_password({"email": to_internal(acc), "password": pwd})
            st.session_state.user = res.user
        except:
            st.error("❌ 帳號或密碼錯誤")


# --- 3. 登入/註冊介面 ---
if st.session_state.user is None:
    _, center, _ = st.columns([2, 1.2, 2])
    with center:
        st.markdown("<h1 style='text-align: center;'>🍁 Artale 組隊中心</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 帳號登入", "📝 快速註冊"])
        with t1:
            with st.form("login_form"):
                st.text_input("帳號", key="login_acc")
                st.text_input("密碼", type="password", key="login_pwd")
                st.form_submit_button("立即登入", use_container_width=True, on_click=handle_login)
        with t2:
            st.info("請向管理員索取註冊金鑰")

else:
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]

    my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data

    if not my_chars:
        # 強制引導建立角色邏輯... (略過與上次相同)
        st.warning("請先建立角色")
        if st.button("點此建立角色"): st.rerun()

    else:
        boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "暗黑龍王"]
        pq_list = ["101", "女神", "金勾海賊王", "羅密歐與茱麗葉"]
        grind_list = ["蛋龍"]
        task_options = ["--- Boss遠征 ---"] + boss_list + ["--- 組隊任務 ---"] + pq_list + ["--- 團練 ---"] + grind_list

        char_map = {f"{c['char_name']} (Lv.{c['level']} {c['job']})": c for c in my_chars}
        char_options = list(char_map.keys())

        # --- 4. 側邊欄 ---
        with st.sidebar:
            st.header(f"👤 {my_acc}")
            if st.button("登出系統", use_container_width=True):
                supabase.auth.sign_out();
                st.session_state.user = None;
                st.rerun()
            st.divider()

            with st.expander("🛡️ 我的角色管理"):
                # 角色管理邏輯... (與上次相同)
                pass

            with st.expander("📝 我要開團"):
                with st.form("party_form", border=False):
                    t_target = st.selectbox("目標任務", task_options)
                    t_title = st.text_input("隊伍標題")
                    s_char = st.selectbox("選擇角色", char_options)
                    if st.form_submit_button("發布組隊", use_container_width=True):
                        if "---" not in t_target:
                            c = char_map[s_char]
                            supabase.table("party_posts").insert({
                                "title": t_title if t_title else f"{c['char_name']} 的團",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": t_target, "owner_id": str(current_user.id), "members": [], "messages": [],
                                "note": "TYPE_PARTY"
                            }).execute();
                            st.rerun()

            with st.expander("🙋 我要待組"):
                # 待組邏輯... (與上次相同)
                pass

        # --- 5. 主頁面 ---
        main_tab1, main_tab2 = st.tabs(["⚔️ 隊伍列表", "🍁 待組佈告欄"])
        all_data_raw = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
        all_data = []
        for d in all_data_raw:
            exp = get_expiry_info(d['created_at'])
            if exp: d['expiry_label'] = exp; all_data.append(d)

        with main_tab1:
            cats = ["全部", "Boss遠征", "組隊任務", "團練"]
            sub_tabs = st.tabs(cats)
            party_posts = [p for p in all_data if p.get('note') != "TYPE_WAITING"]

            for idx, cat in enumerate(cats):
                with sub_tabs[idx]:
                    if cat == "全部":
                        f = party_posts
                    elif cat == "Boss遠征":
                        f = [p for p in party_posts if p['target'] in boss_list]
                    elif cat == "組隊任務":
                        f = [p for p in party_posts if p['target'] in pq_list]
                    else:
                        f = [p for p in party_posts if p['target'] in grind_list]

                    for p in f:
                        m_list = p.get('members', [])
                        cur_count = len(m_list) + 1
                        is_full = cur_count >= 6
                        # 判斷登入者是否在隊伍中 (隊長或隊員)
                        is_joined = (str(p['owner_id']) == str(current_user.id)) or any(
                            str(m.get('owner_id')) == str(current_user.id) for m in m_list)
                        has_admin = (str(p['owner_id']) == str(current_user.id) or is_admin)

                        # 動態標題標籤
                        status_tag = " (滿員)" if is_full else ""
                        title_prefix = "【" + p['target'] + "】 " + p['title'] + status_tag + f" ｜ 👥 {cur_count}/6"

                        # 根據狀態決定外殼容器
                        col_m, col_d = st.columns([0.94, 0.06])
                        with col_m:
                            # 注入 HTML 標記來控制樣式
                            div_class = "joined-party" if is_joined else ("full-party" if is_full else "")
                            st.markdown(f'<div class="{div_class}">', unsafe_allow_html=True)

                            with st.expander(title_prefix):
                                st.markdown('</div>', unsafe_allow_html=True)  # 結束背景色影響範圍，不影響內部
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(
                                        f"👑 **隊長**：{p['char_name']} (Lv.{p['level']} {p['job']}) <span style='color: #888; margin-left: 10px; font-size: 0.85em;'>{p['expiry_label']}</span>",
                                        unsafe_allow_html=True)
                                    st.divider()
                                    st.write("👥 隊員名單：")
                                    for m_idx, m in enumerate(m_list):
                                        mc1, mc2 = st.columns([4, 1.5])
                                        mc1.write(f" └ {m['name']} (Lv.{m['level']} {m['job']})")
                                        if has_admin or str(m.get('owner_id')) == str(current_user.id):
                                            if mc2.button("退出", key=f"kick_{cat}_{p['id']}_{m_idx}"):
                                                m_list.pop(m_idx);
                                                supabase.table("party_posts").update({"members": m_list}).eq("id", p[
                                                    'id']).execute();
                                                st.rerun()

                                    # 加入按鈕：滿員時禁用
                                    if st.button("➕ 加入隊伍", key=f"join_{cat}_{p['id']}", use_container_width=True,
                                                 disabled=is_full):
                                        if not any(
                                                str(m.get('owner_id')) == str(current_user.id) for m in m_list) and str(
                                                p['owner_id']) != str(current_user.id):
                                            tc = my_chars[0]
                                            m_list.append(
                                                {"name": tc['char_name'], "job": tc['job'], "level": tc['level'],
                                                 "owner_id": str(current_user.id)})
                                            supabase.table("party_posts").update({"members": m_list}).eq("id", p[
                                                'id']).execute();
                                            st.rerun()
                                        else:
                                            st.warning("你已在隊伍中")
                                with c2:
                                    st.write("💬 聊天室")
                                    msgs = p.get('messages', [])
                                    for msg in msgs[-5:]: st.caption(f"**{msg['user']}**: {msg['text']}")
                                    with st.form(key=f"chat_{cat}_{p['id']}", clear_on_submit=True):
                                        ci, cb = st.columns([3, 1.2])
                                        txt = ci.text_input("訊息", key=f"ti_{cat}_{p['id']}",
                                                            label_visibility="collapsed")
                                        if cb.form_submit_button("送出", use_container_width=True):
                                            if txt:
                                                msgs.append({"user": my_chars[0]['char_name'], "text": txt})
                                                supabase.table("party_posts").update({"messages": msgs}).eq("id", p[
                                                    'id']).execute();
                                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                        with col_d:
                            if has_admin:
                                if st.button("🗑️", key=f"del_{cat}_{p['id']}"):
                                    supabase.table("party_posts").delete().eq("id", p['id']).execute();
                                    st.rerun()

        with main_tab2:
            # 待組佈告欄邏輯... (維持原樣)
            pass