def login_page():
    # 縮小介面並置中
    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        st.markdown("<h2 style='text-align: center;'>🍁 Artale 組隊中心</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["登入系統", "註冊帳號"])

        with tab1:
            with st.form("login_form"):
                # 這裡要確保括號完整
                acc = st.text_input("帳號", value=st.session_state.temp_acc)
                pwd = st.text_input("密碼", type="password", value=st.session_state.temp_pw)

                if st.form_submit_button("立即登入", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({
                            "email": to_internal(acc),
                            "password": pwd
                        })
                        st.session_state.user = res.user
                        st.rerun()
                    except:
                        st.error("❌ 登入失敗：帳號或密碼錯誤")

        with tab2:
            st.caption("✨ 提示：帳號可使用任何文字，無須 Email 格式。")
            with st.form("signup_form"):
                new_acc = st.text_input("設定帳號")
                new_pw = st.text_input("設定密碼", type="password")
                if st.form_submit_button("確認申請", use_container_width=True):
                    if not new_acc or len(new_pw) < 6:
                        st.error("⚠️ 帳號不能為空，且密碼需至少 6 位數")
                    else:
                        try:
                            supabase.auth.sign_up({
                                "email": to_internal(new_acc),
                                "password": new_pw
                            })
                            st.session_state.temp_acc = new_acc
                            st.session_state.temp_pw = new_pw
                            st.success(f"✅ 帳號「{new_acc}」申請成功！請切換至登入頁。")
                        except:
                            st.error("❌ 申請失敗：帳號可能已存在")