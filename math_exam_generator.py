import streamlit as st
import random
import math
from fpdf import FPDF
import os
import tempfile

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
# Part 2: 歷屆試題還原 (Real Exam Restored)
# ==========================================

def generate_real_exam_exponents():
    """還原題型：指數律運算 (參考 Q1)"""
    # 題目形式：7^10 * 7^2 / 7^4
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
    """還原題型：多項式減法 (參考 Q2)"""
    # 題目形式：(5x^2 - 2x) - (4 - 3x)
    a = random.randint(2, 9)
    b = random.randint(-9, -1) # 讓它是負的，增加去括號難度
    c = random.randint(1, 9)
    d = random.randint(-9, -1) # 第二項 x 係數
    
    # 建構題目字串 (注意符號處理)
    poly1 = f"{a}x^2 {b}x" # 簡單處理，若 b 為負會顯示 5x^2 -2x (可接受，或寫更細)
    poly2 = f"{c} {d}x"
    
    q_str = f"計算 $({a}x^2 + ({b}x)) - ({c} + ({d}x))$ 的結果，與下列何者相同？"
    
    # 計算結果
    # x^2 係數: a
    # x 係數: b - d
    # 常數: -c
    coeff_x = b - d
    coeff_c = -c
    
    x_sign = "+" if coeff_x >= 0 else "-"
    c_sign = "+" if coeff_c >= 0 else "-"
    
    ans_str = f"${a}x^2 {x_sign} {abs(coeff_x)}x {c_sign} {abs(coeff_c)}$"
    detail = f"去括號變號：$({a}x^2 {b}x) - {c} - ({d}x) = {a}x^2 + ({b}-{d})x - {c}$。"
    return {"topic": "🔥 歷屆-多項式", "question": q_str, "answer": ans_str, "detail": detail}

def generate_real_exam_system_val():
    """還原題型：聯立方程式求代數值 (參考 Q4)"""
    # 先決定 x, y 答案 (整數)
    x = random.randint(-5, 5)
    y = random.randint(-5, 5)
    
    # 生成係數 (故意用一點大數字)
    a1 = random.randint(10, 40)
    b1 = random.randint(2, 9)
    c1 = a1 * x + b1 * y
    
    a2 = random.randint(10, 40)
    b2 = -b1 # 設計讓 y 係數互為相反數，方便消去 (或是隨機)
    c2 = a2 * x + b2 * y
    
    # 題目問 ax + by 的值
    ask_a = random.randint(1, 3)
    ask_b = random.randint(1, 3)
    target_val = ask_a * x + ask_b * y
    
    eq1 = f"{a1}x + {b1}y = {c1}"
    eq2 = f"{a2}x {b2}y = {c2}" # b2 是負數
    
    q_str = f"若二元一次聯立方程式 $\\begin{{cases}} {eq1} \\\\ {eq2} \\end{{cases}}$ 的解為 $\\begin{{cases}} x=a \\\\ y=b \\end{{cases}}$，則 ${ask_a}a + {ask_b}b$ 之值為何？"
    ans_str = f"{target_val}"
    detail = f"先解聯立得 $x={x}, y={y}$。代入 ${ask_a}({x}) + {ask_b}({y}) = {target_val}$。"
    return {"topic": "🔥 歷屆-聯立方程式", "question": q_str, "answer": ans_str, "detail": detail}

def generate_real_exam_radicals():
    """還原題型：根號運算 (參考 Q8)"""
    # 題目形式：(2sqrt(3) + sqrt(6)) * sqrt(2)
    # 設計構造： (a sqrt(b) + sqrt(c)) * sqrt(d)
    # 讓 c * d = b * k^2 (可以化簡)
    
    d = random.choice([2, 3, 5])
    b = random.choice([2, 3, 5])
    if b == d: b = 7 # 避免過度重複
    
    a = random.randint(2, 4)
    # 讓 c*d 是一個完全平方數的倍數，例如 c=6, d=2 -> 12 -> 2sqrt(3)
    # 或者簡單一點，隨機生成，最後讓答案保留根號
    c = b * d * random.choice([1, 4]) # 這樣 c*d 會包含 d^2
    # 修正邏輯：隨機出題，解析寫清楚化簡過程
    
    c = random.choice([6, 10, 15])
    d = random.choice([2, 3, 5])
    
    q_str = f"計算 $({a}\\sqrt{{{b}}} + \\sqrt{{{c}}}) \\times \\sqrt{{{d}}}$ 的結果。"
    
    # 答案計算: a*sqrt(bd) + sqrt(cd)
    term1_inner = b * d
    term2_inner = c * d
    
    # 簡單化簡 function
    def simplify_sqrt(val):
        root = 1
        for i in range(2, int(math.sqrt(val)) + 1):
            while val % (i * i) == 0:
                root *= i
                val //= (i * i)
        return root, val

    c1, r1 = simplify_sqrt(term1_inner)
    c2, r2 = simplify_sqrt(term2_inner)
    
    # 合併係數 a
    total_c1 = a * c1
    
    # 檢查根號內是否相同，可合併
    if r1 == r2:
        ans_str = f"${total_c1 + c2}\\sqrt{{{r1}}}$"
    else:
        term1 = f"{total_c1}\\sqrt{{{r1}}}" if r1 > 1 else f"{total_c1}"
        term2 = f"{c2}\\sqrt{{{r2}}}" if r2 > 1 else f"{c2}"
        if c2 == 1 and r2 > 1: term2 = f"\\sqrt{{{r2}}}" # 係數1不寫
        ans_str = f"${term1} + {term2}$"

    detail = f"分配律：${a}\\sqrt{{{b}}}\\times\\sqrt{{{d}}} + \\sqrt{{{c}}}\\times\\sqrt{{{d}}} = {a}\\sqrt{{{term1_inner}}} + \\sqrt{{{term2_inner}}}$，再化簡。"
    return {"topic": "🔥 歷屆-根號運算", "question": q_str, "answer": ans_str, "detail": detail}

def generate_real_exam_quadratic_shift():
    """還原題型：二次函數平移 (參考 Q21)"""
    # 題目：y = -(x+h)^2 + k 向右/左平移
    h = random.randint(-9, 9)
    k = random.randint(-10, 10)
    a = -1 # 參考題目開口向下
    
    shift = random.randint(2, 10)
    direction = random.choice(["右", "左"])
    
    h_sign = "+" if h >= 0 else "-"
    org_eq = f"y = - (x {h_sign} {abs(h)})^2 + {k}"
    
    q_str = f"座標平面上有二次函數 ${org_eq}$ 的圖形，將此圖形向{direction}平移 {shift} 單位。求新圖形的頂點座標？"
    
    # 原頂點 (-h, k)
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
# Part 3: 進階生活應用 (Advanced Scenario)
# ==========================================

def generate_advanced_inequality():
    """進階-生活應用(不等式)"""
    scenario = random.choice(['ticket', 'mobile_plan'])
    if scenario == 'ticket':
        price = random.choice([100, 200, 250, 300, 500])
        group_limit = random.choice([20, 30, 40, 50])
        discount_off = random.choice([10, 20, 30]) 
        discount_rate = (100 - discount_off) / 100
        threshold = math.ceil(group_limit * discount_rate)
        q_str = (f"遊樂園門票每張 {price} 元，{group_limit} 人以上(含)團體票打 {10-discount_off//10} 折。"
                 f"若團體不足 {group_limit} 人，人數至少多少時，直接買 {group_limit} 張團體票反而划算？")
        ans_str = f"{threshold} 人"
        detail = f"設人數 x。$x \\times {price} > {group_limit} \\times {price} \\times {discount_rate}$。"
    else:
        base_a = random.randint(300, 600)
        rate_a = random.randint(2, 4)
        base_b = random.randint(100, 200)
        rate_b = random.randint(6, 9)
        diff_base = base_a - base_b
        diff_rate = rate_b - rate_a
        threshold = math.ceil(diff_base / diff_rate)
        q_str = (f"電信方案 A 月租費 {base_a} 元，每分鐘通話 {rate_a} 元；"
                 f"方案 B 月租費 {base_b} 元，每分鐘通話 {rate_b} 元。"
                 f"當每月通話時間超過多少分鐘時，選擇方案 A 會比較划算？")
        ans_str = f"{threshold} 分鐘"
        detail = f"設通話 x 分鐘。${base_a} + {rate_a}x < {base_b} + {rate_b}x$，移項解 x。"
    return {"topic": "進階-不等式應用", "question": q_str, "answer": ans_str, "detail": detail}

def generate_advanced_sequence():
    """進階-規律探索(數列)"""
    # 火柴棒問題
    shape = random.choice(['正方形', '正三角形', '正六邊形'])
    if shape == '正方形': a1, d = 4, 3
    elif shape == '正三角形': a1, d = 3, 2
    else: a1, d = 6, 5
    n = random.randint(10, 50)
    q_str = (f"用火柴棒排連鎖{shape}，排1個需{a1}根，排2個需{a1+d}根... "
             f"請問排 {n} 個連鎖{shape}共需幾根火柴棒？")
    ans_val = a1 + (n - 1) * d
    ans_str = f"{ans_val} 根"
    detail = f"等差數列首項 {a1}，公差 {d}。公式 $a_n = a_1 + (n-1)d$。"
    return {"topic": "進階-數列規律", "question": q_str, "answer": ans_str, "detail": detail}

# ==========================================
# Part 4: 題型策略地圖
# ==========================================

TOPIC_MAPPING = {
    # 基礎區
    "基礎 - 數與量": generate_number_basic,
    "基礎 - 代數": generate_linear_algebra_basic,
    "基礎 - 幾何": generate_geometry_basic,
    # 歷屆改編區 (New!)
    "🔥 歷屆 - 指數律運算": generate_real_exam_exponents,
    "🔥 歷屆 - 多項式加減": generate_real_exam_polynomial,
    "🔥 歷屆 - 聯立方程式求值": generate_real_exam_system_val,
    "🔥 歷屆 - 根號運算": generate_real_exam_radicals,
    "🔥 歷屆 - 二次函數平移": generate_real_exam_quadratic_shift,
    # 進階應用區
    "進階 - 不等式應用": generate_advanced_inequality,
    "進階 - 數列規律": generate_advanced_sequence,
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
            clean_q = item['question'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\times', 'x').replace('\\div', '÷').replace('\\le', '<=').replace('\\ge', '>=')
            clean_a = item['answer'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\pi', 'π').replace('\\times', 'x')
            
            # 標題縮寫
            topic_show = item['topic']
            if "🔥" in topic_show: topic_show = "歷屆改編"
            elif "進階" in topic_show: topic_show = "素養應用"
            elif "-" in topic_show: topic_show = topic_show.split('-')[1]
            
            question_text = f"Q{idx+1}. [{topic_show}] {clean_q}"
            pdf.multi_cell(0, 10, question_text)
            
            if mode == "student":
                pdf.ln(25) 
            else:
                pdf.set_text_color(255, 0, 0)
                pdf.multi_cell(0, 8, f"Ans: {clean_a}")
                # [Fix] 修正錯誤：使用 set_font_size 而不是 set_font(size=10)
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

    # 2. 圖片試題區 (優化：每張圖一頁，滿版顯示)
    if uploaded_images:
        pdf.add_page()
        if font_ready: pdf.set_font("TaipeiSans", '', 16)
        pdf.cell(0, 10, "--- 以下為上傳之圖片試題 ---", ln=True, align='C')
        
        for img_file in uploaded_images:
            try:
                img_file.seek(0)
                file_ext = img_file.name.split('.')[-1].lower()
                if file_ext not in ['jpg', 'jpeg', 'png']: file_ext = 'png'
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                    tmp.write(img_file.read())
                    tmp_path = tmp.name
                
                # [Improvement] 新增一頁，並將圖片放大至滿版 (寬 190mm，預留邊距)
                pdf.add_page()
                # A4 寬 210mm，高 297mm。w=190 代表左右各留 10mm 邊距
                pdf.image(tmp_path, x=10, y=10, w=190)
                
                os.remove(tmp_path)
            except Exception as e:
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 10, f"Error: {e}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# Part 6: Streamlit UI
# ==========================================

def main():
    st.title("📝 全方位國中數學出題系統 (Pro版)")
    st.markdown("### 包含基礎觀念與 **🔥 歷屆試題還原** (上傳圖片即還原)")
    st.markdown("---")

    all_topics = list(TOPIC_MAPPING.keys())
    if "selected_topics" not in st.session_state:
        # 預設選一些基礎跟歷屆改編
        st.session_state.selected_topics = [t for t in all_topics if "歷屆" in t][:3]

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
        
        st.info("🔥 **新功能**：已將您的圖片試題轉化為可隨機變化的「歷屆改編」題型，勾選後即可無限生成！")

    if "exam_data" not in st.session_state:
        st.session_state["exam_data"] = []
    
    if generate_btn:
        if not selected_topics and not uploaded_files:
            st.error("請至少選擇一個單元或上傳圖片！")
        else:
            if selected_topics:
                with st.spinner("正在生成歷屆改編題..."):
                    st.session_state["exam_data"] = generate_exam_data(selected_topics, num_questions)
            else:
                st.session_state["exam_data"] = []
            
            st.success("成功生成！")

    if st.session_state["exam_data"] or uploaded_files:
        st.subheader(f"👀 {custom_title} - 試題預覽")
        if st.session_state["exam_data"]:
            for i, q in enumerate(st.session_state["exam_data"][:3]):
                with st.expander(f"Q{i+1} [{q['topic']}]"):
                    st.write(f"**題目**： {q['question']}")
                    st.write(f"**答案**： {q['answer']}")
                    st.caption(f"解析： {q['detail']}")
        
        st.divider()
        safe_title = custom_title.replace(" ", "_")
        col1, col2 = st.columns(2)
        with col1:
            pdf_student = create_pdf(st.session_state["exam_data"], custom_title, mode="student", uploaded_images=uploaded_files)
            st.download_button("📄 下載學生版", pdf_student, f"{safe_title}_學生版.pdf", "application/pdf")
        with col2:
            pdf_parent = create_pdf(st.session_state["exam_data"], custom_title, mode="parent", uploaded_images=uploaded_files)
            st.download_button("👨‍🏫 下載家長版", pdf_parent, f"{safe_title}_解答版.pdf", "application/pdf")

if __name__ == "__main__":
    main()
