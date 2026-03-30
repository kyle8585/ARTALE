import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

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


def handle_signup():
    new_acc = st.session_state.get("reg_acc")
    new_pw = st.session_state.get("reg_pw")
    input_key = st.session_state.get("reg_key")
    if input_key == REG_SECRET:
        try:
            supabase.auth.sign_up({"email": to_internal(new_acc), "password": new_pw})
            st.success("✅ 註冊成功，請切換至登入頁面")
        except:
            st.error("❌ 註冊失敗，帳號可能已存在")
    else:
        st.error("❌ 註冊金鑰錯誤")


# --- 3. 介面邏輯分流 ---

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
            with st.form("signup_form"):
                st.text_input("自訂帳號", key="reg_acc")
                st.text_input("設定密碼", type="password", key="reg_pw")
                st.text_input("註冊金鑰", type="password", key="reg_key")
                st.form_submit_button("註冊帳號", use_container_width=True, on_click=handle_signup)

else:
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]

    my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data

    if not my_chars:
        _, center, _ = st.columns([1.5, 1, 1.5])
        with center:
            st.markdown("### 🛡️ 建立你的第一個角色")
            st.info("歡迎來到 Artale！在開始組隊之前，請先設定您的角色資訊。")
            with st.form("init_char_form"):
                new_name = st.text_input("角色名稱", placeholder="範例：楓之谷大師")
                new_job = st.selectbox("職業類別", all_jobs)
                new_lvl = st.number_input("當前等級", 1, 200, 30)
                if st.form_submit_button("完成設定並進入大廳", use_container_width=True):
                    if new_name:
                        supabase.table("user_characters").insert({
                            "owner_id": str(current_user.id), "char_name": new_name, "job": new_job, "level": new_lvl
                        }).execute();
                        st.rerun()
                    else:
                        st.error("請輸入角色名稱")
            if st.button("登出系統"):
                supabase.auth.sign_out();
                st.session_state.user = None;
                st.rerun()

    else:
        # 定義分類任務列表
        boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "暗黑龍王"]
        pq_list = ["101", "女神", "金勾海賊王", "羅密歐與茱麗葉"]
        grind_list = ["蛋龍"]

        # 建立帶有分隔標籤的選單
        task_options = (
                ["--- Boss遠征 ---"] + boss_list +
                ["--- 組隊任務 ---"] + pq_list +
                ["--- 團練 ---"] + grind_list
        )

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

            # 1. 我的角色管理
            with st.expander("🛡️ 我的角色管理", expanded=False):
                for c in my_chars:
                    c1, c2 = st.columns([3, 1])
                    c1.caption(f"{c['char_name']} (Lv.{c['level']})")
                    if c2.button("🗑️", key=f"side_del_{c['id']}"):
                        supabase.table("user_characters").delete().eq("id", c['id']).execute();
                        st.rerun()
                st.write("---")
                nc_name = st.text_input("新增角色名")
                nc_job = st.selectbox("職業", all_jobs, key="side_job")
                nc_lvl = st.number_input("等級", 1, 200, 100, key="side_lvl")
                if st.button("儲存新角色", use_container_width=True):
                    supabase.table("user_characters").insert(
                        {"owner_id": str(current_user.id), "char_name": nc_name, "job": nc_job,
                         "level": nc_lvl}).execute();
                    st.rerun()

            # 2. 我要開團 (順序：目標 -> 標題 -> 角色)
            with st.expander("📝 我要開團", expanded=False):
                with st.form("party_form", border=False):
                    t_target = st.selectbox("目標任務", task_options)
                    t_title = st.text_input("隊伍標題 (例：連7拉圖、缺標賊)")
                    s_char = st.selectbox("選擇角色", char_options)

                    if st.form_submit_button("發布組隊", use_container_width=True):
                        if "---" in t_target:
                            st.error("請選擇有效的任務標籤")
                        else:
                            c = char_map[s_char]
                            supabase.table("party_posts").insert({
                                "title": t_title if t_title else f"{c['char_name']} 的團",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": t_target, "owner_id": str(current_user.id), "members": [], "messages": [],
                                "note": "TYPE_PARTY"
                            }).execute();
                            st.rerun()

            # 3. 我要待組 (順序：目標 -> 標題 -> 角色)
            with st.expander("🙋 我要待組", expanded=False):
                with st.form("waiting_form", border=False):
                    w_target = st.selectbox("想參加的任務", task_options, key="w_t")
                    w_note = st.text_input("留言 (例：熟圖、有火眼)", key="w_n")
                    w_char = st.selectbox("選擇角色", char_options, key="w_c")

                    if st.form_submit_button("登錄待組", use_container_width=True):
                        if "---" in w_target:
                            st.error("請選擇有效的任務標籤")
                        else:
                            c = char_map[w_char]
                            supabase.table("party_posts").insert({
                                "title": w_note if w_note else "徵求隊伍中",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": w_target, "owner_id": str(current_user.id),
                                "note": "TYPE_WAITING"
                            }).execute();
                            st.rerun()

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
                        has_admin = (str(p['owner_id']) == str(current_user.id) or is_admin)
                        col_m, col_d = st.columns([0.94, 0.06])
                        with col_m:
                            expander = st.expander(f"【{p['target']}】 {p['title']} ｜ 👥 {len(m_list) + 1}/6")
                            with expander:
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
                                    if st.button("➕ 加入隊伍", key=f"join_{cat}_{p['id']}", use_container_width=True):
                                        tc = my_chars[0]
                                        m_list.append({"name": tc['char_name'], "job": tc['job'], "level": tc['level'],
                                                       "owner_id": str(current_user.id)})
                                        supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                     p['id']).execute();
                                        st.rerun()
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
                        with col_d:
                            if has_admin:
                                if st.button("🗑️", key=f"del_{cat}_{p['id']}"):
                                    supabase.table("party_posts").delete().eq("id", p['id']).execute();
                                    st.rerun()

        with main_tab2:
            st.caption("正在找團的玩家：")
            cats_w = ["全部", "Boss遠征", "組隊任務", "團練"]
            sub_tabs_w = st.tabs(cats_w)
            wait_posts = [p for p in all_data if p.get('note') == "TYPE_WAITING"]
            for idx, cat in enumerate(cats_w):
                with sub_tabs_w[idx]:
                    if cat == "全部":
                        f_w = wait_posts
                    elif cat == "Boss遠征":
                        f_w = [p for p in wait_posts if p['target'] in boss_list]
                    elif cat == "組隊任務":
                        f_w = [p for p in wait_posts if p['target'] in pq_list]
                    else:
                        f_w = [p for p in wait_posts if p['target'] in grind_list]
                    for w in f_w:
                        col_info, col_act = st.columns([0.9, 0.1])
                        with col_info:
                            st.markdown(f"""
                            <div style="border: 1px solid #444; padding: 10px; border-radius: 5px; background-color: #1e1e1e; margin-bottom: 10px; position: relative;">
                                <div style="float: right; color: #888; font-size: 0.8em;">{w['expiry_label']}</div>
                                <span style="color: #ffaa00; font-weight: bold;">【{w['target']}】</span> 
                                <span style="font-size: 1.1em; color: #fff;">{w['char_name']}</span> 
                                <span style="color: #ccc;">(Lv.{w['level']} {w['job']})</span> <br>
                                <span style="color: #888; font-size: 0.9em;">💬 留言：{w['title']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        with col_act:
                            if str(w['owner_id']) == str(current_user.id) or is_admin:
                                if st.button("撤回", key=f"del_w_{cat}_{w['id']}", use_container_width=True):
                                    supabase.table("party_posts").delete().eq("id", w['id']).execute();
                                    st.rerun()