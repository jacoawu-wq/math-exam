import streamlit as st
import random
import math
from fpdf import FPDF
import os
import tempfile
import uuid
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import io
import google.generativeai as genai
from PIL import Image

# 1. 設定頁面配置
st.set_page_config(page_title="全方位數學自動出題系統 (AI繪圖版)", layout="wide", page_icon="🎨")

# 字型設定
font_path = 'TaipeiSansTCBeta-Regular.ttf'
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    # 設定 Matplotlib 全域字型，讓 AI 畫圖時能自動吃到中文
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

# ==========================================
# Part 0: AI 核心邏輯 (Gemini Integration)
# ==========================================

def get_ai_variation(image_file, api_key, model_name):
    """
    使用 Google Gemini Vision 模型分析圖片並生成變體 (含繪圖代碼)
    """
    if not api_key:
        return None, "請先輸入 Google API Key"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        image_file.seek(0)
        img = Image.open(image_file)
        
        # [關鍵更新] Prompt 指令：要求 AI 生成 Python 繪圖代碼
        prompt = """
        你是一位專業的國中數學老師。請分析這張圖片中的數學題目：
        1. 找出核心觀念（如：相似三角形、圓周角、二次函數...）。
        2. 「重新設計」一道新題目，邏輯相同但數字改變。
        3. 【重要】如果題目涉及幾何圖形（三角形、圓、函數圖形等），請撰寫一段 Python matplotlib 程式碼來繪製該圖。
           - 程式碼不需要 `plt.show()`。
           - 必須將圖表物件存入變數 `fig` (例如 `fig, ax = plt.subplots()`)。
           - 若有文字標註，請直接使用中文，系統已設定好字體。
           - 圖形要簡單清晰，標示出新題目中的數據（邊長、角度）。
        
        請嚴格依照以下格式輸出（不要輸出 markdown ```python 標記，只要純文字內容）：
        
        [題目]
        (新題目內容)
        
        [答案]
        (答案)
        
        [解析]
        (計算過程)
        
        [繪圖程式碼]
        (若無圖則留空，若有圖請直接寫code，不要加 ```)
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        fig, ax = plt.subplots()
        ...
        """
        
        response = model.generate_content([prompt, img])
        return response.text, None
            
    except Exception as e:
        return None, f"AI 連線錯誤: {str(e)}"

def parse_ai_response(text):
    """解析 AI 回傳的格式，包含程式碼"""
    result = {
        "topic": "🤖 AI-仿題生成",
        "question": "",
        "answer": "",
        "detail": "",
        "code": None
    }
    
    try:
        # 分割區塊
        if '[題目]' in text:
            parts = text.split('[答案]')
            result["question"] = parts[0].replace('[題目]', '').strip()
            
            remain = parts[1]
            if '[解析]' in remain:
                parts2 = remain.split('[解析]')
                result["answer"] = parts2[0].strip()
                
                remain2 = parts2[1]
                if '[繪圖程式碼]' in remain2:
                    parts3 = remain2.split('[繪圖程式碼]')
                    result["detail"] = parts3[0].strip()
                    code_str = parts3[1].strip()
                    # 清理可能殘留的 markdown 標記
                    code_str = code_str.replace('```python', '').replace('```', '')
                    if len(code_str) > 10: # 簡單檢查是否有內容
                        result["code"] = code_str
                else:
                    result["detail"] = remain2.strip()
    except:
        result["question"] = text
        result["answer"] = "解析失敗"
        result["detail"] = "格式不符，請參考原文。"
        
    return result

def execute_drawing_code(code_str):
    """執行 AI 產生的繪圖代碼並回傳圖片 Bytes"""
    if not code_str: return None
    
    try:
        # 建立一個安全的執行環境字典
        local_scope = {}
        # 執行 AI 的代碼
        exec(code_str, globals(), local_scope)
        
        # 檢查是否有產出 fig
        if 'fig' in local_scope:
            fig = local_scope['fig']
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            buf.seek(0)
            return buf
    except Exception as e:
        print(f"Drawing Error: {e}")
        return None
    return None

# ==========================================
# Part 1: 基礎題目生成邏輯 (保留)
# ==========================================

def generate_number_basic():
    sub_type = random.choice(['calc', 'sci', 'index'])
    if sub_type == 'calc':
        a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-10, 10)
        if c == 0: c = 1
        op1, op2 = random.choice(['+', '-']), random.choice(['*', '-'])
        q_str = f"計算： ${a} {op1} ({b}) {op2} ({c})$"
        ans_str = str(a + (b * c if op2 == '*' else b - c) if op1 == '+' else a - (b * c if op2 == '*' else b - c))
        detail = "先乘除後加減，注意正負號變化。"
    elif sub_type == 'sci':
        base = random.randint(1, 9); power = random.randint(-8, 8)
        num = base * (10**power)
        q_str = f"將整數 {num} 以科學記號表示。" if power >=0 else f"將小數 {num:.8f}".rstrip('0') + " 以科學記號表示。"
        ans_str = f"${base} \\times 10^{{{power}}}$"
        detail = "科學記號形式為 $a \\times 10^n$。"
    else:
        base = random.randint(2, 5); p1, p2 = random.randint(2, 5), random.randint(2, 5)
        q_str = f"化簡： $({base}^{{{p1}}})^{{{p2}}} \\div {base}^{{{p2}}}$"
        ans_str = f"${base}^{{{p1 * p2 - p2}}}$"
        detail = "利用指數律運算。"
    return {"topic": "基礎-數與量", "question": q_str, "answer": ans_str, "detail": detail}

def generate_linear_algebra_basic():
    x = random.randint(-15, 15); a = random.choice([-5, -4, -3, -2, 2, 3, 4, 5]); b = random.randint(-20, 20)
    c = a * x + b
    b_sign = "+" if b >= 0 else "-"
    q_str = f"解方程式： ${a}x {b_sign} {abs(b)} = {c}$"
    ans_str = f"$x = {x}$"
    detail = f"移項法則：${a}x = {c} - ({b})$。"
    return {"topic": "基礎-代數運算", "question": q_str, "answer": ans_str, "detail": detail}

def generate_geometry_basic():
    a1, a2 = random.randrange(30, 80, 5), random.randrange(30, 80, 5)
    q_str = f"三角形兩內角為 {a1}° 與 {a2}°，求第三個內角。"
    ans_str = f"{180 - a1 - a2}°"
    detail = "三角形內角和為 180 度。"
    return {"topic": "基礎-幾何圖形", "question": q_str, "answer": ans_str, "detail": detail}

# ==========================================
# Part 2: 動態繪圖題 (保留)
# ==========================================

def generate_visual_parking():
    n_cars = random.randint(10, 30); w_space = random.choice([200, 220, 250]); w_gap = random.choice([100, 120, 150])
    total_width = n_cars * w_space + (n_cars - 1) * w_gap
    q_str = f"某園區規劃 {n_cars} 個無障礙停車位（如下圖），車位寬 {w_space} cm，間隔 {w_gap} cm。求總寬度？"
    ans_str = f"{total_width} cm"
    detail = f"總寬 = {n_cars}x{w_space} + ({n_cars}-1)x{w_gap} = {total_width}"

    fig, ax = plt.subplots(figsize=(8, 2.5))
    color_car, color_gap = '#b3d9ff', '#e6e6e6'
    
    rect1 = patches.Rectangle((0, 0), w_space, 100, facecolor=color_car, edgecolor='black')
    ax.add_patch(rect1)
    ax.text(w_space/2, 50, f"車位\n{w_space}", ha='center', va='center', fontsize=10, fontproperties=font_prop if os.path.exists(font_path) else None)
    
    rect_g1 = patches.Rectangle((w_space, 0), w_gap, 100, facecolor=color_gap, hatch='//', edgecolor='black')
    ax.add_patch(rect_g1)
    
    rect2 = patches.Rectangle((w_space+w_gap, 0), w_space, 100, facecolor=color_car, edgecolor='black')
    ax.add_patch(rect2)
    
    ax.text(w_space+w_gap+w_space+50, 50, "......", ha='center', va='center', fontsize=20)
    
    final_x = w_space+w_gap+w_space+100
    rect_n = patches.Rectangle((final_x, 0), w_space, 100, facecolor=color_car, edgecolor='black')
    ax.add_patch(rect_n)
    ax.text(final_x + w_space/2, 50, f"車位\n{n_cars}", ha='center', va='center', fontsize=10, fontproperties=font_prop if os.path.exists(font_path) else None)
    
    ax.set_xlim(-50, final_x + w_space + 50)
    ax.set_ylim(-20, 120)
    ax.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    buf.seek(0)
    
    return {"topic": "🎨 素養-圖形計算", "question": q_str, "answer": ans_str, "detail": detail, "image_data": buf}

TOPIC_MAPPING = {
    "基礎 - 數與量": generate_number_basic,
    "基礎 - 代數": generate_linear_algebra_basic,
    "基礎 - 幾何": generate_geometry_basic,
    "🎨 素養 - 停車位問題": generate_visual_parking,
}

def generate_exam_data(selected_topics, num_questions):
    if not selected_topics: return []
    exam_list = []
    for i in range(num_questions):
        topic_name = selected_topics[i % len(selected_topics)]
        if topic_name in TOPIC_MAPPING:
            exam_list.append(TOPIC_MAPPING[topic_name]())
    random.shuffle(exam_list)
    return exam_list

# ==========================================
# Part 5: PDF 匯出功能
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

    full_title = f"{custom_title} ({'學生' if mode=='student' else '解答'}卷)"
    pdf.cell(0, 10, full_title, ln=True, align='C')
    pdf.ln(10)
    
    # 1. 題目區
    for idx, item in enumerate(exam_data):
        q_text = item['question'].replace('$', '').replace('\\times', 'x').replace('\\div', '/')
        t_name = item['topic'].split('-')[-1] if '-' in item['topic'] else item['topic']
        pdf.multi_cell(0, 10, f"Q{idx+1}. [{t_name}] {q_text}")
        
        # 處理圖片 (包含 AI 動態生成的與 Python 內建生成的)
        img_buf = None
        if 'image_data' in item: # 內建 Python 題的圖
            img_buf = item['image_data']
        elif 'code' in item and item['code']: # AI 現場畫的圖
            img_buf = execute_drawing_code(item['code'])
            
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

    # 2. 圖片試題區 (原始上傳圖)
    if uploaded_images:
        pdf.add_page()
        if font_ready: pdf.set_font("TaipeiSans", '', 16)
        pdf.cell(0, 10, "--- 附錄：原始圖片試題 ---", ln=True, align='C')
        
        for img_file in uploaded_images:
            try:
                img_file.seek(0)
                file_ext = img_file.name.split('.')[-1].lower()
                if file_ext not in ['jpg', 'jpeg', 'png']: file_ext = 'png'
                unique_name = f"{uuid.uuid4()}.{file_ext}"
                tmp_path = os.path.join(tempfile.gettempdir(), unique_name)
                
                with open(tmp_path, "wb") as tmp:
                    tmp.write(img_file.read())
                
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
    st.title("🤖 全方位國中數學出題系統 (AI 繪圖旗艦版)")
    st.markdown("### 支援：基礎生成、圖片上傳、**Gemini AI 自動仿題與畫圖**")
    
    if "exam_data" not in st.session_state:
        st.session_state["exam_data"] = []
    if "ai_generated_questions" not in st.session_state:
        st.session_state["ai_generated_questions"] = []

    with st.sidebar:
        st.header("⚙️ 設定")
        
        # API Key
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ 已載入系統 API Key")
        else:
            api_key = st.text_input("Google API Key", type="password")
        
        # 自動偵測模型
        model_options = ["models/gemini-1.5-flash"] 
        selected_model = model_options[0]
        
        if api_key:
            try:
                genai.configure(api_key=api_key)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if available_models:
                    model_options = available_models
                    default_idx = 0
                    for i, m in enumerate(model_options):
                        if "flash" in m: default_idx = i; break
                    selected_model = st.selectbox("選擇 AI 模型", model_options, index=default_idx)
                else:
                    selected_model = st.selectbox("選擇 AI 模型 (預設)", model_options)
            except Exception:
                selected_model = st.selectbox("選擇 AI 模型 (連線失敗)", model_options)
        
        custom_title = st.text_input("試卷標題", value="會考衝刺練習")
        
        st.subheader("1. 上傳考題圖片")
        uploaded_files = st.file_uploader("支援 JPG/PNG (AI 將自動分析)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        st.divider()
        
        st.subheader("2. 補充隨機題 (選填)")
        all_topics = list(TOPIC_MAPPING.keys())
        selected_topics = st.multiselect("選擇單元", options=all_topics)
        num_questions = st.slider("補充題數", 0, 20, 5)
        
        generate_btn = st.button("🚀 建立新考卷 (含 AI 變題)", type="primary")

    # ==========================================
    # 核心邏輯
    # ==========================================
    if generate_btn:
        st.session_state["exam_data"] = []
        st.session_state["ai_generated_questions"] = []
        
        if selected_topics:
            with st.spinner("正在生成基礎隨機題..."):
                st.session_state["exam_data"] = generate_exam_data(selected_topics, num_questions)
        
        if uploaded_files:
            if not api_key:
                st.warning("⚠️ 未輸入 API Key，僅顯示原始圖片。")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, img_file in enumerate(uploaded_files):
                    status_text.text(f"🤖 AI 正在繪製第 {idx+1}/{len(uploaded_files)} 題的圖形...")
                    
                    ai_text, error = get_ai_variation(img_file, api_key, selected_model)
                    
                    if error:
                        st.error(f"第 {idx+1} 張圖片分析失敗: {error}")
                    else:
                        new_q = parse_ai_response(ai_text)
                        new_q["source_img_idx"] = idx 
                        st.session_state["ai_generated_questions"].append(new_q)
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.text("✅ AI 變題與繪圖完成！")
                progress_bar.empty()
        
        st.success("考卷生成完畢！")

    # ==========================================
    # 顯示結果
    # ==========================================
    
    has_content = st.session_state["exam_data"] or st.session_state["ai_generated_questions"] or uploaded_files
    
    if has_content:
        st.markdown(f"## 🏫 {custom_title}")
        
        col1, col2 = st.columns([2, 1])
        with col1: show_answers = st.checkbox("🔍 顯示解答 (教師模式)", value=False)
        with col2:
            final_exam_data = st.session_state["exam_data"] + st.session_state["ai_generated_questions"]
            if st.button("📥 下載完整 PDF"):
                pdf_bytes = create_pdf(final_exam_data, custom_title, mode="parent", uploaded_images=uploaded_files)
                st.download_button("點此下載", pdf_bytes, f"{custom_title}.pdf", "application/pdf")

        st.divider()

        # 1. 基礎隨機題
        if st.session_state["exam_data"]:
            st.subheader("📌 第一部分：基礎練習")
            for i, q in enumerate(st.session_state["exam_data"]):
                t_name = q['topic'].split('-')[-1] if '-' in q['topic'] else q['topic']
                st.markdown(f"**Q{i+1}. [{t_name}]**")
                st.markdown(q['question'])
                if 'image_data' in q:
                    st.image(q['image_data'], caption="示意圖", width=400)
                
                if show_answers:
                    st.success(f"Ans: {q['answer']}")
                    st.caption(q['detail'])
                st.write("---")

        # 2. AI 變題生成區
        if st.session_state["ai_generated_questions"]:
            st.subheader("🤖 第二部分：AI 仿題與繪圖")
            
            for i, q in enumerate(st.session_state["ai_generated_questions"]):
                st.markdown(f"**AI-Q{i+1}. (改編自上傳考題)**")
                
                col_q, col_origin = st.columns([2, 1])
                
                with col_q:
                    st.info(q['question'])
                    
                    # [關鍵更新] 顯示 AI 產生的繪圖代碼結果
                    if 'code' in q and q['code']:
                        img_buf = execute_drawing_code(q['code'])
                        if img_buf:
                            st.image(img_buf, caption="AI 自動繪製示意圖", width=400)
                        else:
                            st.warning("⚠️ 圖片繪製失敗 (代碼錯誤)")
                    
                    if show_answers:
                        st.success(f"Ans: {q['answer']}")
                        st.markdown(f"**解析：**\n{q['detail']}")
                
                with col_origin:
                    if "source_img_idx" in q and uploaded_files and q["source_img_idx"] < len(uploaded_files):
                        st.image(uploaded_files[q["source_img_idx"]], caption="原始題目", use_container_width=True)
                
                st.write("---")
        
        elif uploaded_files and not st.session_state["ai_generated_questions"]:
            st.subheader("📷 原始考題圖片")
            for img in uploaded_files:
                st.image(img, use_container_width=True)
                st.write("---")

if __name__ == "__main__":
    main()
