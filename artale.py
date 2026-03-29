# --- 主頁面：分類顯示 ---
categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]
tabs = st.tabs(categories)

try:
    response = supabase.table("party_posts").select("*").order("created_at", desc=True).execute()
    posts = response.data
except Exception as e:
    st.error(f"資料讀取失敗：{e}")
    posts = []

for i, cat_name in enumerate(categories):
    with tabs[i]:
        if cat_name == "全部":
            filtered_posts = posts
        elif cat_name == "BOSS遠征":
            filtered_posts = [p for p in posts if p['target'] in boss_list]
        elif cat_name == "組隊任務":
            filtered_posts = [p for p in posts if p['target'] in pq_list]
        else:
            filtered_posts = [p for p in posts if p['target'] in grind_list]

        if filtered_posts:
            for p in filtered_posts:
                # 這裡增加 cat_name 讓每個分頁的 ID 唯一
                with st.expander(f"【{p['target']}】 {p['char_name']} 的隊伍 - 備註：{p.get('note', '無')}",
                                 expanded=True):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"👑 **隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                        st.code(f"/找人 {p['char_name']}", language="bash")

                        members = p.get('members', [])
                        if members:
                            st.write("👥 **目前成員:**")
                            for m in members:
                                st.write(f" └ {m['name']} (Lv.{m['level']} {m['job']})")

                        st.divider()
                        # 注意這裡的 key 加入了 cat_name
                        with st.popover("➕ 我要加入此團", key=f"pop_{cat_name}_{p['id']}"):
                            m_name = st.text_input("你的 ID", key=f"mname_{cat_name}_{p['id']}")
                            m_job = st.selectbox("你的職業", all_jobs, key=f"mjob_{cat_name}_{p['id']}")
                            m_lvl = st.number_input("你的等級", 1, 200, 100, key=f"mlvl_{cat_name}_{p['id']}")
                            if st.button("確認加入", key=f"btn_{cat_name}_{p['id']}"):
                                if m_name:
                                    new_member = {"name": m_name, "job": m_job, "level": m_lvl}
                                    members.append(new_member)
                                    supabase.table("party_posts").update({"members": members}).eq("id",
                                                                                                  p["id"]).execute()
                                    st.rerun()

                    with col2:
                        # 這裡的 key 也加入了 cat_name
                        if st.button("撤除全團", key=f"del_{cat_name}_{p['id']}"):
                            supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                            st.rerun()
        else:
            st.info(f"目前沒有 {cat_name} 的隊伍。")