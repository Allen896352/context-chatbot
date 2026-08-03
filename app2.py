import streamlit as st
from google import genai
from google.genai import types
import csv
from datetime import datetime
import os

# ==========================================
# 1. 初始化與 API 設定
# ==========================================
API_KEY = "AQ.Ab8RN6KGrTcgzZ5yt6vG3Z4ERVmkPvqG440d9NwaT__uEqIRyQ" 

st.set_page_config(page_title="AI 服務體驗研究", page_icon="🤖")

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)
client = st.session_state.client

# 狀態管理
if "pre_survey_completed" not in st.session_state:
    st.session_state.pre_survey_completed = False
if "context_style" not in st.session_state:
    st.session_state.context_style = None
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "survey_completed" not in st.session_state:
    st.session_state.survey_completed = False
if "user_interaction_count" not in st.session_state:
    st.session_state.user_interaction_count = 0

# 建立儲存資料的 CSV 檔案 (擴充了前測的欄位)
CSV_FILE = 'research_data.csv'
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            '時間', 
            '前測_過去AI使用頻率', '前測_過去AI滿意度', '前測_對AI的信任度', 
            '情境前測內容', '系統分配屬性', '互動次數', 
            '後測_題目1', '後測_題目2', '後測_題目3', '後測_題目4'
        ])


# ==========================================
# 2. 階段一：前測問卷 (過去對 AI 的感受)
# ==========================================
if not st.session_state.pre_survey_completed:
    st.title("歡迎參與 AI 服務體驗測試")
    st.write("這是一項關於 AI 聊天機器人服務體驗的研究。在開始之前，請先與我們分享您過去的經驗：")
    
    with st.form("pre_test_form"):
        st.write("📝 **第一部分：過去 AI 使用經驗**")
        
        # 前測題目 (你可以根據研究需求修改)
        st.session_state.pre_freq = st.selectbox(
            "1. 請問您過去使用 AI 客服（或 ChatGPT 等聊天機器人）的頻率為何？",
            ("從未使用過", "很少使用 (幾個月一次)", "偶爾使用 (每週幾次)", "經常使用 (幾乎每天)")
        )
        
        st.session_state.pre_sat = st.slider(
            "2. 過去與 AI 客服互動的經驗中，您的整體滿意度為何？ (1=非常不滿意，5=非常滿意)", 1, 5, 3
        )
        
        st.session_state.pre_trust = st.slider(
            "3. 您多大程度上信任 AI 機器人能幫您解決問題？ (1=完全不信任，5=非常信任)", 1, 5, 3
        )
        
        submit_pre_test = st.form_submit_button("下一步")
        
        if submit_pre_test:
            st.session_state.pre_survey_completed = True
            st.rerun()

# ==========================================
# 3. 階段二：隱性情境判定 (User Context-Culture Orientation)
# ==========================================
elif st.session_state.pre_survey_completed and st.session_state.context_style is None:
    st.title("情境模擬測試")
    st.write("謝謝您的填寫！接下來，請先回答一個簡單的日常情境題：")
    st.info("**「如果您要請朋友順路幫忙買晚餐，您通常會怎麼傳訊息跟他說？」**")
    
    user_input = st.text_input("請輸入您的真實反應：", placeholder="例如：幫我買份排骨飯...")
    
    if st.button("開始進入系統") and user_input:
        with st.spinner('系統設定中...'):
            analysis_prompt = f"""
            請分析以下這句話屬於高語境還是低語境溝通。
            高語境：依賴隱含意義、關係線索、比較間接簡略。
            低語境：直接、明確、精準且資訊完整。
            使用者說：「{user_input}」
            請只回答「高語境」或「低語境」三個字。
            """
            
            result_response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=analysis_prompt
            )
            result = result_response.text.strip()
            
            st.session_state.onboarding_text = user_input
            
            if "高" in result:
                st.session_state.context_style = "High-Context"
                system_instruction = """
                你現在是一個「高語境」的聊天機器人。你的核心目標是創造『社會親近感』。
                1. 關係導向：展現溫暖、同理心，像朋友一樣聊天。
                2. 語氣自然：多使用口語化詞彙（如：懂了、沒問題、太好了吧），並適當加入 Emoji。
                3. 重視情境：不要生硬地條列資訊，用對話的方式引導，讓使用者覺得「你懂他」。
                """
            else:
                st.session_state.context_style = "Low-Context"
                system_instruction = """
                你現在是一個「低語境」的聊天機器人。你的核心目標是創造『訊息清晰度』。
                1. 任務導向：直接、明確、精準，不說廢話。
                2. 語氣專業：不要使用表情符號(Emoji)，不要有多餘的情感寒暄。
                3. 資訊完整：務必使用「條列式」或「表格」來整理重點，追求最高效率的資訊傳遞。
                """
            
            config = types.GenerateContentConfig(system_instruction=system_instruction)
            st.session_state.chat_session = client.chats.create(
                model="gemini-3.1-flash-lite",
                config=config
            )
            
            st.session_state.messages.append({"role": "assistant", "content": "您好，設定已完成。請問今天有什麼我可以協助您的嗎？（請隨意與我進行幾次對話測試）"})
            st.rerun()

# ==========================================
# 4. 階段三：對話體驗與後測問卷
# ==========================================
elif st.session_state.context_style is not None and not st.session_state.survey_completed:
    st.title("💬 智慧服務小幫手")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("請輸入您的問題..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        st.session_state.user_interaction_count += 1
        
        response = st.session_state.chat_session.send_message(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        st.rerun()
    
    st.markdown("---")
    
    REQUIRED_INTERACTIONS = 3 
    
    if st.session_state.user_interaction_count >= REQUIRED_INTERACTIONS:
        st.write("📝 **體驗結束後，請協助完成以下問卷：**")
        with st.form("research_survey"):
            st.write("請以 1 (非常不同意) 到 5 (非常同意) 進行評分：")
            
            q1_score = st.slider("Q1. [題目1佔位符] 我認為這個機器人的說話方式很適合我。", 1, 5, 3)
            q2_score = st.slider("Q2. [題目2佔位符] 這個機器人讓我有親切的感覺。", 1, 5, 3)
            q3_score = st.slider("Q3. [題目3佔位符] 機器人提供的資訊非常清楚明白。", 1, 5, 3)
            q4_score = st.slider("Q4. [題目4佔位符] 再次使用意圖。", 1, 5, 3)
            
            submit_btn = st.form_submit_button("送出所有結果並結束測試")
            
            if submit_btn:
                # 這裡會一次把「前測資料 + 系統屬性 + 後測資料」寫進同一列，方便分析
                with open(CSV_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                        st.session_state.pre_freq,     # 前測頻率
                        st.session_state.pre_sat,      # 前測滿意度
                        st.session_state.pre_trust,    # 前測信任度
                        st.session_state.onboarding_text, 
                        st.session_state.context_style, 
                        st.session_state.user_interaction_count,
                        q1_score, 
                        q2_score, 
                        q3_score, 
                        q4_score
                    ])
                st.session_state.survey_completed = True
                st.rerun()
    else:
        remaining = REQUIRED_INTERACTIONS - st.session_state.user_interaction_count
        st.info(f"💡 請再與機器人進行 {remaining} 次對話，測試結束後的問卷才會解鎖喔！")

# ==========================================
# 5. 階段四：測試完成畫面
# ==========================================
elif st.session_state.survey_completed:
    st.success("🎉 問卷已送出！非常感謝您參與本次研究。")
    st.balloons()
