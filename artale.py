import streamlit as st
from supabase import create_client, Client

# 1. 初始化 Supabase 連線
url = "https://ybhbqrlimofarkmcyrrk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliaGJxcmxpbW9mYXJrbWN5cnJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTM1MTMsImV4cCI6MjA5MDM2OTUxM30.4FQbRtE2mKR1XKhCJs4_tl94TRMCq8O9ORRtxk3bqto"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Artale 組隊中心", page_icon="🍁", layout="wide")
st.title("🍁 Artale 線上組隊中心")

# --- 2. 定義資料清單 ---
boss_list = ["拉圖斯(普)", "拉圖斯(困難)", "殘暴炎魔", "龍王"]
pq_list = ["101", "羅密歐與茱麗葉", "金勾海賊王", "女神"]
grind_list = ["蛋龍"]
all_targets = pq_list + boss_list + grind_list
all_jobs = ["英雄", "聖騎", "黑騎", "火毒", "冰雷", "主教", "刀賊", "標賊", "弓手", "弩手", "拳霸", "槍神"]
categories = ["全部", "BOSS遠征", "組隊任務", "野外團練"]

# --- 3. 側邊欄：發布新組隊 ---
with st.sidebar:
    st.header("📝 我要開團")
    with st.form("party_form", clear_on_submit=True):
        char_name = st.text_input("隊長 ID")
        job = st.selectbox("隊長職業", all_jobs)
        level = st.number_input("隊長等級", 1, 200, 120)
        target = st.selectbox("目標", all_targets)
        note = st.text_input("備註 (例：缺僧侶)")
        submit = st.form_submit_button("發布組隊")

        if submit:
            if char_name:
                data = {
                    "char_name": char_name,
                    "job": job,
                    "level": level,
                    "target": target,
                    "note": note,
                    "members": []
                }
                try:
                    supabase.table("party_posts").insert(data).execute()
                    st.success("發布成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"發布失敗：{e}")
            else:
                st.error("請輸入角色 ID")

# --- 4. 主頁面：讀取與顯示 ---
tabs = st.tabs(categories)

# 讀取資料
try:
    # 這裡確保抓取所有欄位，並按時間排序
    response = supabase.table("party_posts").select("*").order("created_at", desc=True).execute()
    posts = response.data if response.data else []
except Exception as e:
    st.error(f"資料讀取失敗：{e}")
    posts = []

# 渲染分頁內容
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

        if filtered:
            for p in filtered:
                # 使用唯一 Key 避免重複元件錯誤
                with st.expander(f"【{p['target']}】 {p['char_name']} - {p.get('note', '')}", expanded=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"👑 **隊長:** {p['char_name']} (Lv.{p['level']} {p['job']})")
                        st.code(f"/找人 {p['char_name']}", language="bash")

                        m_list = p.get('members', [])
                        if m_list:
                            st.write("👥 **隊員:**")
                            for m in m_list:
                                st.write(f" └ {m['name']} (Lv.{m['level']} {m['job']})")

                        st.divider()
                        # 加入功能
                        with st.popover("➕ 加入此團", key=f"pop_{cat_name}_{p['id']}"):
                            m_name = st.text_input("你的 ID", key=f"in_{cat_name}_{p['id']}")
                            m_job = st.selectbox("職業", all_jobs, key=f"ij_{cat_name}_{p['id']}")
                            m_lvl = st.number_input("等級", 1, 200, 100, key=f"il_{cat_name}_{p['id']}")
                            if st.button("送出加入申請", key=f"btn_{cat_name}_{p['id']}"):
                                if m_name:
                                    new_m = {"name": m_name, "job": m_job, "level": m_lvl}
                                    m_list.append(new_m)
                                    supabase.table("party_posts").update({"members": m_list}).eq("id",
                                                                                                 p["id"]).execute()
                                    st.rerun()

                    with c2:
                        if st.button("撤除", key=f"del_{cat_name}_{p['id']}"):
                            supabase.table("party_posts").delete().eq("id", p["id"]).execute()
                            st.rerun()
        else:
            st.info(f"目前沒有 {cat_name} 的隊伍。")