import streamlit as st
from supabase import create_client, Client

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"

ADMIN_ACC = "akuy7788"
REG_SECRET = "場外artale"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()

if 'user' not in st.session_state: st.session_state.user = None


def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 2. 登入/註冊介面 ---
if st.session_state.user is None:
    _, center, _ = st.columns([2, 1.2, 2])
    with center:
        st.write("")
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
                        st.error("❌ 登入失敗：請檢查帳號密碼。")
        with t2:
            with st.form("signup_form"):
                new_acc = st.text_input("自訂帳號")
                new_pw = st.text_input("設定密碼 (至少6位)", type="password")
                input_key = st.text_input("註冊金鑰", type="password")
                if st.form_submit_button("註冊帳號", use_container_width=True):
                    if input_key == REG_SECRET:
                        try:
                            supabase.auth.sign_up({"email": to_internal(new_acc), "password": new_pw})
                            st.success("✅ 註冊成功！")
                        except:
                            st.error("❌ 註冊失敗")
                    else:
                        st.error("❌ 金鑰錯誤")
else:
    # --- 3. 登入後主程式 ---
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)

    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
    boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
    pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
    grind_list = ["蛋龍"]
    all_targets = pq_list + boss_list + grind_list
    categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]

    try:
        my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data
    except:
        my_chars = []

    char_map = {f"{c['char_name']} (Lv.{c['level']} {c['job']})": c for c in my_chars}
    char_options = list(char_map.keys())

    with st.sidebar:
        st.header(f"👤 {my_acc}")
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out();
            st.session_state.user = None;
            st.rerun()

        st.divider()
        with st.expander("🛡️ 我的角色管理"):
            for c in my_chars:
                c1, c2 = st.columns([3, 1])
                c1.caption(f"{c['char_name']} (Lv.{c['level']} {c['job']})")
                if c2.button("🗑️", key=f"side_del_c_{c['id']}"):
                    supabase.table("user_characters").delete().eq("id", c['id']).execute();
                    st.rerun()
            nc_name = st.text_input("角色名稱")
            nc_job = st.selectbox("職業", all_jobs)
            nc_lvl = st.number_input("等級", 1, 200, 100)
            if st.button("儲存角色", use_container_width=True):
                if nc_name:
                    supabase.table("user_characters").insert(
                        {"owner_id": str(current_user.id), "char_name": nc_name, "job": nc_job,
                         "level": nc_lvl}).execute();
                    st.rerun()

        st.divider()
        st.header("📝 我要開團")
        with st.form("party_form"):
            s_char = st.selectbox("選擇發團角色", ["請選擇"] + char_options)
            t_title = st.text_input("隊伍標題")
            t_target = st.selectbox("目標", all_targets)
            t_note = st.text_input("備註")
            if st.form_submit_button("發布組隊", use_container_width=True):
                if s_char != "請選擇":
                    c_data = char_map[s_char]
                    supabase.table("party_posts").insert({
                        "title": t_title if t_title else f"{c_data['char_name']} 的團",
                        "char_name": c_data['char_name'], "job": c_data['job'], "level": c_data['level'],
                        "target": t_target, "note": t_note, "owner_id": str(current_user.id),
                        "members": [], "messages": []
                    }).execute();
                    st.rerun()

    # --- 4. 主頁面 ---
    tabs = st.tabs(categories)
    posts = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data

    for i, cat_name in enumerate(categories):
        with tabs[i]:
            if cat_name == "全部":
                filtered = posts
            elif cat_name == "BOSS遠征":
                filtered = [p for p in posts if p['target'] in boss_list]
            elif cat_name == "組隊任務":
                filtered = [p for p in posts if p['target'] in pq_list]
            else:
                filtered = [p for p in posts if p['target'] in grind_list]

            if not filtered: st.info(f"目前沒有 {cat_name} 的隊伍。"); continue

            for p in filtered:
                m_list = p.get('members', [])
                is_leader = (str(p.get('owner_id')) == str(current_user.id))
                has_admin = (is_leader or is_admin)

                # 修正此處佈局定義，解決 NameError: col
                col_main, col_btn = st.columns([0.94, 0.06])

                with col_main:
                    label = f"【{p['target']}】 {p['title']} ｜ 👑 {p['char_name']} ｜ 👥 {len(m_list) + 1}/6"
                    exp = st.expander(label, expanded=True)

                with col_btn:
                    if has_admin:
                        if st.button("🗑️", key=f"del_{cat_name}_{p['id']}", type="primary"):
                            supabase.table("party_posts").delete().eq("id", p["id"]).execute();
                            st.rerun()

                with exp:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.markdown(f"**👑 隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                        if p['note']: st.info(f"📝 備註: {p['note']}")

                        st.divider()
                        st.write("👥 **隊員名單:**")
                        for idx, m in enumerate(m_list):
                            mc1, mc2 = st.columns([4, 1.5])
                            mc1.write(f" └ {m['name']} (Lv.{m.get('level', '?')} {m['job']})")
                            if has_admin or str(m.get('owner_id')) == str(current_user.id):
                                if mc2.button("退出/踢除", key=f"kick_{cat_name}_{p['id']}_{idx}"):
                                    m_list.pop(idx);
                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                 p["id"]).execute();
                                    st.rerun()

                        st.write("")
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            with st.popover("➕ 加入隊伍", use_container_width=True):
                                if has_admin:
                                    st.subheader("🔧 手動新增 (隊長專用)")
                                    mn = st.text_input("隊員名稱", key=f"mn_{cat_name}_{p['id']}")
                                    mj = st.selectbox("職業", all_jobs, key=f"mj_{cat_name}_{p['id']}")
                                    ml = st.number_input("等級", 1, 200, 100, key=f"ml_{cat_name}_{p['id']}")
                                    if st.button("確認手動加入", key=f"mb_{cat_name}_{p['id']}"):
                                        if mn:
                                            m_list.append({"name": mn, "job": mj, "level": ml, "owner_id": "manual"})
                                            supabase.table("party_posts").update({"members": m_list}).eq("id", p[
                                                "id"]).execute();
                                            st.rerun()
                                    st.divider()

                                st.subheader("👤 以我的角色加入")
                                if char_options:
                                    join_sel = st.selectbox("選取角色", char_options, key=f"js_{cat_name}_{p['id']}")
                                    if st.button("確認加入", key=f"jb_{cat_name}_{p['id']}"):
                                        tc = char_map[join_sel]
                                        m_list.append({"name": tc['char_name'], "job": tc['job'], "level": tc['level'],
                                                       "owner_id": str(current_user.id)})
                                        supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                     p["id"]).execute();
                                        st.rerun()
                                else:
                                    st.warning("請先建立角色")

                        with btn_c2:
                            if has_admin:
                                with st.popover("✏️ 修改隊伍", use_container_width=True):
                                    ut = st.text_input("新標題", value=p['title'], key=f"ut_{cat_name}_{p['id']}")
                                    un = st.text_input("新備註", value=p['note'], key=f"un_{cat_name}_{p['id']}")
                                    if st.button("更新資訊", key=f"ub_{cat_name}_{p['id']}"):
                                        supabase.table("party_posts").update({"title": ut, "note": un}).eq("id", p[
                                            "id"]).execute();
                                        st.rerun()

                    with c2:
                        st.write("💬 **隊伍聊天室**")
                        chat_box = st.container(height=280)
                        msgs = p.get('messages', [])
                        with chat_box:
                            for m in msgs: st.markdown(f"**{m['user']}:** {m['text']}")

                        with st.form(key=f"chat_form_{cat_name}_{p['id']}", clear_on_submit=True):
                            cf1, cf2 = st.columns([4, 1])
                            msg_i = cf1.text_input("訊息", key=f"msg_i_{cat_name}_{p['id']}",
                                                   label_visibility="collapsed")
                            if cf2.form_submit_button("送出"):
                                if msg_i:
                                    s_name = my_chars[0]['char_name'] if my_chars else my_acc
                                    msgs.append({"user": s_name, "text": msg_i})
                                    supabase.table("party_posts").update({"messages": msgs}).eq("id",
                                                                                                p["id"]).execute();
                                    st.rerun()