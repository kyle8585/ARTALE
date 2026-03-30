import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
import time

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

# 精確 CSS 修正
st.markdown("""
<style>
    /* 基礎間距修正 */
    [data-testid="stForm"] [data-testid="stVerticalBlock"], 
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"],
    [data-testid="stPopover"] [data-testid="stVerticalBlock"] {
        gap: 1rem !important;
    }
    [data-testid="stMain"] [data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }
    [data-testid="stMain"] div[data-testid="stExpander"] {
        margin-top: -8px !important;
        margin-bottom: -8px !important;
    }

    /* 特殊樣式：已加入隊伍 (橘色) */
    .joined-party [data-testid="stExpander"] {
        border: 2px solid #e67e22 !important;
        background-color: rgba(230, 126, 34, 0.05) !important;
        border-radius: 10px !important;
    }
    .joined-party [data-testid="stExpanderSummary"] { 
        color: #e67e22 !important; 
        font-weight: bold !important; 
    }

    /* 特殊樣式：隊伍已滿 (紅色) */
    .full-party [data-testid="stExpander"] {
        border: 2px solid #ff4b4b !important;
        background-color: rgba(255, 75, 75, 0.05) !important;
        border-radius: 10px !important;
        opacity: 0.85;
    }
    .full-party [data-testid="stExpanderSummary"] {
        color: #ff4b4b !important;
        font-style: italic;
    }

    /* 特殊樣式：導覽選中目標 (金黃色) */
    .target-focus [data-testid="stExpander"] {
        border: 3px solid #f1c40f !important;
        box-shadow: 0px 0px 15px rgba(241, 196, 15, 0.4) !important;
        background-color: rgba(241, 196, 15, 0.1) !important;
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
if 'target_party' not in st.session_state: st.session_state.target_party = None


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
    _, center, _ = st.columns([2, 1.8, 2])
    with center:
        st.markdown("<h1 style='text-align: center;'>🍁 Artale 組隊中心</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 帳號登入", "📝 快速註冊"])
        with t1:
            with st.form("login_form"):
                acc = st.text_input("帳號")
                pwd = st.text_input("密碼", type="password")
                if st.form_submit_button("立即登入", use_container_width=True):
                    if acc and pwd:
                        with st.spinner("正在驗證中..."):
                            try:
                                res = supabase.auth.sign_in_with_password({"email": to_internal(acc), "password": pwd})
                                if res.user:
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
                        try:
                            supabase.auth.sign_up({"email": to_internal(new_acc), "password": new_pw})
                            st.success("✅ 註冊成功")
                        except:
                            st.error("註冊失敗")

else:
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]

    # 預先讀取資料
    my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data
    raw_data = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
    all_data = [d for d in raw_data if get_expiry_info(d['created_at'])]

    boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "暗黑龍王"]
    pq_list = ["101", "女神", "金勾海賊王", "羅密歐與茱麗葉"]
    grind_list = ["蛋龍"]
    task_options = ["--- Boss ---"] + boss_list + ["--- PQ ---"] + pq_list + ["--- 團練 ---"] + grind_list

    with st.sidebar:
        st.header(f"👤 {my_acc}")
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

        st.divider()

        # --- 新增：我的隊伍快速導覽 ---
        st.subheader("🚩 我的隊伍導覽")
        my_joined_list = []
        for p in all_data:
            is_o = str(p['owner_id']) == str(current_user.id)
            is_m = any(str(m.get('owner_id')) == str(current_user.id) for m in p.get('members', []))
            if (is_o or is_m) and p.get('note') != "TYPE_WAITING":
                my_joined_list.append(p)

        if my_joined_list:
            for p in my_joined_list:
                role = "👑" if str(p['owner_id']) == str(current_user.id) else "⚔️"
                btn_label = f"{role} {p['target']} | {p['start_time']}"
                if st.button(btn_label, key=f"nav_{p['id']}", use_container_width=True):
                    st.session_state.target_party = p['id']
                    st.rerun()
        else:
            st.caption("尚未加入任何隊伍")

        st.divider()

        with st.expander("🛡️ 角色管理"):
            for c in my_chars:
                c1, c2 = st.columns([3, 1])
                c1.caption(f"{c['char_name']} (Lv.{c['level']} {c['job']})")
                if c2.button("🗑️", key=f"del_c_{c['id']}"):
                    supabase.table("user_characters").delete().eq("id", c['id']).execute()
                    st.rerun()
            st.divider()
            nc_name = st.text_input("新增角色名")
            nc_job = st.selectbox("職業", all_jobs)
            nc_lvl = st.number_input("等級", 1, 200, 100)
            if st.button("儲存新角色", use_container_width=True):
                if nc_name:
                    supabase.table("user_characters").insert(
                        {"owner_id": str(current_user.id), "char_name": nc_name, "job": nc_job,
                         "level": nc_lvl}).execute()
                    st.rerun()

        if my_chars:
            char_map = {f"{c['char_name']} (Lv.{c['level']} {c['job']})": c for c in my_chars}
            char_options = list(char_map.keys())

            with st.expander("📝 我要開團"):
                with st.form("p_form", border=False):
                    t_target = st.selectbox("目標任務", task_options)
                    t_title = st.text_input("隊伍標題")
                    t_time = st.text_input("開打時間", placeholder="例如：現打、20:30、滿開")
                    s_char = st.selectbox("選擇發起角色", char_options)
                    if st.form_submit_button("發布組隊", use_container_width=True):
                        if "---" not in t_target:
                            c = char_map[s_char]
                            supabase.table("party_posts").insert({
                                "title": t_title if t_title else f"{c['char_name']}的團",
                                "start_time": t_time if t_time else "現打",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": t_target, "owner_id": str(current_user.id), "members": [], "messages": [],
                                "note": "TYPE_PARTY"
                            }).execute()
                            time.sleep(0.5)
                            st.rerun()

            with st.expander("🙋 我要待組"):
                with st.form("w_form", border=False):
                    w_target = st.selectbox("想參加的任務", task_options, key="w_target")
                    w_note = st.text_input("備註:打上可配合時間佳")
                    w_char_sel = st.selectbox("使用角色", char_options, key="w_char")
                    if st.form_submit_button("登錄待組", use_container_width=True):
                        if "---" not in w_target:
                            c = char_map[w_char_sel]
                            supabase.table("party_posts").insert({
                                "title": w_note if w_note else "徵求隊伍中",
                                "char_name": c['char_name'], "job": c['job'], "level": c['level'],
                                "target": w_target, "owner_id": str(current_user.id), "members": [], "messages": [],
                                "note": "TYPE_WAITING"
                            }).execute()
                            time.sleep(0.5)
                            st.rerun()

    # --- 5. 主頁面 ---
    if not my_chars:
        st.warning("👋 歡迎！請先在左側建立角色後即可開始使用。")
    else:
        main_tab1, main_tab2 = st.tabs(["⚔️ 隊伍列表", "🍁 待組佈告欄"])

        with main_tab1:
            cats = ["全部", "Boss遠征", "組隊任務", "團練"]
            sub_tabs = st.tabs(cats)
            party_only = [p for p in all_data if p.get('note') != "TYPE_WAITING"]

            for idx, cat_name in enumerate(cats):
                with sub_tabs[idx]:
                    f = party_only
                    if cat_name == "Boss遠征":
                        f = [p for p in party_only if p['target'] in boss_list]
                    elif cat_name == "組隊任務":
                        f = [p for p in party_only if p['target'] in pq_list]
                    elif cat_name == "團練":
                        f = [p for p in party_only if p['target'] in grind_list]

                    # 排序：被導覽選中的隊伍置頂
                    f = sorted(f, key=lambda x: x['id'] == st.session_state.target_party, reverse=True)

                    for p in f:
                        m_list = p.get('members', [])
                        cur_count = len(m_list) + 1
                        is_full = cur_count >= 6
                        is_owner = str(p['owner_id']) == str(current_user.id)
                        is_member = any(str(m.get('owner_id')) == str(current_user.id) for m in m_list)
                        is_joined = is_owner or is_member
                        is_target = st.session_state.target_party == p['id']

                        p_time_val = p.get('start_time', '現打')

                        col_m, col_d = st.columns([0.94, 0.06])
                        with col_m:
                            status_class = ""
                            full_tag = ""
                            if is_target:
                                status_class = "target-focus"
                                full_tag = "🎯 "
                            elif is_full:
                                status_class = "full-party"
                                full_tag = "(已滿) "
                            elif is_joined:
                                status_class = "joined-party"

                            st.markdown(f'<div class="{status_class}">', unsafe_allow_html=True)
                            exp_label = f"{full_tag}【{p['target']}】{p['title']} ｜ 🕒 {p_time_val} ｜ 👥 {cur_count}/6"

                            # 若為目標則自動展開
                            with st.expander(exp_label, expanded=is_target):
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"👑 **隊長**：{p['char_name']} (Lv.{p['level']} {p['job']})")
                                    st.markdown(f"⏰ **預計時間**：{p_time_val}")

                                    if is_owner or is_admin:
                                        with st.popover("⚙️ 管理隊伍 (修改標題/時間)", use_container_width=True):
                                            new_title = st.text_input("編輯標題", value=p['title'],
                                                                      key=f"et_{cat_name}_{p['id']}")
                                            new_time = st.text_input("編輯時間", value=p_time_val,
                                                                     key=f"es_{cat_name}_{p['id']}")
                                            if st.button("更新隊伍資訊", key=f"ub_{cat_name}_{p['id']}",
                                                         use_container_width=True):
                                                try:
                                                    supabase.table("party_posts").update(
                                                        {"title": new_title, "start_time": new_time}).eq("id", p[
                                                        'id']).execute()
                                                    st.success("更新成功！")
                                                    time.sleep(0.5)
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"更新失敗: {e}")

                                    st.divider()
                                    for m_idx, m in enumerate(m_list):
                                        mc1, mc2 = st.columns([4, 1.5])
                                        suffix = f" <small style='color:gray'>(路人-由{m.get('added_by', '未知')}新增)</small>" if m.get(
                                            'is_guest') else ""
                                        mc1.markdown(f"└ {m['name']} (Lv.{m['level']} {m['job']}){suffix}",
                                                     unsafe_allow_html=True)
                                        if is_owner or is_admin or str(m.get('owner_id')) == str(current_user.id):
                                            if mc2.button("退出", key=f"k_{cat_name}_{p['id']}_{m_idx}"):
                                                m_list.pop(m_idx)
                                                supabase.table("party_posts").update({"members": m_list}).eq("id", p[
                                                    'id']).execute()
                                                st.rerun()

                                    if not is_full:
                                        with st.popover("➕ 加入/新增隊員", use_container_width=True):
                                            sub_t1, sub_t2 = st.tabs(["選擇角色", "手動路人"])
                                            with sub_t1:
                                                sel_to_join = st.selectbox("選擇角色加入", char_options,
                                                                           key=f"sel_j_{cat_name}_{p['id']}")
                                                if st.button("確認加入", key=f"btn_j_{cat_name}_{p['id']}"):
                                                    cj = char_map[sel_to_join]
                                                    m_list.append({"name": cj['char_name'], "job": cj['job'],
                                                                   "level": cj['level'],
                                                                   "owner_id": str(current_user.id)})
                                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                                 p[
                                                                                                                     'id']).execute()
                                                    st.rerun()
                                            with sub_t2:
                                                g_name = st.text_input("路人名稱", key=f"gn_{cat_name}_{p['id']}")
                                                g_job = st.selectbox("職業", all_jobs, key=f"gj_{cat_name}_{p['id']}")
                                                g_lvl = st.number_input("等級", 1, 200, 100,
                                                                        key=f"gl_{cat_name}_{p['id']}")
                                                if st.button("新增路員", key=f"gb_{cat_name}_{p['id']}"):
                                                    if g_name:
                                                        m_list.append({"name": g_name, "job": g_job, "level": g_lvl,
                                                                       "is_guest": True, "added_by": my_acc})
                                                        supabase.table("party_posts").update({"members": m_list}).eq(
                                                            "id", p['id']).execute()
                                                        st.rerun()
                                    else:
                                        st.error("🚫 隊伍已滿")
                                with c2:
                                    st.write("💬 聊天室")
                                    msgs = p.get('messages', [])
                                    for msg in msgs[-5:]: st.caption(f"**{msg['user']}**: {msg['text']}")
                                    with st.form(key=f"ch_{cat_name}_{p['id']}", clear_on_submit=True):
                                        it, bt = st.columns([3, 1])
                                        txt = it.text_input("訊息", label_visibility="collapsed")
                                        if bt.form_submit_button("送出"):
                                            if txt:
                                                # 使用第一個角色名發言
                                                speaker = my_chars[0]['char_name'] if my_chars else my_acc
                                                msgs.append({"user": speaker, "text": txt})
                                                supabase.table("party_posts").update({"messages": msgs}).eq("id", p[
                                                    'id']).execute()
                                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        with col_d:
                            if is_owner or is_admin:
                                if st.button("🗑️", key=f"dp_{cat_name}_{p['id']}"):
                                    supabase.table("party_posts").delete().eq("id", p['id']).execute()
                                    st.rerun()

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
                            supabase.table("party_posts").delete().eq("id", w['id']).execute()
                            st.rerun()