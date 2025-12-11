import streamlit as st
import random
import math
from fpdf import FPDF
import os
import tempfile
import uuid
import io
import time
import glob 
import json
from PIL import Image

# 嘗試匯入 matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib.font_manager as fm
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    st.error("⚠️ 系統缺少 matplotlib。請檢查 requirements.txt。")

# 匯入 Google Generative AI
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    st.error("⚠️ 系統缺少 google-generativeai。請檢查 requirements.txt。")

# 1. 設定頁面配置
st.set_page_config(page_title="全方位數學自動出題系統 (極速題庫版)", layout="wide", page_icon="⚡")

# 字型設定
font_path = 'TaipeiSansTCBeta-Regular.ttf'
if HAS_MATPLOTLIB and os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False 

# 資料庫檔案名稱
DB_FILENAME = "question_bank_db.json"

# ==========================================
# Part 0: AI 核心邏輯
# ==========================================

def get_ai_variation(image_input, api_key, model_name):
    """
    使用 Google Gemini Vision 模型分析圖片
    """
    if not HAS_GENAI: return None, "缺少 AI 套件"
    if not api_key: return None, "未輸入 API Key"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # 處理圖片來源
        if isinstance(image_input, str): 
            img = Image.open(image_input)
        else: 
            image_input.seek(0)
            img = Image.open(image_input)
        
        # 固定使用「多題拆解」Prompt
        prompt = """
        你是一位專業的國中數學老師。這張圖片中包含「多道」不同的數學題目（可能有編號如 1, 2, 3...）。
        請執行以下任務：
        1. 辨識出圖中所有的題目。
        2. **針對每一道識別出的題目**，各設計 1 道「邏輯相同、但數字改變」的新題目。
           - 例如圖中有 5 題，你就產生 5 題對應的新題目。
           - 題目敘述要通順繁體中文。
        3. 【重要】如果某題涉及幾何圖形，請為該題撰寫 Python matplotlib 程式碼 (fig)。
        
        請嚴格依照以下格式輸出（每一題之間用 "===題組分隔線===" 分隔）：
        [題目] (第1題變體)
        [答案]
        [解析]
        [繪圖程式碼]
        ===題組分隔線===
        [題目] (第2題變體)
        ...
        """
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # 強效重試機制
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                response = model.generate_content([prompt, img], safety_settings=safety_settings)
                break 
            except Exception as e:
                if "429" in str(e):
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 20 # 預處理時可以等久一點
                        time.sleep(wait_time) 
                        continue
                    else:
                        return None, "API 額度已滿 (429)。"
                else:
                    raise e

        if not response.candidates: return None, "AI 拒絕回答。"
        if not response.parts: return None, "AI 回傳空白。"

        return response.text, None
            
    except Exception as e:
        return None, f"AI 處理失敗: {str(e)}"

def parse_ai_response(text):
    """解析 AI 回傳格式"""
    questions = []
    raw_blocks = text.split("===題組分隔線===")
    
    for block in raw_blocks:
        if not block.strip(): continue
        result = {"topic": "🤖 AI-仿題生成", "question": "", "answer": "", "detail": "", "code": None}
        try:
            if '[題目]' in block:
                parts = block.split('[答案]')
                result["question"] = parts[0].replace('[題目]', '').strip()
                remain = parts[1]
                if '[解析]' in remain:
                    parts2 = remain.split('[解析]')
                    result["answer"] = parts2[0].strip()
                    remain2 = parts2[1]
                    if '[繪圖程式碼]' in remain2:
                        parts3 = remain2.split('[繪圖程式碼]')
                        result["detail"] = parts3[0].strip()
                        code_str = parts3[1].strip().replace('```python', '').replace('```', '')
                        if len(code_str) > 10: result["code"] = code_str
                    else:
                        result["detail"] = remain2.strip()
                questions.append(result)
        except: continue
            
    return questions

def execute_drawing_code(code_str):
    if not code_str or not HAS_MATPLOTLIB: return None
    try:
        local_scope = {}
        exec(code_str, globals(), local_scope)
        if 'fig' in local_scope:
            fig = local_scope['fig']
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            buf.seek(0)
            return buf
    except: return None
    return None

# ==========================================
# Part 1: 資料庫管理 (Database Manager)
# ==========================================

def load_database():
    """載入題庫 JSON"""
    if os.path.exists(DB_FILENAME):
        with open(DB_FILENAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_database(data):
    """儲存題庫 JSON"""
    with open(DB_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# Part 5: PDF 匯出
# ==========================================

class PDFExport(FPDF):
    def footer(self):
        self.set_y(-15)
        try: self.set_font("TaipeiSans", '', 10)
        except: self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(exam_data, custom_title, mode="student"):
    pdf = PDFExport()
    pdf.add_page()
    
    font_path = 'TaipeiSansTCBeta-Regular.ttf'
    font_ready = False
    if os.path.exists(font_path):
        pdf.add_font('TaipeiSans', '', font_path, uni=True)
        pdf.set_font("TaipeiSans", '', 14)
        font_ready = True
    else:
        pdf.set_font("Arial", '', 14)

    pdf.cell(0, 10, f"{custom_title} ({'學生' if mode=='student' else '解答'}卷)", ln=True, align='C')
    pdf.ln(10)
    
    for idx, item in enumerate(exam_data):
        q_text = item['question'].replace('$', '').replace('\\times', 'x').replace('\\div', '/')
        t_name = item['topic'].split('-')[-1] if '-' in item['topic'] else item['topic']
        pdf.multi_cell(0, 10, f"Q{idx+1}. [{t_name}] {q_text}")
        
        img_buf = None
        # 如果是即時生成的，會有 image_data (BytesIO)
        if 'image_data' in item: img_buf = item['image_data']
        # 如果是資料庫讀出來的，會有 code (str)，需要現場畫
        elif 'code' in item and item['code']: img_buf = execute_drawing_code(item['code'])
            
        if img_buf:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(img_buf.getvalue())
                    tmp_path = tmp.name
                pdf.image(tmp_path, w=150)
                os.remove(tmp_path)
            except: pass

        if mode == "student":
            pdf.ln(20)
        else:
            pdf.set_text_color(255, 0, 0)
            pdf.multi_cell(0, 8, f"Ans: {item['answer']}")
            pdf.set_font_size(10)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 8, f"解析: {item['detail']}")
            pdf.set_text_color(0, 0, 0)
            if font_ready: pdf.set_font("TaipeiSans", '', 14)
            else: pdf.set_font("Arial", '', 14)
            pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# Part 6: Streamlit UI
# ==========================================

def main():
    st.title("⚡ 全方位數學出題系統 (極速題庫版)")
    
    # 載入現有資料庫
    db_questions = load_database()
    
    if "exam_data" not in st.session_state: st.session_state["exam_data"] = []

    with st.sidebar:
        st.header("⚙️ 設定")
        
        # API Key (僅用於管理員模式)
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ 系統 API Key (管理員用)")
        else:
            api_key = st.text_input("Google API Key", type="password")
        
        custom_title = st.text_input("試卷標題", value="會考衝刺練習")
        
        st.divider()
        
        # 模式選擇
        mode = st.radio("選擇功能", ["📝 快速出題 (學生/家長)", "🛠️ 建立題庫 (管理員)"])
        
        if mode == "📝 快速出題 (學生/家長)":
            st.info(f"📚 目前題庫庫存：{len(db_questions)} 題")
            
            if len(db_questions) == 0:
                st.warning("題庫是空的！請切換到「管理員」模式先生成題目。")
            
            num_questions = st.slider("隨機出題數量", 1, min(50, len(db_questions)) if db_questions else 1, 5)
            generate_btn = st.button("🚀 立即生成 (免等待)", type="primary")
            
        else: # 管理員模式
            st.warning("⚠️ 此模式會消耗 API 額度並需要較長時間。")
            bank_folder = "question_bank"
            
            # 檢查資料夾
            bank_images = []
            if os.path.exists(bank_folder):
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.PNG']:
                    bank_images.extend(glob.glob(os.path.join(bank_folder, ext)))
            
            st.write(f"📂 掃描到 {len(bank_images)} 張原始考卷圖片")
            
            # [修正處] 模型自動偵測，取代寫死 "models/gemini-1.5-flash"
            model_options = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
            selected_model = model_options[0] # 預設值
            
            # 如果有 API Key，嘗試連線列出可用模型
            if api_key and HAS_GENAI:
                try:
                    genai.configure(api_key=api_key)
                    models = list(genai.list_models())
                    available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
                    if available:
                        default_idx = 0
                        for i, m in enumerate(available):
                            if "flash" in m: default_idx = i; break
                        model_options = available
                        selected_model = st.selectbox("選擇 AI 模型", model_options, index=default_idx)
                    else:
                        selected_model = st.selectbox("選擇 AI 模型 (預設)", model_options)
                except Exception as e:
                    # 避免在這裡報錯，改用下拉選單顯示狀態
                    selected_model = st.selectbox(f"AI 模型 (連線異常: {str(e)[:20]}...)", model_options)
            else:
                selected_model = st.selectbox("AI 模型", model_options, disabled=True, help="請先輸入 API Key")
            
            process_btn = st.button("⚡ 開始批量轉化 (存入資料庫)")
            
            # 下載資料庫按鈕
            if db_questions:
                json_str = json.dumps(db_questions, ensure_ascii=False, indent=4)
                st.download_button("💾 下載題庫檔案 (backup)", json_str, file_name="question_bank_db.json", mime="application/json")

    # ==========================================
    # 邏輯執行
    # ==========================================
    
    # [模式 A] 快速出題 (不用 AI，直接讀 JSON)
    if mode == "📝 快速出題 (學生/家長)" and generate_btn:
        if not db_questions:
            st.error("題庫無資料，無法出題。")
        else:
            # 隨機抽取
            st.session_state["exam_data"] = random.sample(db_questions, num_questions)
            st.success(f"已從題庫中隨機抽出 {num_questions} 題！")

    # [模式 B] 管理員批量轉化 (呼叫 AI 並存檔)
    if mode == "🛠️ 建立題庫 (管理員)" and process_btn:
        if not api_key:
            st.error("請輸入 API Key！")
        elif not bank_images:
            st.error("找不到圖片！請確認 'question_bank' 資料夾已上傳。")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            new_questions_count = 0
            
            # 讀取現有資料庫，避免覆蓋
            current_db = load_database()
            
            for idx, img_path in enumerate(bank_images):
                file_name = os.path.basename(img_path)
                status_text.text(f"正在處理：{file_name} ...")
                
                # 為了避免 429，每張圖強制休息 20 秒
                if idx > 0:
                    time.sleep(20)
                
                # 使用選單選到的模型 (selected_model) 而非寫死的字串
                ai_text, error = get_ai_variation(img_path, api_key, selected_model)
                
                if error:
                    st.warning(f"{file_name} 失敗: {error}")
                else:
                    questions = parse_ai_response(ai_text)
                    for q in questions:
                        q['source_file'] = file_name # 標記來源
                        current_db.append(q)
                        new_questions_count += 1
                
                progress_bar.progress((idx + 1) / len(bank_images))
                # 每處理完一張就存檔一次，避免程式中斷全白費
                save_database(current_db)
            
            status_text.text("✅ 全部處理完成！")
            st.success(f"成功新增 {new_questions_count} 題！目前題庫總數：{len(current_db)} 題。")
            st.info("💡 請記得點擊左側「下載題庫檔案」，並將其上傳到 GitHub，這樣下次重啟時資料才不會消失！")

    # ==========================================
    # 顯示試卷
    # ==========================================
    
    if st.session_state["exam_data"]:
        st.markdown(f"## 🏫 {custom_title}")
        col1, col2 = st.columns([2, 1])
        with col1: show_answers = st.checkbox("🔍 顯示解答", value=False)
        with col2:
            if st.button("📥 下載考卷 PDF"):
                pdf_bytes = create_pdf(st.session_state["exam_data"], custom_title, mode="parent")
                st.download_button("點此下載", pdf_bytes, f"{custom_title}.pdf", "application/pdf")

        st.divider()

        for i, q in enumerate(st.session_state["exam_data"]):
            st.markdown(f"**Q{i+1}.**")
            st.info(q['question'])
            
            # 繪圖題處理 (從 JSON 讀出的 code 需要現場執行)
            if 'code' in q and q['code']:
                img_buf = execute_drawing_code(q['code'])
                if img_buf: st.image(img_buf, width=400)
            
            if show_answers:
                st.success(f"Ans: {q['answer']}")
                st.markdown(f"**解析：**\n{q['detail']}")
            st.write("---")

if __name__ == "__main__":
    main()
