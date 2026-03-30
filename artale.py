import streamlit as st
from supabase import create_client, Client

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"

ADMIN_ACC = "admin"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()

if 'user' not in st.session_state: st.session_state.user = None


def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 2. 登入介面 ---
if st.session_state.user is None:
    _, center, _ = st.columns([1, 1.5, 1])
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
                        st.error("❌ 登入失敗：請檢查帳號密碼。")
        with t2:
            with st.form("signup_form"):
                new_acc = st.text_input("自訂帳號")
                new_pw = st.text_input("密碼 (至少6位)", type="password")
                if st.form_submit_button("註冊帳號", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": to_internal(new_acc), "password": new_pw})
                        st.success(f"✅ 註冊成功！帳號: {new_acc}")
                    except Exception as e:
                        st.error(f"❌ 註冊失敗: {e}")
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
        st.header(f"👤 {my_acc} {'[管理者]' if is_admin else ''}")
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out();
            st.session_state.user = None;
            st.rerun()

        st.divider()
        with st.expander("🛡️ 我的角色管理"):
            for c in my_chars:
                c1, c2 = st.columns([3, 1])
                c1.caption(f"{c['char_name']} (Lv.{c['level']} {c['job']})")
                if c2.button("🗑️", key=f"sidebar_del_c_{c['id']}"):
                    supabase.table("user_characters").delete().eq("id", c['id']).execute();
                    st.rerun()
            nc_name = st.text_input("角色名稱", key="nc_name")
            nc_job = st.selectbox("職業", all_jobs, key="nc_job")
            nc_lvl = st.number_input("等級", 1, 200, 100, key="nc_lvl")
            if st.button("儲存角色", use_container_width=True):
                if nc_name:
                    supabase.table("user_characters").insert(
                        {"owner_id": str(current_user.id), "char_name": nc_name, "job": nc_job,
                         "level": nc_lvl}).execute();
                    st.rerun()

        st.divider()
        st.header("📝 我要開團")
        with st.form("party_form", clear_on_submit=True):
            selected_char_label = st.selectbox("選擇發團角色", ["請選擇角色"] + char_options)
            title = st.text_input("隊伍標題")
            target = st.selectbox("目標", all_targets)
            note = st.text_input("備註")
            if st.form_submit_button("發布組隊", use_container_width=True):
                if selected_char_label != "請選擇角色":
                    c_data = char_map[selected_char_label]
                    supabase.table("party_posts").insert({
                        "title": title if title else f"{c_data['char_name']} 的團",
                        "char_name": c_data['char_name'],
                        "job": c_data['job'],
                        "level": c_data['level'],
                        "target": target,
                        "note": note,
                        "owner_id": str(current_user.id),
                        "members": [],
                        "messages": []
                    }).execute();
                    st.rerun()
                else:
                    st.warning("請先選擇一個角色再發帖！")

    # --- 4. 主頁面：列表顯示 ---
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
                has_admin_power = (is_leader or is_admin)

                # --- 右上角佈局 ---
                col_title, col_del = st.columns([0.92, 0.08])

                with col_title:
                    label = f"【{p['target']}】 {p.get('title', '無標題')} ｜ 👑 {p['char_name']} ｜ 👥 {len(m_list) + 1}/6"
                    exp = st.expander(label)

                with col_del:
                    if has_admin_power:
                        # 刪除按鈕 key 加入 cat_name 避免重複
                        if st.button("🗑️", key=f"del_party_{cat_name}_{p['id']}", help="刪除隊伍", type="primary"):
                            supabase.table("party_posts").delete().eq("id", p["id"]).execute();
                            st.rerun()

                with exp:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown(f"**👑 隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                        if p.get('note'): st.info(f"📝 備註: {p['note']}")
                        st.code(f"/找人 {p['char_name']}", language="bash")

                        st.divider()
                        st.write("👥 **隊員名單:**")
                        for idx, m in enumerate(m_list):
                            mc1, mc2 = st.columns([4, 1.5])
                            mc1.write(f" └ {m['name']} (Lv.{m.get('level', '?')} {m['job']})")

                            m_owner_id = str(m.get('owner_id', ''))
                            if has_admin_power:
                                if mc2.button("踢除", key=f"kick_{cat_name}_{p['id']}_{idx}"):
                                    m_list.pop(idx);
                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                 p["id"]).execute();
                                    st.rerun()
                            elif m_owner_id == str(current_user.id):
                                if mc2.button("退出", key=f"exit_{cat_name}_{p['id']}_{idx}"):
                                    m_list.pop(idx);
                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                 p["id"]).execute();
                                    st.rerun()

                        st.write("")
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if not is_leader:
                                with st.popover("➕ 加入隊伍", use_container_width=True):
                                    if char_options:
                                        # 關鍵修正：此處 key 加入了 cat_name
                                        join_label = st.selectbox("選擇角色", char_options,
                                                                  key=f"sel_join_{cat_name}_{p['id']}")
                                        if st.button("確認加入", key=f"btn_join_{cat_name}_{p['id']}",
                                                     use_container_width=True):
                                            target_c = char_map[join_label]
                                            m_list.append({
                                                "name": target_c['char_name'],
                                                "job": target_c['job'],
                                                "level": target_c['level'],
                                                "owner_id": str(current_user.id)
                                            })
                                            supabase.table("party_posts").update({"members": m_list}).eq("id", p[
                                                "id"]).execute();
                                            st.rerun()
                                    else:
                                        st.warning("請先在左側建立角色！")

                        with btn_c2:
                            if has_admin_power:
                                with st.popover("✏️ 修改資訊", use_container_width=True):
                                    nt = st.text_input("新標題", value=p['title'],
                                                       key=f"edit_title_{cat_name}_{p['id']}")
                                    nn = st.text_input("新備註", value=p['note'], key=f"edit_note_{cat_name}_{p['id']}")
                                    if st.button("更新", key=f"btn_update_{cat_name}_{p['id']}",
                                                 use_container_width=True):
                                        supabase.table("party_posts").update({"title": nt, "note": nn}).eq("id", p[
                                            "id"]).execute();
                                        st.rerun()

                    with col2:
                        st.write("💬 隊伍聊天室")
                        c_box = st.container(height=250)
                        msgs = p.get('messages', [])
                        with c_box:
                            for m in msgs: st.markdown(f"**{m['user']}:** {m['text']}")
                        with st.form(key=f"form_chat_{cat_name}_{p['id']}", clear_on_submit=True):
                            f1, f2 = st.columns([4, 1])
                            u_msg = f1.text_input("訊息內容", key=f"input_chat_{cat_name}_{p['id']}")
                            if f2.form_submit_button("送出") and u_msg:
                                sender_name = my_chars[0]['char_name'] if my_chars else my_acc
                                msgs.append({"user": sender_name, "text": u_msg})
                                supabase.table("party_posts").update({"messages": msgs}).eq("id", p["id"]).execute();
                                st.rerun()