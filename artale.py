for p in filtered:
    m_list = p.get('members', [])
    is_owner = (str(p.get('owner_id')) == str(current_user.id))
    has_admin_power = (is_owner or is_admin)

    # --- 核心改動：右上角刪除按鈕列 ---
    col_title, col_del = st.columns([0.9, 0.1])

    with col_title:
        # 這裡放原本的 Expander，但把標題稍微縮短一點以預留空間
        label = f"【{p['target']}】 {p.get('title', '無標題')} ｜ 👑 {p['char_name']} ｜ 👥 {len(m_list) + 1}/6"
        exp = st.expander(label)

    with col_del:
        # 只有權限者看得到右上角的刪除
        if has_admin_power:
            if st.button("🗑️", key=f"top_del_{p['id']}", help="撤銷此組隊", type="primary"):
                supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                st.rerun()

    # Expander 內部的內容
    with exp:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"**👑 隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
            if p.get('note'): st.info(f"📝 備註: {p['note']}")
            st.code(f"/找人 {p['char_name']}", language="bash")

            st.divider()
            st.write("👥 **隊員名單:**")
            for idx, m in enumerate(m_list):
                c1, c2 = st.columns([4, 1.5])
                c1.write(f" └ {m['name']} (Lv.{m.get('level', '?')} {m['job']})")

                m_owner_id = str(m.get('owner_id', ''))
                if has_admin_power:
                    if c2.button("踢除", key=f"rm_{cat_name}_{p['id']}_{idx}"):
                        m_list.pop(idx);
                        supabase.table("party_posts").update({"members": m_list}).eq("id", p["id"]).execute();
                        st.rerun()
                elif m_owner_id == str(current_user.id):
                    if c2.button("退出", key=f"ex_{cat_name}_{p['id']}_{idx}"):
                        m_list.pop(idx);
                        supabase.table("party_posts").update({"members": m_list}).eq("id", p["id"]).execute();
                        st.rerun()

            st.write("")
            # 下方保留「加入」與「修改」按鈕
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                if not is_owner:
                    with st.popover("➕ 加入隊伍", use_container_width=True):
                        join_char = st.selectbox("選角色", ["手動輸入"] + char_options, key=f"jc_{cat_name}_{p['id']}")
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
                            m_list.append({"name": f_jn, "job": f_jj, "level": f_jl, "owner_id": str(current_user.id)})
                            supabase.table("party_posts").update({"members": m_list}).eq("id", p["id"]).execute();
                            st.rerun()

            with btn_col2:
                if has_admin_power:
                    with st.popover("✏️ 修改資訊", use_container_width=True):
                        nt = st.text_input("新標題", value=p['title'], key=f"et_{cat_name}_{p['id']}")
                        nn = st.text_input("新備註", value=p['note'], key=f"en_{cat_name}_{p['id']}")
                        if st.button("更新", key=f"ub_{cat_name}_{p['id']}", use_container_width=True):
                            supabase.table("party_posts").update({"title": nt, "note": nn}).eq("id", p["id"]).execute();
                            st.rerun()

        with col2:
            st.write("💬 隊伍聊天室")
            c_box = st.container(height=250)
            msgs = p.get('messages', [])
            with c_box:
                for m in msgs: st.markdown(f"**{m['user']}:** {m['text']}")
            with st.form(key=f"cf_{cat_name}_{p['id']}", clear_on_submit=True):
                c1, c2 = st.columns([4, 1])
                u_msg = c1.text_input("訊息內容", key=f"mi_{cat_name}_{p['id']}")
                if c2.form_submit_button("送出") and u_msg:
                    msgs.append({"user": my_acc, "text": u_msg});
                    supabase.table("party_posts").update({"messages": msgs}).eq("id", p["id"]).execute();
                    st.rerun()