import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# 1. 初始化 Supabase
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")
st.title("🍁 Artale 線上組隊中心")

# --- 2. 定義清單 ---
all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
grind_list = ["蛋龍"]
all_targets = pq_list + boss_list + grind_list
categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]

# --- 3. 側邊欄：發布新組隊 ---
with st.sidebar:
    st.header("📝 我要開團")
    with st.form("party_form", clear_on_submit=True):
        new_title = st.text_input("隊伍標題", placeholder="例如：101 五場速刷")
        char_name = st.text_input("隊長 ID")
        job = st.selectbox("隊長職業", all_jobs)
        level = st.number_input("隊長等級", 1, 200, 120)
        target = st.selectbox("目標", all_targets)
        admin_pw = st.text_input("設置管理密碼 (選填)", type="password", help="設置後，修改、踢人或撤團需驗證此密碼")
        note = st.text_input("備註")
        submit = st.form_submit_button("發布組隊", use_container_width=True)

        if submit and char_name:
            data = {
                "title": new_title if new_title else f"{char_name} 的組隊",
                "char_name": char_name, "job": job, "level": level, "target": target, "note": note,
                "password": admin_pw if admin_pw else None,
                "members": [], "messages": []
            }
            supabase.table("party_posts").insert(data).execute()
            st.success("發布成功！")
            st.rerun()

# --- 4. 主頁面：讀取資料 ---
tabs = st.tabs(categories)
try:
    response = supabase.table("party_posts").select("*").order("created_at", desc=True).execute()
    posts = response.data if response.data else []
except:
    posts = []

# --- 5. 渲染列表 ---
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
            member_count = len(m_list) + 1
            expander_label = f"【{p['target']}】 {p.get('title', '無標題')} ｜ 👑 {p['char_name']} ｜ 👥 {member_count}/6"

            with st.expander(expander_label, expanded=False):
                col_info, col_chat = st.columns([1, 1])

                with col_info:
                    st.markdown(f"**👑 隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                    if p.get('note'): st.caption(f"📝 備註: {p['note']}")
                    st.code(f"/找人 {p['char_name']}", language="bash")

                    st.divider()
                    st.write("👥 **隊員清單:**")
                    if m_list:
                        for idx, m in enumerate(m_list):
                            st.write(f" └ {m['name']} (Lv.{m.get('level', '??')} {m['job']})")
                    else:
                        st.caption("目前尚無隊員")

                    st.write("")
                    b1, b2, b3 = st.columns(3)

                    # ➕ 加入隊伍
                    with b1:
                        with st.popover("➕ 加入", use_container_width=True):
                            m_name = st.text_input("你的 ID", key=f"in_name_{cat_name}_{p['id']}")
                            m_job = st.selectbox("職業", all_jobs, key=f"in_job_{cat_name}_{p['id']}")
                            m_lvl = st.number_input("等級", 1, 200, 100, key=f"in_lvl_{cat_name}_{p['id']}")
                            if st.button("確認加入", key=f"in_btn_{cat_name}_{p['id']}", use_container_width=True):
                                if m_name:
                                    m_list.append({"name": m_name, "job": m_job, "level": m_lvl})
                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                 p["id"]).execute()
                                    st.rerun()

                    # ✏️ 修改與成員管理 (整合刪除功能)
                    with b2:
                        with st.popover("✏️ 管理", use_container_width=True):
                            new_t = st.text_input("修改標題", value=p.get('title', ''),
                                                  key=f"ed_t_{cat_name}_{p['id']}")
                            new_n = st.text_input("修改備註", value=p.get('note', ''), key=f"ed_n_{cat_name}_{p['id']}")

                            st.write("---")
                            st.write("👥 **成員移除:**")
                            member_to_remove = None
                            if m_list:
                                for idx, m in enumerate(m_list):
                                    c_m1, c_m2 = st.columns([3, 1])
                                    c_m1.caption(f"{m['name']} ({m['job']})")
                                    if c_m2.button("踢除", key=f"rm_{cat_name}_{p['id']}_{idx}"):
                                        member_to_remove = idx
                            else:
                                st.caption("目前無隊員可移除")

                            st.write("---")
                            input_pw = ""
                            if p.get('password'):
                                input_pw = st.text_input("輸入管理密碼", type="password",
                                                         key=f"ed_pw_{cat_name}_{p['id']}")

                            if st.button("執行變更", key=f"do_ed_{cat_name}_{p['id']}", use_container_width=True,
                                         type="primary"):
                                if not p.get('password') or input_pw == p['password']:
                                    # 處理成員移除
                                    final_m_list = m_list
                                    if member_to_remove is not None:
                                        final_m_list = [m for i_m, m in enumerate(m_list) if i_m != member_to_remove]

                                    # 更新資料庫
                                    supabase.table("party_posts").update({
                                        "title": new_t,
                                        "note": new_n,
                                        "members": final_m_list
                                    }).eq("id", p["id"]).execute()
                                    st.success("變更已套用！")
                                    st.rerun()
                                else:
                                    st.error("密碼錯誤！")

                    # 🗑️ 撤除全團
                    with b3:
                        with st.popover("🗑️ 撤團", use_container_width=True):
                            can_delete = False
                            if p.get('password'):
                                check_pw = st.text_input("輸入密碼以撤團", type="password",
                                                         key=f"pw_chk_{cat_name}_{p['id']}")
                                if st.button("確認撤團", key=f"real_del_{cat_name}_{p['id']}", type="primary"):
                                    if check_pw == p['password']:
                                        can_delete = True
                                    else:
                                        st.error("密碼錯誤！")
                            else:
                                if st.button("直接撤團", key=f"direct_del_{cat_name}_{p['id']}", type="primary"):
                                    can_delete = True

                            if can_delete:
                                supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                                st.rerun()

                with col_chat:
                    st.write("💬 **隊伍聊天室**")
                    chat_box = st.container(height=180)
                    msg_list = p.get('messages', [])
                    with chat_box:
                        if not msg_list: st.caption("目前尚無訊息...")
                        for m in msg_list: st.markdown(f"**{m['user']}:** {m['text']}")

                    with st.form(key=f"chat_form_{cat_name}_{p['id']}", clear_on_submit=True):
                        c1, c2 = st.columns([4, 1])
                        u_msg = c1.text_input("訊息", placeholder="說點什麼...", key=f"msg_input_{cat_name}_{p['id']}")
                        if c2.form_submit_button("送出") and u_msg:
                            sender = st.session_state.get(f"in_name_{cat_name}_{p['id']}", "匿名")
                            msg_list.append({"user": sender if sender else "匿名", "text": u_msg})
                            supabase.table("party_posts").update({"messages": msg_list}).eq("id", p["id"]).execute()
                            st.rerun()