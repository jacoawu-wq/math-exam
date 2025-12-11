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
from PIL import Image

# 嘗試匯入 matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib.font_manager as fm
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    st.error("⚠️ 系統缺少 matplotlib。請檢查 requirements.txt 是否包含 'matplotlib'，並請嘗試 Reboot App。")

# 匯入 Google Generative AI
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    st.error("⚠️ 系統缺少 google-generativeai。請檢查 requirements.txt，並請嘗試 Reboot App。")

# 1. 設定頁面配置
st.set_page_config(page_title="全方位數學自動出題系統 (AI 旗艦版)", layout="wide", page_icon="🛡️")

# 字型設定
font_path = 'TaipeiSansTCBeta-Regular.ttf'
if HAS_MATPLOTLIB and os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False 

# ==========================================
# Part 0: AI 核心邏輯
# ==========================================

def get_ai_variation(image_input, api_key, model_name):
    """
    使用 Google Gemini Vision 模型分析圖片
    預設模式：自動拆解圖片中的多道題目 (Multi-Question Mode)
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
        
        # [關鍵更新] 固定使用「多題拆解」Prompt
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
        
        # 重試機制 (針對 429 錯誤)
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                response = model.generate_content([prompt, img], safety_settings=safety_settings)
                break 
            except Exception as e:
                if "429" in str(e):
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 10
                        time.sleep(wait_time) 
                        continue
                    else:
                        return None, "API 額度已滿 (429)。請讓程式休息 2 分鐘後再試。"
                else:
                    raise e

        if not response.candidates: return None, "AI 拒絕回答。"
        if not response.parts: return None, "AI 回傳空白。"

        return response.text, None
            
    except Exception as e:
        return None, f"AI 處理失敗: {str(e)}"

def parse_ai_response(text):
    """解析 AI 回傳格式 (支援多題解析)"""
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
            
    if not questions and text:
        return [{"topic": "🤖 AI-仿題生成", "question": text, "answer": "解析失敗", "detail": "格式不符"}]
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
# Part 1: 基礎題目生成
# ==========================================
def generate_number_basic():
    a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-10, 10)
    if c==0: c=1
    q_str = f"計算： ${a} + ({b}) \\times ({c})$"
    ans_str = str(a + b * c)
    return {"topic": "基礎-數與量", "question": q_str, "answer": ans_str, "detail": "四則運算"}

def generate_linear_algebra_basic():
    x = random.randint(-10, 10); a = random.choice([-3, 2, 3]); b = random.randint(-10, 10)
    c = a * x + b
    return {"topic": "基礎-代數", "question": f"解 ${a}x + ({b}) = {c}$", "answer": f"$x={x}$", "detail": "移項"}

def generate_geometry_basic():
    a1 = random.randrange(30, 80, 5); a2 = random.randrange(30, 80, 5)
    return {"topic": "基礎-幾何", "question": f"三角形兩內角為 {a1}°, {a2}°，求第三角。", "answer": f"{180-a1-a2}°", "detail": "內角和"}

TOPIC_MAPPING = {
    "基礎 - 數與量": generate_number_basic,
    "基礎 - 代數": generate_linear_algebra_basic,
    "基礎 - 幾何": generate_geometry_basic,
}

def generate_exam_data(selected_topics, num_questions):
    if not selected_topics: return []
    exam_list = []
    for i in range(num_questions):
        topic_name = selected_topics[i % len(selected_topics)]
        if topic_name in TOPIC_MAPPING:
            exam_list.append(TOPIC_MAPPING[topic_name]())
    return exam_list

# ==========================================
# Part 5: PDF 匯出
# ==========================================

class PDFExport(FPDF):
    def footer(self):
        self.set_y(-15)
        try: self.set_font("TaipeiSans", '', 10)
        except: self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(exam_data, custom_title, mode="student", image_paths=None):
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
        if 'image_data' in item: img_buf = item['image_data']
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

    if image_paths:
        pdf.add_page()
        if font_ready: pdf.set_font("TaipeiSans", '', 16)
        pdf.cell(0, 10, "--- 原始試題區 (Reference) ---", ln=True, align='C')
        for img_source in image_paths:
            try:
                if isinstance(img_source, str):
                    pdf.image(img_source, x=10, w=190)
                else:
                    img_source.seek(0)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(img_source.read())
                        tmp_path = tmp.name
                    pdf.image(tmp_path, x=10, w=190)
                    os.remove(tmp_path)
                pdf.ln(10)
            except: pass

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# Part 6: Streamlit UI
# ==========================================

def main():
    st.title("🗄️ 全方位數學出題系統 (題庫旗艦版)")
    
    if "exam_data" not in st.session_state: st.session_state["exam_data"] = []
    if "ai_generated_questions" not in st.session_state: st.session_state["ai_generated_questions"] = []
    if "selected_bank_images" not in st.session_state: st.session_state["selected_bank_images"] = []

    with st.sidebar:
        st.header("⚙️ 設定")
        
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ 系統 API Key")
        else:
            api_key = st.text_input("Google API Key", type="password")
        
        # [關鍵更新] 自動列出可用模型，解決 404 問題
        model_options = ["models/gemini-1.5-flash", "models/gemini-pro"]
        selected_model = model_options[0]
        if api_key and HAS_GENAI:
            try:
                genai.configure(api_key=api_key)
                models = list(genai.list_models())
                available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
                if available:
                    default_idx = 0
                    # 優先選 flash 模型，速度快且便宜
                    for i, m in enumerate(available):
                        if "flash" in m: default_idx = i; break
                    model_options = available
                    selected_model = st.selectbox("AI 模型 (自動偵測)", model_options, index=default_idx)
            except:
                st.warning("⚠️ 無法連線 Google 取得模型列表，將使用預設值。")
        
        bank_folder = "question_bank"
        bank_images = []
        if os.path.exists(bank_folder):
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.PNG']:
                bank_images.extend(glob.glob(os.path.join(bank_folder, ext)))
        
        custom_title = st.text_input("試卷標題", value="會考衝刺練習")
        
        st.divider()
        st.subheader("1. 題目來源")
        source_mode = st.radio("選擇模式", ["📸 上傳圖片 (單次)", "📂 題庫隨機抽取", "🎲 純演算法生成"])
        
        uploaded_files = []
        bank_sample_count = 0
        
        if source_mode == "📸 上傳圖片 (單次)":
            uploaded_files = st.file_uploader("上傳圖片", type=['png', 'jpg'], accept_multiple_files=True)
            
        elif source_mode == "📂 題庫隨機抽取":
            if not bank_images:
                st.error(f"❌ 找不到 'question_bank' 資料夾！")
            else:
                st.success(f"✅ 題庫中共有 {len(bank_images)} 張圖片")
                bank_sample_count = st.slider("從題庫隨機抽出幾張圖?", 1, min(10, len(bank_images)), 3)
        
        st.divider()
        st.subheader("2. 隨機題庫 (非AI)")
        all_topics = list(TOPIC_MAPPING.keys())
        selected_topics = st.multiselect("選擇單元", options=all_topics)
        num_questions = st.slider("題目數量", 0, 50, 5)

        generate_btn = st.button("🚀 建立考卷", type="primary")

    if generate_btn:
        st.session_state["exam_data"] = []
        st.session_state["ai_generated_questions"] = []
        st.session_state["selected_bank_images"] = [] 
        
        # 生成非 AI 題
        if selected_topics:
             st.session_state["exam_data"] = generate_exam_data(selected_topics, num_questions)

        target_images = []
        
        if source_mode == "📸 上傳圖片 (單次)" and uploaded_files:
            target_images = uploaded_files 
            st.session_state["selected_bank_images"] = uploaded_files
            
        elif source_mode == "📂 題庫隨機抽取" and bank_images:
            target_images = random.sample(bank_images, bank_sample_count)
            st.session_state["selected_bank_images"] = target_images
            st.info(f"🎲 已從題庫抽出: {[os.path.basename(p) for p in target_images]}")

        if target_images:
            if not api_key:
                st.warning("⚠️ 未輸入 API Key，僅顯示原始圖片。")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, img_source in enumerate(target_images):
                    status_text.text(f"🤖 AI 分析第 {idx+1}/{len(target_images)} 題...")
                    
                    if idx > 0:
                        for s in range(10, 0, -1):
                            status_text.text(f"⏳ 冷卻中 (避免 429 錯誤)... {s} 秒")
                            time.sleep(1)
                    
                    # 預設多題拆解模式
                    ai_text, error = get_ai_variation(img_source, api_key, selected_model)
                    
                    if error:
                        st.warning(f"圖片分析失敗: {error}")
                    else:
                        new_qs = parse_ai_response(ai_text)
                        for q in new_qs:
                            q["source_img_idx"] = idx 
                            st.session_state["ai_generated_questions"].append(q)
                    
                    progress_bar.progress((idx + 1) / len(target_images))
                
                status_text.text("✅ 完成！")
                progress_bar.empty()
        
        st.success("考卷生成完畢！")

    has_content = st.session_state["ai_generated_questions"] or st.session_state["selected_bank_images"] or st.session_state["exam_data"]
    
    if has_content:
        st.markdown(f"## 🏫 {custom_title}")
        col1, col2 = st.columns([2, 1])
        with col1: show_answers = st.checkbox("🔍 顯示解答", value=False)
        with col2:
            final_data = st.session_state["exam_data"] + st.session_state["ai_generated_questions"]
            if st.button("📥 下載 PDF"):
                pdf_bytes = create_pdf(final_data, custom_title, mode="parent", image_paths=st.session_state["selected_bank_images"])
                st.download_button("點此下載", pdf_bytes, f"{custom_title}.pdf", "application/pdf")

        st.divider()

        if st.session_state["exam_data"]:
            st.subheader("📝 基礎試題")
            for i, q in enumerate(st.session_state["exam_data"]):
                st.markdown(f"**Q{i+1}. [{q['topic']}]**")
                st.markdown(q['question'])
                if show_answers: st.success(f"Ans: {q['answer']}"); st.caption(q['detail'])
                st.write("---")

        if st.session_state["ai_generated_questions"]:
            st.subheader("📝 AI 變題區")
            for i, q in enumerate(st.session_state["ai_generated_questions"]):
                source_label = f" (源自圖 {q.get('source_img_idx', 0)+1})"
                st.markdown(f"**AI-Q{i+1}{source_label}.**")
                
                col_q, col_img = st.columns([2, 1])
                with col_q:
                    st.info(q['question'])
                    if 'code' in q and q['code']:
                        img_buf = execute_drawing_code(q['code'])
                        if img_buf: st.image(img_buf, width=400)
                    if show_answers: st.success(q['answer']); st.markdown(q['detail'])
                
                with col_img:
                    idx = q.get("source_img_idx")
                    images_list = st.session_state["selected_bank_images"]
                    if idx is not None and idx < len(images_list):
                        img_src = images_list[idx]
                        if isinstance(img_src, str): st.image(img_src, caption="題庫原圖")
                        else: st.image(img_src, caption="上傳原圖")
                st.write("---")
        
        elif st.session_state["selected_bank_images"]:
            st.subheader("📷 原始試題")
            for img in st.session_state["selected_bank_images"]:
                st.image(img, width=500)

if __name__ == "__main__":
    main()
