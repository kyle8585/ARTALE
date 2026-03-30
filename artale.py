import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# CSS 樣式：美化 UI 並縮減欄位間距
st.markdown("""
<style>
    /* 縮減所有元件之間的預設間距 */
    [data-testid="stVerticalBlock"] > div {
        padding-top: 0.05rem !important;
        padding-bottom: 0.05rem !important;
    }

    /* 縮減摺疊面板 (Expander) 的外邊距 */
    div[data-testid="stExpander"] {
        margin-bottom: -10px !important;
    }

    /* 已加入隊伍的特別樣式 */
    .joined-party [data-testid="stExpander"] {
        border: 2px solid #e67e22 !important;
        background-color: rgba(230, 126, 34, 0.05) !important;
        border-radius: 10px !important;
    }
    .joined-party [data-testid="stExpanderSummary"] { 
        color: #e67e22 !important; 
        font-weight: bold !important; 
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


def to_internal(acc): return f"{acc.strip()}@artale.local"


def get_expiry_info(created_at_str):
    try:
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        expiry_date = created_at + timedelta(days=7)
        remaining = expiry_date - now
        if remaining.total_seconds() <= 0: return None
        days, hours = remaining.days, remaining.seconds // 3600
        return f"⏳ {days}天 {hours}時" if days > 0 else f"⏳ {hours}時"
    except:
        return "⏳ 7天"


# --- 2. 登入/註冊介面 ---
if st.session_state.user is None:
    _, center, _ = st.columns([2, 1.5, 2])
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
                        st.error("❌ 帳號或密碼錯誤")
        with t2:
            with st.form("signup_form"):
                new_acc = st.text_input("帳號")
                new_pw = st.text_input("密碼", type="password")
                input_key = st.text_input("邀請碼")
                if st.form_submit_button("註冊", use_container_width=True):
                    if input_key == REG_SECRET:
                        supabase.auth.sign_up({"email": to_internal(new_acc), "password": new_pw})
                        st.success("✅ 註冊成功，請登入")
                    else:
                        st.error("邀請碼錯誤")

else:
    # --- 3. 登入後邏輯 ---
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]

    my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data

    boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "暗黑龍王"]
    pq_list = ["101", "女神", "金勾海賊王", "羅密歐與茱麗葉"]
    grind_list = ["蛋龍"]
    task_options = ["--- Boss ---"] + boss_list + ["--- PQ ---"] + pq_list + ["--- 團練 ---"] + grind_list

    # --- 4. 側邊欄 ---
    with st.sidebar:
        st.header(f"👤 {my_acc}")
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out();
            st.session_state.user = None;
            st.rerun()
        st.divider()

        with st.expander("🛡️ 角色管理"):
            for c in my_chars:
                c1, c2 = st.columns([3, 1])
                c1.caption(f"{c['char_name']} (Lv.{c['level']} {c['job']})")
                if c2.button("🗑️", key=f"del_c_{c['id']}"):
                    supabase.table("user_characters").delete().eq("id", c['id']).execute();
                    st.rerun()
            st.divider()
            nc_name = st.text_input("新增角色名")
            nc_job = st.selectbox("職業", all_jobs)
            nc_lvl = st.number_input("等級", 1, 200, 100)
            if st.button("儲存新角色", use_container_width=True):
                if nc_name:
                    supabase.table("user_characters").insert(
                        {"owner_id": str(current_user.id), "char_name": nc_name, "job": nc_job,
                         "level": nc_lvl}).execute();
                    st.rerun()

        if my_chars:
            char_map = {f"{c['char_name']} (Lv.{c['level']} {c['job']})": c for c in my_chars}
            char_options = list(char_map.keys())

            with st.expander("📝 我要開團"):
                with st.form("p_form", border=False):
                    t_target = st.selectbox("目標任務", task_options)
                    t_title = st.text_input("隊伍標題")
                    s_char = st.selectbox("選擇發起角色", char_options)
                    if st.form_submit_button("發布組隊", use_container_width=True):
                        if "---" not in t_target:
                            c = char_map[s_char]
                            supabase.table("party_posts").insert({
                                "title": t_title if t_title else f"{c['char_name']}的團",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": t_target, "owner_id": str(current_user.id), "members": [], "messages": [],
                                "note": "TYPE_PARTY"
                            }).execute();
                            st.rerun()

            with st.expander("🙋 我要待組"):
                with st.form("w_form", border=False):
                    w_target = st.selectbox("想參加的任務", task_options, key="w_target_sb")
                    w_note = st.text_input("留言/備註", placeholder="例如：熟練、有火眼", key="w_note_ti")
                    w_char_sel = st.selectbox("使用角色", char_options, key="w_char_sb")
                    if st.form_submit_button("登錄待組", use_container_width=True):
                        if "---" not in w_target:
                            c = char_map[w_char_sel]
                            supabase.table("party_posts").insert({
                                "title": w_note if w_note else "徵求隊伍中",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": w_target, "owner_id": str(current_user.id), "note": "TYPE_WAITING"
                            }).execute();
                            st.rerun()

    # --- 5. 主頁面 ---
    if not my_chars:
        st.warning("👋 歡迎！請先在左側建立角色後即可開始使用組隊功能。")
    else:
        main_tab1, main_tab2 = st.tabs(["⚔️ 隊伍列表", "🍁 待組佈告欄"])
        raw_data = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
        all_data = [d for d in raw_data if get_expiry_info(d['created_at'])]

        with main_tab1:
            cats = ["全部", "Boss遠征", "組隊任務", "團練"]
            sub_tabs = st.tabs(cats)
            party_only = [p for p in all_data if p.get('note') != "TYPE_WAITING"]

            for idx, cat_name in enumerate(cats):
                with sub_tabs[idx]:
                    if cat_name == "全部":
                        f = party_only
                    elif cat_name == "Boss遠征":
                        f = [p for p in party_only if p['target'] in boss_list]
                    elif cat_name == "組隊任務":
                        f = [p for p in party_only if p['target'] in pq_list]
                    else:
                        f = [p for p in party_only if p['target'] in grind_list]

                    for p in f:
                        m_list = p.get('members', [])
                        is_joined = any(str(m.get('owner_id')) == str(current_user.id) for m in m_list) or str(
                            p['owner_id']) == str(current_user.id)
                        div_class = "joined-party" if is_joined else ""

                        st.markdown(f'<div class="{div_class}">', unsafe_allow_html=True)
                        col_m, col_d = st.columns([0.94, 0.06])
                        with col_m:
                            # 這裡是核心組隊列表方塊
                            with st.expander(f"【{p['target']}】 {p['title']} ｜ 👥 {len(m_list) + 1}/6"):
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"👑 **隊長**：{p['char_name']} (Lv.{p['level']} {p['job']})")
                                    st.divider()
                                    for m_idx, m in enumerate(m_list):
                                        mc1, mc2 = st.columns([4, 1.5])
                                        suffix = f" <small style='color:gray'>(路人-由{m.get('added_by', '未知')}新增)</small>" if m.get(
                                            'is_guest') else ""
                                        mc1.markdown(f"└ {m['name']} (Lv.{m['level']} {m['job']}){suffix}",
                                                     unsafe_allow_html=True)
                                        if str(p['owner_id']) == str(current_user.id) or is_admin or str(
                                                m.get('owner_id')) == str(current_user.id):
                                            if mc2.button("退出", key=f"k_{cat_name}_{p['id']}_{m_idx}"):
                                                m_list.pop(m_idx);
                                                supabase.table("party_posts").update({"members": m_list}).eq("id", p[
                                                    'id']).execute();
                                                st.rerun()

                                    if len(m_list) < 5:
                                        with st.popover("➕ 加入/新增隊員", use_container_width=True):
                                            sub_t1, sub_t2 = st.tabs(["選擇角色", "手動路人"])
                                            with sub_t1:
                                                sel_to_join = st.selectbox("選擇要加入的角色", char_options,
                                                                           key=f"sel_j_{cat_name}_{p['id']}")
                                                if st.button("確認加入", key=f"btn_j_{cat_name}_{p['id']}"):
                                                    cj = char_map[sel_to_join]
                                                    m_list.append({"name": cj['char_name'], "job": cj['job'],
                                                                   "level": cj['level'],
                                                                   "owner_id": str(current_user.id)})
                                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                                 p[
                                                                                                                     'id']).execute();
                                                    st.rerun()
                                            with sub_t2:
                                                g_name = st.text_input("路人名稱", key=f"gn_{cat_name}_{p['id']}")
                                                g_job = st.selectbox("職業", all_jobs, key=f"gj_{cat_name}_{p['id']}")
                                                g_lvl = st.number_input("等級", 1, 200, 100,
                                                                        key=f"gl_{cat_name}_{p['id']}")
                                                if st.button("新增路人", key=f"gb_{cat_name}_{p['id']}"):
                                                    if g_name:
                                                        m_list.append({"name": g_name, "job": g_job, "level": g_lvl,
                                                                       "is_guest": True, "added_by": my_acc})
                                                        supabase.table("party_posts").update({"members": m_list}).eq(
                                                            "id", p['id']).execute();
                                                        st.rerun()
                                with c2:
                                    st.write("💬 聊天室")
                                    msgs = p.get('messages', [])
                                    for msg in msgs[-5:]: st.caption(f"**{msg['user']}**: {msg['text']}")
                                    with st.form(key=f"ch_{cat_name}_{p['id']}", clear_on_submit=True):
                                        it, bt = st.columns([3, 1])
                                        txt = it.text_input("訊息", label_visibility="collapsed")
                                        if bt.form_submit_button("送出"):
                                            if txt:
                                                msgs.append({"user": my_chars[0]['char_name'], "text": txt})
                                                supabase.table("party_posts").update({"messages": msgs}).eq("id", p[
                                                    'id']).execute();
                                                st.rerun()
                        with col_d:
                            if str(p['owner_id']) == str(current_user.id) or is_admin:
                                if st.button("🗑️", key=f"dp_{cat_name}_{p['id']}"):
                                    supabase.table("party_posts").delete().eq("id", p['id']).execute();
                                    st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        with main_tab2:
            st.caption("🔍 正在找團的玩家：")
            wait_posts = [p for p in all_data if p.get('note') == "TYPE_WAITING"]
            for w in wait_posts:
                ci, ca = st.columns([0.9, 0.1])
                with ci:
                    st.markdown(f'''
                    <div style="border:1px solid #444; padding:8px; border-radius:10px; background:#1e1e1e; margin-bottom:4px;">
                        <span style="color:#ffaa00; font-weight:bold;">【{w["target"]}】</span> {w["char_name"]} (Lv.{w["level"]} {w["job"]}) 
                        ｜ <small style="color:#bbb;">{w["title"]}</small>
                    </div>
                    ''', unsafe_allow_html=True)
                with ca:
                    if str(w['owner_id']) == str(current_user.id) or is_admin:
                        if st.button("撤回", key=f"dw_{w['id']}"):
                            supabase.table("party_posts").delete().eq("id", w['id']).execute();
                            st.rerun()