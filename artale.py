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


# --- 2. 時間處理工具 ---
def get_expiry_info(created_at_str):
    """計算剩餘時間並回傳顯示字串"""
    try:
        # Supabase 回傳的是 ISO 格式字串
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        expiry_date = created_at + timedelta(days=7)
        remaining = expiry_date - now

        if remaining.total_seconds() <= 0:
            return None  # 已過期

        days = remaining.days
        hours = remaining.seconds // 3600
        if days > 0:
            return f"⏳ 剩餘 {days}天 {hours}小時"
        else:
            return f"⏳ 剩餘 {hours}小時"
    except:
        return "⏳ 期限一週"


# --- 3. 處理函式 ---
def handle_login():
    acc = st.session_state.get("login_acc")
    pwd = st.session_state.get("login_pwd")
    if acc and pwd:
        try:
            res = supabase.auth.sign_in_with_password({"email": to_internal(acc), "password": pwd})
            st.session_state.user = res.user
        except:
            st.error("❌ 登入失敗")


def handle_signup():
    new_acc = st.session_state.get("reg_acc")
    new_pw = st.session_state.get("reg_pw")
    input_key = st.session_state.get("reg_key")
    if input_key == REG_SECRET:
        try:
            supabase.auth.sign_up({"email": to_internal(new_acc), "password": new_pw})
            st.success("✅ 註冊成功")
        except:
            st.error("❌ 註冊失敗")
    else:
        st.error("❌ 金鑰錯誤")


# --- 4. 登入介面 ---
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
    # --- 5. 登入後主程式 ---
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)

    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
    boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
    pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
    grind_list = ["蛋龍"]
    all_targets = pq_list + boss_list + grind_list

    my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data
    char_map = {f"{c['char_name']} (Lv.{c['level']} {c['job']})": c for c in my_chars}
    char_options = list(char_map.keys())

    with st.sidebar:
        st.header(f"👤 {my_acc}")
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out();
            st.session_state.user = None;
            st.rerun()

        with st.expander("🛡️ 我的角色管理"):
            for c in my_chars:
                c1, c2 = st.columns([3, 1])
                c1.caption(f"{c['char_name']} (Lv.{c['level']})")
                if c2.button("🗑️", key=f"side_del_{c['id']}"):
                    supabase.table("user_characters").delete().eq("id", c['id']).execute();
                    st.rerun()
            nc_name = st.text_input("角色名")
            nc_job = st.selectbox("職業", all_jobs)
            nc_lvl = st.number_input("等級", 1, 200, 100)
            if st.button("儲存角色", use_container_width=True):
                supabase.table("user_characters").insert(
                    {"owner_id": str(current_user.id), "char_name": nc_name, "job": nc_job, "level": nc_lvl}).execute();
                st.rerun()

        st.divider()
        st.subheader("📝 我要開團")
        with st.form("party_form"):
            s_char = st.selectbox("發團角色", ["請選擇"] + char_options)
            t_title = st.text_input("隊伍標題")
            t_target = st.selectbox("目標任務", all_targets)
            if st.form_submit_button("發布組隊", use_container_width=True):
                if s_char != "請選擇":
                    c = char_map[s_char]
                    supabase.table("party_posts").insert({
                        "title": t_title if t_title else f"{c['char_name']} 的團",
                        "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                        "target": t_target, "owner_id": str(current_user.id), "members": [], "messages": [],
                        "note": "TYPE_PARTY"
                    }).execute();
                    st.rerun()

        st.subheader("🙋 我要待組")
        with st.form("waiting_form"):
            w_char = st.selectbox("待組角色", ["請選擇"] + char_options)
            w_target = st.selectbox("想參加的任務", all_targets)
            w_note = st.text_input("留言 (例：有洗血、熟圖)")
            if st.form_submit_button("登錄待組", use_container_width=True):
                if w_char != "請選擇":
                    c = char_map[w_char]
                    supabase.table("party_posts").insert({
                        "title": w_note if w_note else "徵求隊伍中",
                        "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                        "target": w_target, "owner_id": str(current_user.id),
                        "note": "TYPE_WAITING"
                    }).execute();
                    st.rerun()

    # --- 6. 主頁面 ---
    main_tab1, main_tab2 = st.tabs(["⚔️ 隊伍列表", "🍁 待組佈告欄"])

    all_data_raw = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data

    # 這裡實作自動過濾：排除掉超過一週的資料
    all_data = []
    for d in all_data_raw:
        expiry_str = get_expiry_info(d['created_at'])
        if expiry_str:  # 如果沒回傳 None，代表還沒過期
            d['expiry_label'] = expiry_str
            all_data.append(d)
        else:
            # 也可以在這裡補一個背景刪除邏輯，但為了效能，通常讓它自然過濾即可
            pass

    with main_tab1:
        cats = ["全部", "BOSS遠征", "組隊任務", "野外團練"]
        sub_tabs = st.tabs(cats)
        party_posts = [p for p in all_data if p.get('note') != "TYPE_WAITING"]

        for idx, cat in enumerate(cats):
            with sub_tabs[idx]:
                if cat == "全部":
                    filtered = party_posts
                elif cat == "BOSS遠征":
                    filtered = [p for p in party_posts if p['target'] in boss_list]
                elif cat == "組隊任務":
                    filtered = [p for p in party_posts if p['target'] in pq_list]
                else:
                    filtered = [p for p in party_posts if p['target'] in grind_list]

                for p in filtered:
                    m_list = p.get('members', [])
                    has_admin = (str(p['owner_id']) == str(current_user.id) or is_admin)

                    col_m, col_d = st.columns([0.94, 0.06])
                    with col_m:
                        # 標題處顯示剩餘時間
                        exp = st.expander(f"【{p['target']}】 {p['title']} ｜ {p['expiry_label']} ｜ 👥 {len(m_list) + 1}/6")
                        with exp:
                            c1, c2 = st.columns(2)
                            with c1:
                                st.write(f"👑 隊長：{p['char_name']} (Lv.{p['level']} {p['job']})")
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

                                if st.button("➕ 加入隊伍", key=f"join_btn_{cat}_{p['id']}", use_container_width=True):
                                    if char_options:
                                        tc = my_chars[0]
                                        m_list.append({"name": tc['char_name'], "job": tc['job'], "level": tc['level'],
                                                       "owner_id": str(current_user.id)})
                                        supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                     p['id']).execute();
                                        st.rerun()
                                    else:
                                        st.warning("請先建立角色")
                            with c2:
                                st.write("💬 聊天室")
                                msgs = p.get('messages', [])
                                if not msgs: st.caption("目前沒有訊息")
                                for m in msgs[-5:]: st.caption(f"**{m['user']}**: {m['text']}")
                                with st.form(key=f"chat_{cat}_{p['id']}", clear_on_submit=True):
                                    ci, cb = st.columns([3, 1.2])
                                    txt = ci.text_input("訊息", key=f"ti_{cat}_{p['id']}", label_visibility="collapsed")
                                    if cb.form_submit_button("送出", use_container_width=True):
                                        if txt:
                                            name = my_chars[0]['char_name'] if my_chars else my_acc
                                            msgs.append({"user": name, "text": txt})
                                            supabase.table("party_posts").update({"messages": msgs}).eq("id", p[
                                                'id']).execute();
                                            st.rerun()
                    with col_d:
                        if has_admin:
                            if st.button("🗑️", key=f"del_p_{cat}_{p['id']}"):
                                supabase.table("party_posts").delete().eq("id", p['id']).execute();
                                st.rerun()

    with main_tab2:
        st.caption("以下為正在找團的玩家：")
        cats_w = ["全部", "BOSS遠征", "組隊任務", "野外團練"]
        sub_tabs_w = st.tabs(cats_w)
        waiting_posts = [p for p in all_data if p.get('note') == "TYPE_WAITING"]

        for idx, cat in enumerate(cats_w):
            with sub_tabs_w[idx]:
                if cat == "全部":
                    f_w = waiting_posts
                elif cat == "BOSS遠征":
                    f_w = [p for p in waiting_posts if p['target'] in boss_list]
                elif cat == "組隊任務":
                    f_w = [p for p in waiting_posts if p['target'] in pq_list]
                else:
                    f_w = [p for p in waiting_posts if p['target'] in grind_list]

                if not f_w: st.info("目前分類下沒有待組玩家。")

                for w in f_w:
                    col_info, col_act = st.columns([0.9, 0.1])
                    with col_info:
                        st.markdown(f"""
                        <div style="border: 1px solid #444; padding: 10px; border-radius: 5px; background-color: #1e1e1e; margin-bottom: 10px; position: relative;">
                            <div style="float: right; color: #888; font-size: 0.8em;">{w['expiry_label']}</div>
                            <span style="color: #ffaa00; font-weight: bold;">【{w['target']}】</span> 
                            <span style="font-size: 1.1em; color: #fff;">{w['char_name']}</span> 
                            <span style="color: #ccc;">(Lv.{w['level']} {w['job']})</span> 
                            <br>
                            <span style="color: #888; font-size: 0.9em;">💬 留言：{w['title']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_act:
                        if str(w['owner_id']) == str(current_user.id) or is_admin:
                            if st.button("撤回", key=f"del_w_{cat}_{w['id']}", use_container_width=True):
                                supabase.table("party_posts").delete().eq("id", w['id']).execute();
                                st.rerun()