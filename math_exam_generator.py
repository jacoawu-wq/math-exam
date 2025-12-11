import streamlit as st
import random
import math
from fpdf import FPDF
import os
import tempfile
import uuid

# 1. 設定頁面配置
st.set_page_config(page_title="全方位數學自動出題系統", layout="wide", page_icon="📝")

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
# Part 2: 資料解讀與表格題 (New! Table-Based Questions)
# ==========================================

def generate_table_poll_adjustment():
    """表格題：民調調整倍率 (參考上傳圖片 11)"""
    # 隨機產生人口占比 (總和 100%)
    pop_18 = random.choice([20, 30, 40])
    pop_40 = random.choice([30, 40])
    pop_60 = 100 - pop_18 - pop_40
    
    # 隨機產生調查占比 (總和 100%，且與人口不同)
    sur_18 = random.choice([10, 20])
    sur_40 = random.choice([30, 40, 50])
    sur_60 = 100 - sur_18 - sur_40
    
    # 目標組別 (隨機問其中一組的調整倍率)
    target_group = random.choice(["18~39歲", "40~59歲", "60歲以上"])
    
    if target_group == "18~39歲":
        pop, sur = pop_18, sur_18
    elif target_group == "40~59歲":
        pop, sur = pop_40, sur_40
    else:
        pop, sur = pop_60, sur_60
        
    rate = pop / sur
    
    # 建立 Markdown 表格字串
    table_md = f"""
| 組別 | 人口占比 | 調查占比 | 調整倍率 |
| :---: | :---: | :---: | :---: |
| 18~39歲組 | {pop_18}% | {sur_18}% | ? |
| 40~59歲組 | {pop_40}% | {sur_40}% | ... |
| 60歲以上組 | {pop_60}% | {sur_60}% | ... |
| **總計** | **100%** | **100%** | |
    """
    
    q_str = (f"某民調公司依年齡分3組，因受訪者分佈不均，利用「調整倍率」修正結果。\n"
             f"已知公式：**調整倍率 = 該組人口占比 / 該組調查占比**。\n\n"
             f"請參考下表，計算 **{target_group}組** 的調整倍率是多少？\n"
             f"{table_md}")
             
    ans_str = f"{rate:.1f} (或 {pop}/{sur})"
    detail = f"{target_group}的人口是 {pop}%，調查是 {sur}%。\n調整倍率 = {pop}% ÷ {sur}% = {rate}。"
    
    return {"topic": "📊 資料解讀-民調倍率", "question": q_str, "answer": ans_str, "detail": detail}

def generate_table_bicycle_gear():
    """表格題：腳踏車齒輪比 (參考上傳圖片 10)"""
    # 隨機產生齒數
    front_gears = sorted(random.sample([20, 22, 30, 32, 40, 44], 3))
    rear_gears = sorted(random.sample([12, 14, 16, 18, 20, 24, 28], 5))
    
    # 建立 Markdown 表格
    front_str = "、".join(map(str, front_gears))
    rear_str = "、".join(map(str, rear_gears))
    
    table_md = f"""
| 位置 | 齒數規格 |
| :--- | :--- |
| **前齒輪** | {front_str} 齒 |
| **後齒輪** | {rear_str} 齒 |
    """
    
    # 設計題目：比較費力程度
    # 齒輪比 = 前 / 後。 比值越大越費力(騎越快)，比值越小越省力。
    f1, r1 = random.choice(front_gears), random.choice(rear_gears)
    ratio1 = f1 / r1
    
    # 生成一個選項，讓它更費力 (比值更大) 或 更省力
    mode = random.choice(["更費力", "更省力"])
    
    q_str = (f"小桃的變速自行車齒輪規格如下表所示。已知 **齒輪比 = 前齒輪齒數 / 後齒輪齒數**，"
             f"且齒輪比越大踩起來越費力，越小越省力。\n\n"
             f"{table_md}\n"
             f"若她原本使用「前 {f1} / 後 {r1}」的組合，現在想切換成一個 **{mode}** 的組合，"
             f"下列哪一種配置是正確的？")
    
    # 尋找答案
    valid_answers = []
    for f in front_gears:
        for r in rear_gears:
            if f == f1 and r == r1: continue
            r_new = f / r
            if mode == "更費力" and r_new > ratio1:
                valid_answers.append(f"前 {f} / 後 {r}")
            elif mode == "更省力" and r_new < ratio1:
                valid_answers.append(f"前 {f} / 後 {r}")
    
    if not valid_answers:
        # 防呆：如果找不到，就重生成簡單的算術題
        q_str = f"請計算當前齒輪為 {f1}，後齒輪為 {r1} 時，齒輪比為何？\n{table_md}"
        ans_str = f"{ratio1:.2f}"
        detail = f"齒輪比 = {f1} ÷ {r1} ≈ {ratio1:.2f}"
    else:
        # 隨機選一個正確答案顯示
        correct_ans = random.choice(valid_answers)
        ans_str = f"例如：{correct_ans} (還有其他可能)"
        detail = (f"原組合齒輪比 = {f1}/{r1} ≈ {ratio1:.2f}。\n"
                  f"要{mode}，需找齒輪比 {'大於' if mode=='更費力' else '小於'} {ratio1:.2f} 的組合。\n"
                  f"正確選項之一為 {correct_ans}。")

    return {"topic": "🚲 資料解讀-齒輪比", "question": q_str, "answer": ans_str, "detail": detail}

# ==========================================
# Part 3: 歷屆試題還原 (Real Exam Restored)
# ==========================================

def generate_real_exam_exponents():
    """還原題型：指數律運算"""
    base = random.choice([2, 3, 5, 7, 10])
    n1 = random.randint(5, 15)
    n2 = random.randint(2, 5)
    n3 = random.randint(3, 8)
    q_str = f"算式 ${base}^{{{n1}}} \\times {base}^{{{n2}}} \\div {base}^{{{n3}}}$ 之值可用下列何者表示？"
    ans_pow = n1 + n2 - n3
    ans_str = f"${base}^{{{ans_pow}}}$"
    detail = f"指數律：相乘指數相加，相除指數相減。$({n1} + {n2}) - {n3} = {ans_pow}$。"
    return {"topic": "🔥 歷屆-指數律", "question": q_str, "answer": ans_str, "detail": detail}

def generate_real_exam_polynomial():
    """還原題型：多項式減法"""
    a = random.randint(2, 9)
    b = random.randint(-9, -1)
    c = random.randint(1, 9)
    d = random.randint(-9, -1)
    q_str = f"計算 $({a}x^2 + ({b}x)) - ({c} + ({d}x))$ 的結果，與下列何者相同？"
    coeff_x = b - d
    coeff_c = -c
    x_sign = "+" if coeff_x >= 0 else "-"
    c_sign = "+" if coeff_c >= 0 else "-"
    ans_str = f"${a}x^2 {x_sign} {abs(coeff_x)}x {c_sign} {abs(coeff_c)}$"
    detail = f"去括號變號：$({a}x^2 {b}x) - {c} - ({d}x) = {a}x^2 + ({b}-{d})x - {c}$。"
    return {"topic": "🔥 歷屆-多項式", "question": q_str, "answer": ans_str, "detail": detail}

def generate_real_exam_system_val():
    """還原題型：聯立方程式求代數值"""
    x = random.randint(-5, 5)
    y = random.randint(-5, 5)
    a1 = random.randint(10, 40)
    b1 = random.randint(2, 9)
    c1 = a1 * x + b1 * y
    a2 = random.randint(10, 40)
    b2 = -b1
    c2 = a2 * x + b2 * y
    ask_a = random.randint(1, 3)
    ask_b = random.randint(1, 3)
    target_val = ask_a * x + ask_b * y
    eq1 = f"{a1}x + {b1}y = {c1}"
    eq2 = f"{a2}x {b2}y = {c2}"
    q_str = f"若二元一次聯立方程式 $\\begin{{cases}} {eq1} \\\\ {eq2} \\end{{cases}}$ 的解為 $\\begin{{cases}} x=a \\\\ y=b \\end{{cases}}$，則 ${ask_a}a + {ask_b}b$ 之值為何？"
    ans_str = f"{target_val}"
    detail = f"先解聯立得 $x={x}, y={y}$。代入 ${ask_a}({x}) + {ask_b}({y}) = {target_val}$。"
    return {"topic": "🔥 歷屆-聯立方程式", "question": q_str, "answer": ans_str, "detail": detail}

def generate_real_exam_radicals():
    """還原題型：根號運算"""
    a = random.randint(2, 4)
    b = random.choice([2, 3, 5])
    c = random.choice([6, 10, 15])
    d = random.choice([2, 3, 5])
    q_str = f"計算 $({a}\\sqrt{{{b}}} + \\sqrt{{{c}}}) \\times \\sqrt{{{d}}}$ 的結果。"
    term1_inner = b * d
    term2_inner = c * d
    # 簡單化簡
    def simplify_sqrt(val):
        root = 1
        for i in range(2, int(math.sqrt(val)) + 1):
            while val % (i * i) == 0:
                root *= i
                val //= (i * i)
        return root, val
    c1, r1 = simplify_sqrt(term1_inner)
    c2, r2 = simplify_sqrt(term2_inner)
    total_c1 = a * c1
    if r1 == r2:
        ans_str = f"${total_c1 + c2}\\sqrt{{{r1}}}$"
    else:
        term1 = f"{total_c1}\\sqrt{{{r1}}}" if r1 > 1 else f"{total_c1}"
        term2 = f"{c2}\\sqrt{{{r2}}}" if r2 > 1 else f"{c2}"
        if c2 == 1 and r2 > 1: term2 = f"\\sqrt{{{r2}}}"
        ans_str = f"${term1} + {term2}$"
    detail = f"分配律：${a}\\sqrt{{{b}}}\\times\\sqrt{{{d}}} + \\sqrt{{{c}}}\\times\\sqrt{{{d}}} = {a}\\sqrt{{{term1_inner}}} + \\sqrt{{{term2_inner}}}$，再化簡。"
    return {"topic": "🔥 歷屆-根號運算", "question": q_str, "answer": ans_str, "detail": detail}

def generate_real_exam_quadratic_shift():
    """還原題型：二次函數平移"""
    h = random.randint(-9, 9)
    k = random.randint(-10, 10)
    shift = random.randint(2, 10)
    direction = random.choice(["右", "左"])
    h_sign = "+" if h >= 0 else "-"
    org_eq = f"y = - (x {h_sign} {abs(h)})^2 + {k}"
    q_str = f"座標平面上有二次函數 ${org_eq}$ 的圖形，將此圖形向{direction}平移 {shift} 單位。求新圖形的頂點座標？"
    org_v_x = -h
    org_v_y = k
    if direction == "右":
        new_v_x = org_v_x + shift
    else:
        new_v_x = org_v_x - shift
    ans_str = f"$({new_v_x}, {org_v_y})$"
    detail = f"原頂點為 $({org_v_x}, {org_v_y})$。向{direction}移 {shift} 單位 $\\rightarrow$ x 座標{'+' if direction=='右' else '-'} {shift}。"
    return {"topic": "🔥 歷屆-二次函數平移", "question": q_str, "answer": ans_str, "detail": detail}

# ==========================================
# Part 4: 題型策略地圖
# ==========================================

TOPIC_MAPPING = {
    # 基礎區
    "基礎 - 數與量": generate_number_basic,
    "基礎 - 代數": generate_linear_algebra_basic,
    "基礎 - 幾何": generate_geometry_basic,
    # 資料解讀區 (New!)
    "📊 素養 - 民調調整倍率 (表格)": generate_table_poll_adjustment,
    "🚲 素養 - 腳踏車齒輪比 (表格)": generate_table_bicycle_gear,
    # 歷屆改編區
    "🔥 歷屆 - 指數律運算": generate_real_exam_exponents,
    "🔥 歷屆 - 多項式加減": generate_real_exam_polynomial,
    "🔥 歷屆 - 聯立方程式求值": generate_real_exam_system_val,
    "🔥 歷屆 - 根號運算": generate_real_exam_radicals,
    "🔥 歷屆 - 二次函數平移": generate_real_exam_quadratic_shift,
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
        try:
            pdf.add_font('TaipeiSans', '', font_path, uni=True)
            pdf.set_font("TaipeiSans", '', 14)
            font_ready = True
        except Exception as e:
            print(f"Font Error: {e}")
    
    if not font_ready:
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, "Error: Chinese font not found.", ln=True)

    suffix = "(學生卷)" if mode == "student" else "(解答卷)"
    full_title = f"{custom_title} {suffix}"
    pdf.cell(0, 10, full_title, ln=True, align='C')
    pdf.ln(10)
    
    # 1. 自動生成試題區
    if exam_data:
        for idx, item in enumerate(exam_data):
            # 處理 LaTeX 與表格
            # 注意：FPDF 支援度有限，這裡主要做純文字清理，表格無法直接轉 PDF 表格
            # 所以 PDF 版只會顯示 "請見網頁版表格" 或簡單文字敘述
            clean_q = item['question'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\times', 'x').replace('\\div', '÷')
            clean_a = item['answer'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\pi', 'π')
            
            # 偵測是否含有 Markdown 表格 (簡單判斷)
            if "|" in clean_q:
                clean_q = clean_q.split("|")[0] + "\n[圖表題，請參閱網頁版或附圖]"
            
            topic_show = item['topic'].split('-')[-1] if '-' in item['topic'] else item['topic']
            
            question_text = f"Q{idx+1}. [{topic_show}] {clean_q}"
            pdf.multi_cell(0, 10, question_text)
            
            if mode == "student":
                pdf.ln(25) 
            else:
                pdf.set_text_color(255, 0, 0)
                pdf.multi_cell(0, 8, f"Ans: {clean_a}")
                pdf.set_font_size(10)
                pdf.set_text_color(100, 100, 100)
                pdf.multi_cell(0, 8, f"解析: {item['detail']}")
                pdf.set_text_color(0, 0, 0)
                if font_ready: pdf.set_font("TaipeiSans", '', 14)
                else: pdf.set_font("Arial", '', 14)
                pdf.ln(5)
    else:
        if not uploaded_images:
            pdf.cell(0, 10, "本試卷無隨機題目。", ln=True)

    # 2. 圖片試題區
    if uploaded_images:
        pdf.add_page()
        if font_ready: pdf.set_font("TaipeiSans", '', 16)
        pdf.cell(0, 10, "--- 以下為上傳之圖片試題 ---", ln=True, align='C')
        
        for img_file in uploaded_images:
            tmp_path = None
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
                
            except Exception as e:
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 10, f"Image Error: {e}", ln=True)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except:
                        pass

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# Part 6: Streamlit UI
# ==========================================

def main():
    st.title("📝 全方位國中數學出題系統 (Pro版)")
    st.markdown("### 包含基礎觀念、歷屆改編與 **📊 素養表格題**")
    st.markdown("---")

    all_topics = list(TOPIC_MAPPING.keys())
    if "selected_topics" not in st.session_state:
        # 預設選一些素養題
        st.session_state.selected_topics = [t for t in all_topics if "素養" in t]

    def toggle_all():
        if st.session_state.use_all_topics:
            st.session_state.selected_topics = all_topics
        else:
            st.session_state.selected_topics = []

    with st.sidebar:
        st.header("⚙️ 試卷設定")
        custom_title = st.text_input("試卷標題", value="會考衝刺練習")
        
        st.subheader("📸 上傳考題圖片")
        uploaded_files = st.file_uploader(
            "上傳圖片 (支援 JPG/PNG，可多張)", 
            type=['png', 'jpg', 'jpeg'], 
            accept_multiple_files=True
        )
        if uploaded_files:
            st.caption(f"已上傳 {len(uploaded_files)} 張圖片")

        st.divider()

        st.checkbox("全選所有單元", key="use_all_topics", on_change=toggle_all)
        selected_topics = st.multiselect("選擇單元 (可複選)", options=all_topics, key="selected_topics")
        num_questions = st.slider("題目數量", 5, 50, 10)
        generate_btn = st.button("🚀 建立新考卷", type="primary")
        
        st.info("🔥 **新功能**：新增「表格資料解讀」題型，能自動產生民調倍率表與齒輪比表格！")

    if "exam_data" not in st.session_state:
        st.session_state["exam_data"] = []
    
    if generate_btn:
        if not selected_topics and not uploaded_files:
            st.error("請至少選擇一個單元或上傳圖片！")
        else:
            if selected_topics:
                with st.spinner("正在生成素養題..."):
                    st.session_state["exam_data"] = generate_exam_data(selected_topics, num_questions)
            else:
                st.session_state["exam_data"] = []
            
            st.success("成功生成！")

    # ==========================================
    # 全新設計：線上考卷模式 (Web View)
    # ==========================================
    if st.session_state["exam_data"] or uploaded_files:
        st.markdown(f"## 🏫 {custom_title}")
        
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        with col_ctrl1:
            show_answers = st.checkbox("🔍 顯示解答與解析 (教師模式)", value=False)
        with col_ctrl2:
            if st.button("📥 產生 PDF (備用)"):
                safe_title = custom_title.replace(" ", "_")
                pdf_bytes = create_pdf(st.session_state["exam_data"], custom_title, mode="parent", uploaded_images=uploaded_files)
                st.download_button("點此下載 PDF", pdf_bytes, f"{safe_title}.pdf", "application/pdf")

        st.divider()

        if st.session_state["exam_data"]:
            st.subheader("第一部分：隨機試題")
            for i, q in enumerate(st.session_state["exam_data"]):
                topic_display = q['topic'].split('-')[-1] if '-' in q['topic'] else q['topic']
                st.markdown(f"#### Q{i+1}. [{topic_display}]")
                # [關鍵修正] 使用 st.markdown 才能正確顯示表格
                st.markdown(q['question'])
                
                if show_answers:
                    with st.expander("查看解答", expanded=True):
                        st.success(f"**答案：** {q['answer']}")
                        st.caption(f"**解析：** {q['detail']}")
                else:
                    st.write("(請在此計算作答...)")
                    st.write("---")

        if uploaded_files:
            st.subheader("第二部分：圖片試題")
            for img_file in uploaded_files:
                st.image(img_file, caption=img_file.name, use_container_width=True)
                st.write("---")

if __name__ == "__main__":
    main()
