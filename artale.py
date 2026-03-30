import streamlit as st
from supabase import create_client, Client

# --- 1. 初始化與設定 ---
st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")

URL = "https://ybhbqrlimofarkmcyrrk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"


@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)


supabase = get_supabase()

# 初始化 Session State
if 'user' not in st.session_state: st.session_state.user = None


# 轉換工具
def to_internal(acc):
    return f"{acc.strip()}@artale.local"


# --- 2. 登入/註冊頁面 ---
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
                        st.error("❌ 登入失敗：請檢查帳號密碼")

        with t2:
            st.caption("提示：註冊成功後請切換至登入頁面。")
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
    my_acc = current_user.email.split('@')[0]  # 取得登入顯示名稱

    st.title("🍁 Artale 線上組隊中心")

    # 定義清單
    all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
    boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
    pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
    grind_list = ["蛋龍"]
    all_targets = pq_list + boss_list + grind_list
    categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]

    # 側邊欄：發布與登出
    with st.sidebar:
        st.header(f"👤 您好, {my_acc}")
        if st.button("登出系統", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

        st.divider()
        st.header("📝 我要開團")
        with st.form("party_form", clear_on_submit=True):
            new_title = st.text_input("隊伍標題", placeholder="例如：101 五場速刷")
            job = st.selectbox("我的職業", all_jobs)
            level = st.number_input("我的等級", 1, 200, 120)
            target = st.selectbox("目標", all_targets)
            note = st.text_input("備註")
            submit = st.form_submit_button("發布組隊", use_container_width=True)

            if submit:
                # 確保 data 裡面的欄位與 SQL 完全對應
                data = {
                    "title": str(new_title) if new_title else f"{my_acc} 的組隊",
                    "char_name": str(my_acc),
                    "job": str(job),
                    "level": int(level),
                    "target": str(target),
                    "note": str(note),
                    "owner_id": str(current_user.id),  # 強制轉為字串避免 UUID 錯誤
                    "members": [],
                    "messages": []
                }
                try:
                    supabase.table("party_posts").insert(data).execute()
                    st.success("✅ 發布成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 發布失敗，具體原因：{e}")

    # 主頁面：讀取資料
    tabs = st.tabs(categories)
    try:
        posts = supabase.table("party_posts").select("*").order("created_at", desc=True).execute().data
    except:
        posts = []

    # 渲染列表
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
                is_owner = (p.get('owner_id') == current_user.id)
                member_count = len(m_list) + 1
                label = f"【{p['target']}】 {p.get('title', '無標題')} ｜ 👑 {p['char_name']} ｜ 👥 {member_count}/6"

                with st.expander(label):
                    col_info, col_chat = st.columns([1, 1])

                    with col_info:
                        st.markdown(f"**👑 隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                        if p.get('note'): st.caption(f"📝 備註: {p['note']}")
                        st.code(f"/找人 {p['char_name']}", language="bash")

                        st.divider()
                        st.write("👥 **隊員清單:**")
                        for idx, m in enumerate(m_list):
                            c_m1, c_m2 = st.columns([4, 1])
                            c_m1.write(f" └ {m['name']} (Lv.{m.get('level', '??')} {m['job']})")
                            # 只有隊長可以看到剔除按鈕
                            if is_owner:
                                if c_m2.button("踢除", key=f"rm_{p['id']}_{idx}"):
                                    m_list.pop(idx)
                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                 p["id"]).execute()
                                    st.rerun()

                        st.write("")
                        b1, b2, b3 = st.columns(3)

                        with b1:  # 加入隊伍
                            if not is_owner:
                                with st.popover("➕ 加入", use_container_width=True):
                                    m_job = st.selectbox("職業", all_jobs, key=f"j_{p['id']}")
                                    m_lvl = st.number_input("等級", 1, 200, 100, key=f"l_{p['id']}")
                                    if st.button("確認加入", key=f"btn_{p['id']}", use_container_width=True):
                                        m_list.append({"name": my_acc, "job": m_job, "level": m_lvl})
                                        supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                     p["id"]).execute()
                                        st.rerun()
                                        else:
                                        # 加上 key 確保每個隊伍的按鈕 ID 都是唯一的
                                        st.button("隊長本人", disabled=True, use_container_width=True,
                                                  key=f"owner_btn_{p['id']}")

                        with b2:  # 修改備註 (僅限隊長)
                            if is_owner:
                                with st.popover("✏️ 修改", use_container_width=True):
                                    new_t = st.text_input("修改標題", value=p['title'], key=f"et_{p['id']}")
                                    new_n = st.text_input("修改備註", value=p['note'], key=f"en_{p['id']}")
                                    if st.button("更新", key=f"up_{p['id']}", use_container_width=True):
                                        supabase.table("party_posts").update({"title": new_t, "note": new_n}).eq("id",
                                                                                                                 p[
                                                                                                                     "id"]).execute()
                                        st.rerun()

                        with b3:  # 撤團 (僅限隊長)
                            if is_owner:
                                if st.button("🗑️ 撤團", key=f"del_{p['id']}", type="primary", use_container_width=True):
                                    supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                                    st.rerun()

                    with col_chat:
                        st.write("💬 **隊伍聊天室**")
                        chat_box = st.container(height=180)
                        msg_list = p.get('messages', [])
                        with chat_box:
                            if not msg_list: st.caption("目前尚無訊息...")
                            for m in msg_list: st.markdown(f"**{m['user']}:** {m['text']}")

                        with st.form(key=f"chat_{p['id']}", clear_on_submit=True):
                            c1, c2 = st.columns([4, 1])
                            u_msg = c1.text_input("訊息", placeholder="說點什麼...", key=f"msg_in_{p['id']}")
                            if c2.form_submit_button("送出") and u_msg:
                                msg_list.append({"user": my_acc, "text": u_msg})