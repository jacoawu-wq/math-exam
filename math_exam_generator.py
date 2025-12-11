import streamlit as st
import random
import math
from fpdf import FPDF
import os
import tempfile
import uuid
import io
import time
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
st.set_page_config(page_title="全方位數學自動出題系統 (AI 省流版)", layout="wide", page_icon="🛡️")

# 字型設定
font_path = 'TaipeiSansTCBeta-Regular.ttf'
if HAS_MATPLOTLIB and os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False 

# ==========================================
# Part 0: AI 核心邏輯 (Gemini Integration)
# ==========================================

def get_ai_variation(image_file, api_key, model_name, num_variations=1):
    """
    使用 Google Gemini Vision 模型分析圖片 (批次生成多題以節省額度)
    """
    if not HAS_GENAI: return None, "缺少 AI 套件"
    if not api_key: return None, "未輸入 API Key"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        image_file.seek(0)
        img = Image.open(image_file)
        
        # [關鍵更新] Prompt 支援一次生成多題
        prompt = f"""
        你是一位專業的國中數學老師。請分析這張圖片中的數學題目：
        1. 找出核心觀念。
        2. 請根據這個觀念，連續設計【{num_variations} 道】不同的新題目。
           - 每一題的數字與情境都要不同。
           - 題目敘述要通順繁體中文。
        3. 【重要】如果題目涉及幾何圖形，請為每一題撰寫一段 Python matplotlib 程式碼。
           - 必須將圖表物件存入變數 `fig`。
           - 若有文字標註，請直接使用中文。
        
        請嚴格依照以下格式輸出（每一題之間用 "===題組分隔線===" 分隔）：
        
        [題目]
        (第1題內容)
        [答案]
        (第1題答案)
        [解析]
        (第1題過程)
        [繪圖程式碼]
        (第1題代碼，若無則留空)
        
        ===題組分隔線===
        
        [題目]
        (第2題內容...)
        ...
        """
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
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
                        return None, "API 額度已滿 (429)，請稍後再試。"
                else:
                    raise e

        if not response.candidates:
            return None, "AI 拒絕回答 (可能觸發安全機制)。"
            
        candidate = response.candidates[0]
        if candidate.finish_reason.name != "STOP":
             return None, f"生成被中斷 ({candidate.finish_reason.name})。"

        if not candidate.content or not candidate.content.parts:
             return None, "AI 回傳了空白內容。"

        return response.text, None
            
    except Exception as e:
        return None, f"AI 處理失敗: {str(e)}"

def parse_ai_response(text):
    """解析 AI 回傳格式 (支援多題解析)"""
    questions = []
    
    # 先用分隔線切開每一題
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
        except:
            continue
            
    if not questions and text:
        return [{"topic": "🤖 AI-仿題生成", "question": text, "answer": "解析失敗", "detail": "格式不符"}]
        
    return questions

def execute_drawing_code(code_str):
    """執行繪圖代碼"""
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
    sub_type = random.choice(['calc', 'sci', 'index'])
    if sub_type == 'calc':
        a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-10, 10)
        if c == 0: c = 1
        op1, op2 = random.choice(['+', '-']), random.choice(['*', '-'])
        q_str = f"計算： ${a} {op1} ({b}) {op2} ({c})$"
        ans_str = str(a + (b * c if op2 == '*' else b - c) if op1 == '+' else a - (b * c if op2 == '*' else b - c))
        detail = "先乘除後加減。"
    elif sub_type == 'sci':
        base = random.randint(1, 9); power = random.randint(-8, 8); num = base * (10**power)
        q_str = f"將 {num} 轉為科學記號。"
        ans_str = f"${base} \\times 10^{{{power}}}$"
        detail = "科學記號形式。"
    else:
        base = random.randint(2, 5); p1, p2 = random.randint(2, 5), random.randint(2, 5)
        q_str = f"化簡 $({base}^{{{p1}}})^{{{p2}}} \\div {base}^{{{p2}}}$"
        ans_str = f"${base}^{{{p1 * p2 - p2}}}$"
        detail = "指數律。"
    return {"topic": "基礎-數與量", "question": q_str, "answer": ans_str, "detail": detail}

def generate_linear_algebra_basic():
    x = random.randint(-10, 10); a = random.choice([-3, -2, 2, 3]); b = random.randint(-10, 10)
    c = a * x + b
    q_str = f"解 ${a}x + ({b}) = {c}$"
    ans_str = f"$x = {x}$"
    return {"topic": "基礎-代數", "question": q_str, "answer": ans_str, "detail": "移項求解。"}

def generate_geometry_basic():
    a1 = random.randrange(30, 80, 5); a2 = random.randrange(30, 80, 5)
    q_str = f"三角形兩內角為 {a1}°, {a2}°，求第三角。"
    ans_str = f"{180-a1-a2}°"
    return {"topic": "基礎-幾何", "question": q_str, "answer": ans_str, "detail": "內角和180。"}

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

def create_pdf(exam_data, custom_title, mode="student", uploaded_images=None):
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

    if uploaded_images:
        pdf.add_page()
        if font_ready: pdf.set_font("TaipeiSans", '', 16)
        pdf.cell(0, 10, "--- 原始試題區 ---", ln=True, align='C')
        for img_file in uploaded_images:
            try:
                img_file.seek(0)
                file_ext = img_file.name.split('.')[-1].lower()
                if file_ext not in ['jpg', 'jpeg', 'png']: file_ext = 'png'
                unique_name = f"{uuid.uuid4()}.{file_ext}"
                tmp_path = os.path.join(tempfile.gettempdir(), unique_name)
                with open(tmp_path, "wb") as tmp: tmp.write(img_file.read())
                pdf.add_page()
                pdf.image(tmp_path, x=10, y=10, w=190)
            except: pass
            finally:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    try: os.remove(tmp_path)
                    except: pass

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# Part 6: Streamlit UI
# ==========================================

def main():
    st.title("🤖 全方位國中數學出題系統 (AI 省流版)")
    
    if "exam_data" not in st.session_state: st.session_state["exam_data"] = []
    if "ai_generated_questions" not in st.session_state: st.session_state["ai_generated_questions"] = []

    with st.sidebar:
        st.header("⚙️ 設定")
        
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ 已載入系統 API Key")
        else:
            api_key = st.text_input("Google API Key", type="password")
        
        # 自動偵測模型
        model_options = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        selected_model = model_options[0]
        
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
                    selected_model = st.selectbox("AI 模型", model_options, index=default_idx)
                else:
                    selected_model = st.selectbox("AI 模型 (預設)", model_options)
            except:
                selected_model = st.selectbox("AI 模型 (離線)", model_options)
        
        custom_title = st.text_input("試卷標題", value="會考衝刺練習")
        uploaded_files = st.file_uploader("上傳考題", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        st.divider()
        
        # [New] AI 批次生成設定 (增加上限至10)
        st.subheader("💡 AI 變題設定")
        ai_variations = st.slider("每張圖要變出幾道新題? (單次請求生成多題)", 1, 10, 1, help="設定每張上傳的圖片，AI 要模仿出幾道類似題。一次生成多題可節省 API 額度並加快速度。")
        
        st.divider()
        st.subheader("🎲 隨機題目")
        all_topics = list(TOPIC_MAPPING.keys())
        selected_topics = st.multiselect("隨機單元", options=all_topics)
        num_questions = st.slider("隨機題數", 0, 20, 5)
        
        generate_btn = st.button("🚀 建立考卷", type="primary")

    if generate_btn:
        st.session_state["exam_data"] = []
        st.session_state["ai_generated_questions"] = []
        
        if selected_topics:
            with st.spinner("生成基礎題..."):
                st.session_state["exam_data"] = generate_exam_data(selected_topics, num_questions)
        
        if uploaded_files:
            if not api_key:
                st.warning("⚠️ 未輸入 API Key，僅顯示原始圖片。")
            elif not HAS_GENAI:
                st.error("❌ 系統缺少 AI 套件。")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, img_file in enumerate(uploaded_files):
                    status_text.text(f"🤖 AI 分析第 {idx+1}/{len(uploaded_files)} 題 (生成 {ai_variations} 變題)...")
                    
                    if idx > 0:
                        for s in range(15, 0, -1):
                            status_text.text(f"⏳ 額度保護冷卻中... {s} 秒")
                            time.sleep(1)
                    
                    ai_text, error = get_ai_variation(img_file, api_key, selected_model, num_variations=ai_variations)
                    
                    if error:
                        st.warning(f"第 {idx+1} 張圖片分析略過: {error}")
                    else:
                        new_qs = parse_ai_response(ai_text)
                        for q in new_qs:
                            q["source_img_idx"] = idx 
                            st.session_state["ai_generated_questions"].append(q)
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.text("✅ 完成！")
                progress_bar.empty()
        
        st.success("完成！")

    has_content = st.session_state["exam_data"] or st.session_state["ai_generated_questions"] or uploaded_files
    
    if has_content:
        st.markdown(f"## 🏫 {custom_title}")
        col1, col2 = st.columns([2, 1])
        with col1: show_answers = st.checkbox("🔍 顯示解答", value=False)
        with col2:
            final_data = st.session_state["exam_data"] + st.session_state["ai_generated_questions"]
            if st.button("📥 下載 PDF"):
                pdf_bytes = create_pdf(final_data, custom_title, mode="parent", uploaded_images=uploaded_files)
                st.download_button("點此下載", pdf_bytes, f"{custom_title}.pdf", "application/pdf")

        if st.session_state["exam_data"]:
            st.subheader("一、基礎題")
            for i, q in enumerate(st.session_state["exam_data"]):
                st.markdown(f"**Q{i+1}. [{q['topic']}]**")
                st.markdown(q['question'])
                if show_answers: st.success(q['answer']); st.caption(q['detail'])
                st.write("---")

        if st.session_state["ai_generated_questions"]:
            st.subheader("二、AI 仿題")
            for i, q in enumerate(st.session_state["ai_generated_questions"]):
                st.markdown(f"**AI-Q{i+1}.**")
                col_q, col_img = st.columns([2, 1])
                with col_q:
                    st.info(q['question'])
                    if 'code' in q and q['code']:
                        img_buf = execute_drawing_code(q['code'])
                        if img_buf: st.image(img_buf, width=400)
                    if show_answers: st.success(q['answer']); st.markdown(q['detail'])
                with col_img:
                    if "source_img_idx" in q and uploaded_files:
                        st.image(uploaded_files[q["source_img_idx"]], caption="原題")
                st.write("---")
        
        elif uploaded_files and not st.session_state["ai_generated_questions"]:
            st.subheader("三、原始圖")
            for img in uploaded_files: st.image(img)

if __name__ == "__main__":
    main()
