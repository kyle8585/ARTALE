import streamlit as st
from supabase import create_client, Client

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"

# ⭐ 管理員帳號設定
ADMIN_ACC = "admin"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()

if 'user' not in st.session_state: st.session_state.user = None


def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 2. 登入/註冊介面 ---
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
            st.caption("提示：註冊成功後請切換至登入分頁。")
            with st.form("signup_form"):
                new_acc = st.text_input("自訂帳號")
                new_pw = st.text_input("設定密碼 (至少6位)", type="password")
                if st.form_submit_button("註冊帳號", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": to_internal(new_acc), "password": new_pw})
                        st.success(f"✅ 註冊成功！帳號: {new_acc}")
                    except Exception as e:
                        st.error(f"❌ 註冊失敗: {e}")

# --- 3. 主程式介面 (登入後) ---
else:
    current_user = st.session_state.user
    my_acc = current_user.email.split('@')[0]
    is_admin = (my_acc == ADMIN_ACC)

    # 先定義好所有清單，避免出現 NameError
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
    boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
    pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
    grind_list = ["蛋龍"]
    all_targets = pq_list + boss_list + grind_list
    categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]

    # 讀取「我的角色」資料
    try:
        my_chars = supabase.table("user_characters").select("*").eq("owner_id", str(current_user.id)).execute().data
    except:
        my_chars = []
    char_options = [f"{c['char_name']} (Lv.{c['level']} {c['job']})" for c in my_chars]

    with st.sidebar:
        user_label = f"👤 {my_acc} [管理者]" if is_admin else f"👤 {my_acc}"
        st.header(user_label)
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

        st.divider()
        with st.expander("🛡️ 我的角色管理"):
            for c in my_chars:
                c1, c2 = st.columns([3, 1])
                c1.caption(f"{c['char_name']} - {c['job']} (Lv.{c['level']})")
                if c2.button("🗑️", key=f"del_c_{c['id']}"):
                    supabase.table("user_characters").delete().eq("id", c['id']).execute()
                    st.rerun()
            nc_name = st.text_input("角色名稱", key="nc_name")
            nc_job = st.selectbox("職業", all_jobs, key="nc_job")
            nc_lvl = st.number_input("等級", 1, 200, 100, key="nc_lvl")
            if st.button("儲存角色", use_container_width=True):
                if nc_name:
                    supabase.table("user_characters").insert(
                        {"owner_id": str(current_user.id), "char_name": nc_name, "job": nc_job,
                         "level": nc_lvl}).execute()
                    st.rerun()

        st.divider()
        st.header("📝 我要開團")
        with st.form("party_form", clear_on_submit=True):
            selected_char = st.selectbox("選擇發團角色", ["手動輸入"] + char_options)
            title = st.text_input("隊伍標題")
            target = st.selectbox("目標", all_targets)
            note = st.text_input("備註")
            m_job = st.selectbox("手動職業", all_jobs) if selected_char == "手動輸入" else None
            m_lvl = st.number_input("手動等級", 1, 200, 120) if selected_char == "手動輸入" else None

            if st.form_submit_button("發布組隊", use_container_width=True):
                f_name, f_job, f_lvl = my_acc, m_job, m_lvl
                if selected_char != "手動輸入":
                    c_idx = char_options.index(selected_char)
                    f_name, f_job, f_lvl = my_chars[c_idx]['char_name'], my_chars[c_idx]['job'], my_chars[c_idx][
                        'level']
                supabase.table("party_posts").insert(
                    {"title": title if title else f"{f_name} 的組隊", "char_name": f_name, "job": f_job, "level": f_lvl,
                     "target": target, "note": note, "owner_id": str(current_user.id), "members": [],
                     "messages": []}).execute()
                st.rerun()

    # 主頁面：顯示列表
    tabs = st.tabs(categories)
    try:
        posts = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
    except:
        posts = []

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

            if not filtered:
                st.info(f"目前沒有 {cat_name} 的隊伍。")
                continue

            for p in filtered:
                m_list = p.get('members', [])
                is_owner = (str(p.get('owner_id')) == str(current_user.id))
                member_count = len(m_list) + 1
                label = f"【{p['target']}】 {p.get('title', '無標題')} ｜ 👑 {p['char_name']} ｜ 👥 {member_count}/6"

                with st.expander(label):
                    col_info, col_chat = st.columns([1, 1])
                    with col_info:
                        st.markdown(f"**👑 隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                        st.code(f"/找人 {p['char_name']}", language="bash")
                        st.write("👥 **隊員:**")
                        for idx, m in enumerate(m_list):
                            c1, c2 = st.columns([4, 1])
                            c1.write(f" └ {m['name']} (Lv.{m.get('level', '?')} {m['job']})")
                            if is_owner or is_admin:
                                if c2.button("踢除", key=f"rm_{cat_name}_{p['id']}_{idx}"):
                                    m_list.pop(idx)
                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                 p["id"]).execute()
                                    st.rerun()

                        st.write("")
                        b1, b2, b3 = st.columns(3)
                        with b1:
                            if not is_owner:
                                with st.popover("➕ 加入", use_container_width=True):
                                    join_char = st.selectbox("使用角色", ["手動輸入"] + char_options,
                                                             key=f"jc_{cat_name}_{p['id']}")
                                    j_job = st.selectbox("職業", all_jobs,
                                                         key=f"jj_{cat_name}_{p['id']}") if join_char == "手動輸入" else ""
                                    j_lvl = st.number_input("等級", 1, 200, 100,
                                                            key=f"jl_{cat_name}_{p['id']}") if join_char == "手動輸入" else 0
                                    if st.button("確認加入", key=f"jb_{cat_name}_{p['id']}", use_container_width=True):
                                        f_jn, f_jj, f_jl = my_acc, j_job, j_lvl
                                        if join_char != "手動輸入":
                                            c_idx = char_options.index(join_char)
                                            f_jn, f_jj, f_jl = my_chars[c_idx]['char_name'], my_chars[c_idx]['job'], \
                                            my_chars[c_idx]['level']
                                        m_list.append({"name": f_jn, "job": f_jj, "level": f_jl})
                                        supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                     p["id"]).execute()
                                        st.rerun()
                            else:
                                st.button("隊長本人", disabled=True, use_container_width=True,
                                          key=f"ob_{cat_name}_{p['id']}")

                        with b2:
                            if is_owner:
                                with st.popover("✏️ 修改", use_container_width=True):
                                    nt = st.text_input("標題", value=p['title'], key=f"et_{cat_name}_{p['id']}")
                                    nn = st.text_input("備註", value=p['note'], key=f"en_{cat_name}_{p['id']}")
                                    if st.button("更新", key=f"ub_{cat_name}_{p['id']}", use_container_width=True):
                                        supabase.table("party_posts").update({"title": nt, "note": nn}).eq("id", p[
                                            "id"]).execute()
                                        st.rerun()
                        with b3:
                            if is_owner or is_admin:
                                del_label = "🔥 強制撤團" if is_admin and not is_owner else "🗑️ 撤團"
                                if st.button(del_label, key=f"db_{cat_name}_{p['id']}", type="primary",
                                             use_container_width=True):
                                    supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                                    st.rerun()

                    with col_chat:
                        st.write("💬 聊天室")
                        c_box = st.container(height=180)
                        msgs = p.get('messages', [])
                        with c_box:
                            for m in msgs: st.markdown(f"**{m['user']}:** {m['text']}")
                        with st.form(key=f"cf_{cat_name}_{p['id']}", clear_on_submit=True):
                            c1, c2 = st.columns([4, 1])
                            u_msg = c1.text_input("訊息", key=f"mi_{cat_name}_{p['id']}")
                            if c2.form_submit_button("送出") and u_msg:
                                msgs.append({"user": my_acc, "text": u_msg})
                                supabase.table("party_posts").update({"messages": msgs}).eq("id", p["id"]).execute()
                                st.rerun()