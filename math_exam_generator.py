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

# 1. 設定頁面配置
st.set_page_config(page_title="全方位數學自動出題系統", layout="wide", page_icon="📝")

# 嘗試載入中文字型給 Matplotlib 使用 (用於繪製圖表中的中文)
# 預設尋找根目錄下的台北黑體，若無則回退到預設字體
font_path = 'TaipeiSansTCBeta-Regular.ttf'
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
else:
    # 若無字型檔，避免繪圖亂碼，可設定英文 fallback 或忽略
    pass

# ==========================================
# Part 1: 基礎題目生成邏輯
# ==========================================

def generate_number_basic():
    """數與量基礎：四則運算、科學記號、指數律"""
    sub_type = random.choice(['calc', 'sci', 'index'])
    if sub_type == 'calc':
        a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-10, 10)
        if c == 0: c = 1
        op1, op2 = random.choice(['+', '-']), random.choice(['*', '-'])
        q_str = f"計算： ${a} {op1} ({b}) {op2} ({c})$"
        val_b, val_c = b, c
        res = val_b * val_c if op2 == '*' else val_b - val_c
        final = a + res if op1 == '+' else a - res
        ans_str = f"{final}"
        detail = "先乘除後加減，注意正負號變化。"
    elif sub_type == 'sci':
        base = random.randint(1, 9)
        power = random.randint(-8, 8)
        num = base * (10**power)
        if power >= 0: q_str = f"將整數 {num} 以科學記號表示。"
        else: q_str = f"將小數 {num:.8f}".rstrip('0') + " 以科學記號表示。"
        ans_str = f"${base} \\times 10^{{{power}}}$"
        detail = "科學記號形式為 $a \\times 10^n$，其中 $1 \\le a < 10$。"
    else:
        base = random.randint(2, 5)
        p1, p2 = random.randint(2, 5), random.randint(2, 5)
        q_str = f"化簡： $({base}^{{{p1}}})^{{{p2}}} \\div {base}^{{{p2}}}$"
        final_p = p1 * p2 - p2
        ans_str = f"${base}^{{{final_p}}}$"
        detail = "利用指數律：$(a^m)^n = a^{mn}$ 以及 $a^m \\div a^n = a^{m-n}$。"
    return {"topic": "基礎-數與量", "question": q_str, "answer": ans_str, "detail": detail}

def generate_linear_algebra_basic():
    """一元一次方程式與不等式 (基礎)"""
    x = random.randint(-15, 15)
    a = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    b = random.randint(-20, 20)
    q_type = random.choice(['eq', 'ineq'])
    if q_type == 'eq':
        c = a * x + b
        b_sign = "+" if b >= 0 else "-"
        q_str = f"解方程式： ${a}x {b_sign} {abs(b)} = {c}$"
        ans_str = f"$x = {x}$"
        detail = f"移項：${a}x = {c} - ({b}) = {c-b}$，故 $x = {x}$。"
    else:
        delta = random.randint(1, 10)
        c = a * x + b - delta 
        if a > 0:
            q_str = f"解不等式： ${a}x + {b} > {c}$"
            boundary = (c - b) / a
            ans_str = f"$x > {boundary:.1f}$"
            detail = "移項整理，注意若同除以負數，不等號方向要改變。"
        else:
            q_str = f"解不等式： ${a}x + {b} < {c}$"
            boundary = (c - b) / a
            ans_str = f"$x > {boundary:.1f}$"
            detail = "係數為負數，移項除法時不等號方向改變 ($< \\rightarrow >$)。"
    return {"topic": "基礎-代數運算", "question": q_str, "answer": ans_str, "detail": detail}

def generate_geometry_basic():
    """幾何基礎 (勾股、內角)"""
    g_type = random.choice(['pythagoras', 'angle'])
    if g_type == 'pythagoras':
        triples = [(3,4,5), (5,12,13), (6,8,10), (8,15,17)]
        a, b, c = random.choice(triples)
        q_str = f"直角三角形兩股長分別為 {a}, {b}，求斜邊長。"
        ans_str = f"{c}"
        detail = "畢氏定理：斜邊平方 = 兩股平方和 ($c^2 = a^2 + b^2$)。"
    else:
        a1, a2 = random.randrange(30, 80, 5), random.randrange(30, 80, 5)
        q_str = f"三角形兩內角為 {a1}° 與 {a2}°，求第三個內角。"
        ans_str = f"{180 - a1 - a2}°"
        detail = "三角形內角和為 180 度。"
    return {"topic": "基礎-幾何圖形", "question": q_str, "answer": ans_str, "detail": detail}

# ==========================================
# Part 2: 資料解讀、表格與【動態繪圖題】 (Visual Questions)
# ==========================================

def generate_visual_parking():
    """🎨 動態繪圖題：停車位總長度 (參考上傳圖片 05)"""
    # 1. 隨機生成題目變數
    n_cars = random.randint(10, 30) # 車位數量
    w_space = random.choice([200, 220, 250]) # 車位寬度
    w_gap = random.choice([100, 120, 150]) # 下車區寬度
    
    # 邏輯：N個車位，相鄰共用下車區 => 頭尾各一個車位，中間有 N-1 個下車區
    # 依據常見題意：車位-Gap-車位-Gap...-車位。 Gap數 = N-1
    total_width = n_cars * w_space + (n_cars - 1) * w_gap
    
    q_str = f"某園區規劃 {n_cars} 個無障礙停車位（如下圖），每個停車位寬 {w_space} 公分，" \
            f"相鄰兩個車位中間設有寬 {w_gap} 公分的共用下車區。\n" \
            f"請問圖中所有停車位及下車區的總寬度是多少公分？"
    ans_str = f"{total_width} 公分"
    detail = f"總寬 = (車位數 $\\times$ 車位寬) + ((車位數-1) $\\times$ 下車區寬)\n" \
             f"= ${n_cars} \\times {w_space} + ({n_cars}-1) \\times {w_gap} = {n_cars*w_space} + { (n_cars-1)*w_gap } = {total_width}$"

    # 2. 使用 Matplotlib 動態繪圖
    # 建立畫布
    fig, ax = plt.subplots(figsize=(8, 2.5))
    
    # 繪製示意圖 (畫出前兩個和最後一個，中間用省略號)
    # 顏色與樣式
    color_car = '#b3d9ff' # 淺藍
    color_gap = '#e6e6e6' # 淺灰
    
    # Block 1: 第一個車位
    rect1 = patches.Rectangle((0, 0), w_space, 100, facecolor=color_car, edgecolor='black')
    ax.add_patch(rect1)
    ax.text(w_space/2, 50, f"車位\n{w_space}", ha='center', va='center', fontsize=10, fontproperties=font_prop if os.path.exists(font_path) else None)
    
    # Gap 1: 第一個下車區
    current_x = w_space
    rect_g1 = patches.Rectangle((current_x, 0), w_gap, 100, facecolor=color_gap, hatch='//', edgecolor='black')
    ax.add_patch(rect_g1)
    ax.text(current_x + w_gap/2, 50, f"下車\n{w_gap}", ha='center', va='center', fontsize=9, fontproperties=font_prop if os.path.exists(font_path) else None)
    
    # Block 2: 第二個車位
    current_x += w_gap
    rect2 = patches.Rectangle((current_x, 0), w_space, 100, facecolor=color_car, edgecolor='black')
    ax.add_patch(rect2)
    ax.text(current_x + w_space/2, 50, "車位", ha='center', va='center', fontsize=10, fontproperties=font_prop if os.path.exists(font_path) else None)
    
    # 省略號
    current_x += w_space
    ax.text(current_x + 50, 50, "......", ha='center', va='center', fontsize=20)
    
    # Block N: 最後一個車位 (畫在遠一點的地方示意)
    final_x = current_x + 100
    rect_n = patches.Rectangle((final_x, 0), w_space, 100, facecolor=color_car, edgecolor='black')
    ax.add_patch(rect_n)
    ax.text(final_x + w_space/2, 50, f"車位\n{n_cars}", ha='center', va='center', fontsize=10, fontproperties=font_prop if os.path.exists(font_path) else None)
    
    # 設定圖表範圍與隱藏座標軸
    ax.set_xlim(-50, final_x + w_space + 50)
    ax.set_ylim(-20, 120)
    ax.axis('off')
    
    # 將圖片存入記憶體 (BytesIO)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    buf.seek(0)
    
    return {
        "topic": "🎨 素養-圖形計算(停車位)",
        "question": q_str,
        "answer": ans_str,
        "detail": detail,
        "image_data": buf # 關鍵：將圖片物件傳回
    }

def generate_table_poll_adjustment():
    """表格題：民調調整倍率"""
    pop_18 = random.choice([20, 30, 40])
    pop_40 = random.choice([30, 40])
    pop_60 = 100 - pop_18 - pop_40
    sur_18 = random.choice([10, 20])
    sur_40 = random.choice([30, 40, 50])
    sur_60 = 100 - sur_18 - sur_40
    target_group = random.choice(["18~39歲", "40~59歲", "60歲以上"])
    if target_group == "18~39歲": pop, sur = pop_18, sur_18
    elif target_group == "40~59歲": pop, sur = pop_40, sur_40
    else: pop, sur = pop_60, sur_60
    rate = pop / sur
    table_md = f"""
| 組別 | 人口占比 | 調查占比 | 調整倍率 |
| :---: | :---: | :---: | :---: |
| 18~39歲組 | {pop_18}% | {sur_18}% | ? |
| 40~59歲組 | {pop_40}% | {sur_40}% | ... |
| 60歲以上組 | {pop_60}% | {sur_60}% | ... |
| **總計** | **100%** | **100%** | |
    """
    q_str = (f"某民調公司依年齡分3組，利用「調整倍率」修正結果。公式：**調整倍率 = 人口占比 / 調查占比**。\n"
             f"請參考下表，計算 **{target_group}組** 的調整倍率？\n{table_md}")
    ans_str = f"{rate:.1f} (或 {pop}/{sur})"
    detail = f"{target_group}人口 {pop}%，調查 {sur}%。調整倍率 = {pop}% ÷ {sur}% = {rate}。"
    return {"topic": "📊 資料解讀-民調倍率", "question": q_str, "answer": ans_str, "detail": detail}

def generate_table_bicycle_gear():
    """表格題：腳踏車齒輪比"""
    front_gears = sorted(random.sample([20, 22, 30, 32, 40, 44], 3))
    rear_gears = sorted(random.sample([12, 14, 16, 18, 20, 24, 28], 5))
    front_str = "、".join(map(str, front_gears))
    rear_str = "、".join(map(str, rear_gears))
    table_md = f"""
| 位置 | 齒數規格 |
| :--- | :--- |
| **前齒輪** | {front_str} 齒 |
| **後齒輪** | {rear_str} 齒 |
    """
    f1, r1 = random.choice(front_gears), random.choice(rear_gears)
    ratio1 = f1 / r1
    mode = random.choice(["更費力", "更省力"])
    q_str = (f"變速自行車齒輪規格如下。已知 **齒輪比 = 前齒輪 / 後齒輪**，比值越大越費力。\n"
             f"{table_md}\n若原組合為「前 {f1} / 後 {r1}」，想切換成 **{mode}** 的組合，下列何者正確？")
    valid_answers = []
    for f in front_gears:
        for r in rear_gears:
            if f == f1 and r == r1: continue
            r_new = f / r
            if (mode == "更費力" and r_new > ratio1) or (mode == "更省力" and r_new < ratio1):
                valid_answers.append(f"前 {f} / 後 {r}")
    
    if not valid_answers:
        q_str = f"請計算前 {f1} 後 {r1} 之齒輪比。\n{table_md}"
        ans_str = f"{ratio1:.2f}"
        detail = f"{f1}/{r1} = {ratio1:.2f}"
    else:
        correct_ans = random.choice(valid_answers)
        ans_str = f"例如：{correct_ans}"
        detail = f"原比值 {ratio1:.2f}。需找{'大於' if mode=='更費力' else '小於'}此值的組合。"
    return {"topic": "🚲 資料解讀-齒輪比", "question": q_str, "answer": ans_str, "detail": detail}

# ==========================================
# Part 3: 歷屆試題還原 (Real Exam Restored)
# ==========================================

def generate_real_exam_exponents():
    base = random.choice([2, 3, 5, 7, 10]); n1 = random.randint(5, 15); n2 = random.randint(2, 5); n3 = random.randint(3, 8)
    q_str = f"算式 ${base}^{{{n1}}} \\times {base}^{{{n2}}} \\div {base}^{{{n3}}}$ 之值？"
    ans_str = f"${base}^{{{n1+n2-n3}}}$"
    return {"topic": "🔥 歷屆-指數律", "question": q_str, "answer": ans_str, "detail": "指數相乘相加，相除相減。"}

def generate_real_exam_polynomial():
    a = random.randint(2, 9); b = random.randint(-9, -1); c = random.randint(1, 9); d = random.randint(-9, -1)
    q_str = f"計算 $({a}x^2 + ({b}x)) - ({c} + ({d}x))$ 的結果？"
    ans_str = f"${a}x^2 {'+' if b-d>=0 else '-'} {abs(b-d)}x {'+' if -c>=0 else '-'} {abs(c)}$"
    return {"topic": "🔥 歷屆-多項式", "question": q_str, "answer": ans_str, "detail": "去括號合併同類項。"}

def generate_real_exam_system_val():
    x = random.randint(-5, 5); y = random.randint(-5, 5)
    a1 = random.randint(10, 40); b1 = random.randint(2, 9); c1 = a1 * x + b1 * y
    a2 = random.randint(10, 40); b2 = -b1; c2 = a2 * x + b2 * y
    target = random.randint(1, 3)*x + random.randint(1, 3)*y
    q_str = f"若聯立方程 $\\begin{{cases}} {a1}x + {b1}y = {c1} \\\\ {a2}x {b2}y = {c2} \\end{{cases}}$ 解為 $x=a, y=b$，求特定代數式值。" # 簡化顯示
    ans_str = f"{target} (範例)"
    return {"topic": "🔥 歷屆-聯立方程式", "question": q_str, "answer": ans_str, "detail": f"x={x}, y={y}"}

# ==========================================
# Part 4: 題型策略地圖
# ==========================================

TOPIC_MAPPING = {
    # 繪圖題 (New!)
    "🎨 素養 - 停車位問題 (動態繪圖)": generate_visual_parking,
    # 資料解讀
    "📊 素養 - 民調調整倍率 (表格)": generate_table_poll_adjustment,
    "🚲 素養 - 腳踏車齒輪比 (表格)": generate_table_bicycle_gear,
    # 基礎與歷屆
    "基礎 - 數與量": generate_number_basic,
    "基礎 - 代數": generate_linear_algebra_basic,
    "基礎 - 幾何": generate_geometry_basic,
    "🔥 歷屆 - 指數律": generate_real_exam_exponents,
    "🔥 歷屆 - 多項式": generate_real_exam_polynomial,
    "🔥 歷屆 - 聯立方程式": generate_real_exam_system_val,
}

def generate_exam_data(selected_topics, num_questions):
    if not selected_topics: return []
    exam_list = []
    for i in range(num_questions):
        topic_name = selected_topics[i % len(selected_topics)]
        generator_func = TOPIC_MAPPING[topic_name]
        exam_list.append(generator_func())
    random.shuffle(exam_list)
    return exam_list

# ==========================================
# Part 5: PDF 匯出功能
# ==========================================

class PDFExport(FPDF):
    def footer(self):
        self.set_y(-15)
        try:
            self.set_font("TaipeiSans", '', 10)
        except:
            self.set_font("Arial", 'I', 8)
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
    
    # 1. 隨機題目
    if exam_data:
        for idx, item in enumerate(exam_data):
            # 題目文字
            clean_q = item['question'].replace('$', '').replace('\\times', 'x').replace('\\div', '/')
            if "|" in clean_q: clean_q = clean_q.split("|")[0] + "\n[表格請見線上版]"
            
            topic_show = item['topic'].split('-')[-1] if '-' in item['topic'] else item['topic']
            pdf.multi_cell(0, 10, f"Q{idx+1}. [{topic_show}] {clean_q}")
            
            # [New] 插入動態生成的圖片 (如果有)
            if 'image_data' in item:
                try:
                    # 將 BytesIO 存為暫存檔供 fpdf 使用
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                        tmp_img.write(item['image_data'].getvalue())
                        tmp_img_path = tmp_img.name
                    
                    pdf.image(tmp_img_path, w=150) # 插入圖片
                    os.remove(tmp_img_path) # 清理
                except Exception as e:
                    pdf.cell(0, 10, f"[Image Error: {e}]", ln=True)

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

    # 2. 上傳圖片
    if uploaded_images:
        pdf.add_page()
        if font_ready: pdf.set_font("TaipeiSans", '', 16)
        pdf.cell(0, 10, "--- 圖片試題區 ---", ln=True, align='C')
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
    st.title("📝 全方位國中數學出題系統 (Ultimate)")
    st.markdown("### 支援：基礎、歷屆、**📊 表格題** 與 **🎨 動態繪圖題**")
    
    # 字型檢查提示
    if not os.path.exists(font_path):
        st.warning("⚠️ 未偵測到 'TaipeiSansTCBeta-Regular.ttf'，繪圖題中的中文可能無法顯示。")

    all_topics = list(TOPIC_MAPPING.keys())
    if "selected_topics" not in st.session_state:
        st.session_state.selected_topics = [t for t in all_topics if "素養" in t]

    with st.sidebar:
        st.header("⚙️ 試卷設定")
        custom_title = st.text_input("試卷標題", value="會考衝刺練習")
        uploaded_files = st.file_uploader("上傳圖片考題", type=['png', 'jpg'], accept_multiple_files=True)
        selected_topics = st.multiselect("選擇單元", options=all_topics, key="selected_topics")
        num_questions = st.slider("題目數量", 5, 50, 10)
        generate_btn = st.button("🚀 建立新考卷", type="primary")

    if "exam_data" not in st.session_state:
        st.session_state["exam_data"] = []
    
    if generate_btn:
        if not selected_topics and not uploaded_files:
            st.error("請至少選擇一個單元或上傳圖片！")
        else:
            with st.spinner("正在繪製圖形與生成題目..."):
                if selected_topics:
                    st.session_state["exam_data"] = generate_exam_data(selected_topics, num_questions)
                else:
                    st.session_state["exam_data"] = []
            st.success("生成完畢！")

    if st.session_state["exam_data"] or uploaded_files:
        st.markdown(f"## 🏫 {custom_title}")
        col1, col2 = st.columns([2, 1])
        with col1: show_answers = st.checkbox("🔍 顯示解答 (教師模式)", value=False)
        with col2:
            if st.button("📥 下載 PDF"):
                pdf_bytes = create_pdf(st.session_state["exam_data"], custom_title, mode="parent", uploaded_images=uploaded_files)
                st.download_button("點此下載", pdf_bytes, f"{custom_title}.pdf", "application/pdf")

        st.divider()

        if st.session_state["exam_data"]:
            st.subheader("一、隨機生成試題")
            for i, q in enumerate(st.session_state["exam_data"]):
                t_name = q['topic'].split('-')[-1] if '-' in q['topic'] else q['topic']
                st.markdown(f"**Q{i+1}. [{t_name}]**")
                st.markdown(q['question'])
                
                # [New] 顯示動態生成的圖片
                if 'image_data' in q:
                    st.image(q['image_data'], caption="示意圖 (由程式動態繪製)", use_container_width=False, width=600)
                
                if show_answers:
                    with st.expander("解答", expanded=True):
                        st.success(q['answer'])
                        st.caption(q['detail'])
                st.write("---")

        if uploaded_files:
            st.subheader("二、上傳圖片試題")
            for img in uploaded_files:
                st.image(img, use_container_width=True)
                st.write("---")

if __name__ == "__main__":
    main()
