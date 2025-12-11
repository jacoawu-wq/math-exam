import streamlit as st
import random
import math
from fpdf import FPDF
import os

# 1. 設定頁面配置
st.set_page_config(page_title="全方位數學自動出題系統", layout="wide", page_icon="📝")

# ==========================================
# Part 1: 題目生成核心邏輯 (The Generator)
# ==========================================

# --- 領域一：數與量 (Number and Quantity) ---

def generate_number_basic():
    """數與量基礎：四則運算、科學記號、指數律"""
    sub_type = random.choice(['calc', 'sci', 'index'])
    
    if sub_type == 'calc':
        # 整數四則運算 (含負數)
        a = random.randint(-20, 20)
        b = random.randint(-20, 20)
        c = random.randint(-10, 10)
        if c == 0: c = 1
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['*', '-']) # 避免除法除不盡，先用乘法
        q_str = f"計算： ${a} {op1} ({b}) {op2} ({c})$"
        # 簡單計算答案
        val_b = b
        val_c = c
        res = val_b * val_c if op2 == '*' else val_b - val_c
        final = a + res if op1 == '+' else a - res
        ans_str = f"{final}"
        detail = "先乘除後加減，注意正負號變化。"
        
    elif sub_type == 'sci':
        # 科學記號
        base = random.randint(1, 9)
        power = random.randint(-8, 8)
        num = base * (10**power)
        if power >= 0:
            q_str = f"將整數 {num} 以科學記號表示。"
        else:
            q_str = f"將小數 {num:.8f}".rstrip('0') + " 以科學記號表示。"
        ans_str = f"${base} \\times 10^{{{power}}}$"
        detail = "科學記號形式為 $a \\times 10^n$，其中 $1 \\le a < 10$。"
        
    else:
        # 指數律
        base = random.randint(2, 5)
        p1 = random.randint(2, 5)
        p2 = random.randint(2, 5)
        q_str = f"化簡： $({base}^{{{p1}}})^{{{p2}}} \\div {base}^{{{p2}}}$"
        # ans: base^(p1*p2 - p2)
        final_p = p1 * p2 - p2
        ans_str = f"${base}^{{{final_p}}}$"
        detail = "利用指數律：$(a^m)^n = a^{mn}$ 以及 $a^m \\div a^n = a^{m-n}$。"

    return {"topic": "數與量-基礎運算", "question": q_str, "answer": ans_str, "detail": detail}

def generate_factors_multiples():
    """因數與倍數：GCD, LCM"""
    # 設計兩個數字，讓它們有公因數
    common = random.randint(2, 12)
    a = common * random.randint(1, 10)
    b = common * random.randint(1, 10)
    
    q_type = random.choice(['gcd', 'lcm'])
    if q_type == 'gcd':
        q_str = f"求 ({a}, {b}) 之最大公因數。"
        ans_val = math.gcd(a, b)
        ans_str = f"{ans_val}"
        detail = "利用短除法找出兩數共同的質因數相乘。"
    else:
        q_str = f"求 [{a}, {b}] 之最小公倍數。"
        gcd_val = math.gcd(a, b)
        ans_val = (a * b) // gcd_val
        ans_str = f"{ans_val}"
        detail = "兩數乘積除以最大公因數即為最小公倍數。"
        
    return {"topic": "數與量-因數倍數", "question": q_str, "answer": ans_str, "detail": detail}

def generate_progression():
    """數列與級數 (等差)"""
    a1 = random.randint(-10, 20)
    d = random.randint(-5, 10)
    if d == 0: d = 2
    n = random.randint(5, 20)
    
    q_type = random.choice(['an', 'sum'])
    if q_type == 'an':
        # 求第 n 項
        q_str = f"一等差數列首項 $a_1={a1}$，公差 $d={d}$，求第 {n} 項 $a_{{{n}}}$。"
        an = a1 + (n - 1) * d
        ans_str = f"{an}"
        detail = f"公式：$a_n = a_1 + (n-1)d \\rightarrow {a1} + ({n}-1)({d})$"
    else:
        # 求前 n 項和
        q_str = f"一等差級數首項 $a_1={a1}$，公差 $d={d}$，求前 {n} 項的和 $S_{{{n}}}$。"
        an = a1 + (n - 1) * d
        sn = int(n * (a1 + an) / 2)
        ans_str = f"{sn}"
        detail = f"公式：$S_n = \\frac{{n(a_1 + a_n)}}{{2}}$ 或 $\\frac{{n[2a_1 + (n-1)d]}}{{2}}$"

    return {"topic": "數與量-數列級數", "question": q_str, "answer": ans_str, "detail": detail}

# --- 領域二：代數 (Algebra) ---

def generate_linear_algebra_basic():
    """一元一次方程式與不等式"""
    x = random.randint(-15, 15)
    a = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    b = random.randint(-20, 20)
    
    q_type = random.choice(['eq', 'ineq'])
    
    if q_type == 'eq':
        # ax + b = c
        c = a * x + b
        b_sign = "+" if b >= 0 else "-"
        q_str = f"解方程式： ${a}x {b_sign} {abs(b)} = {c}$"
        ans_str = f"$x = {x}$"
        detail = f"移項：${a}x = {c} - ({b}) = {c-b}$，故 $x = {x}$。"
    else:
        # 不等式 ax + b > c (設計簡單整數解)
        # 讓右邊 c = a*x + b - 1 (若 >)
        delta = random.randint(1, 10)
        c = a * x + b - delta # 使得 x 真實值比邊界大或小
        
        symbol = ">" if a > 0 else "<" # 隨機符號邏輯太複雜，先固定求 x 範圍
        # 題目：求滿足 ax + b > c 的最小整數 (假設 a>0)
        if a > 0:
            q_str = f"解不等式： ${a}x + {b} > {c}$"
            # ax > c - b -> x > (c-b)/a
            boundary = (c - b) / a
            ans_str = f"$x > {boundary:.1f}$" # 顯示小數或分數
            detail = "移項整理，注意若同除以負數，不等號方向要改變。"
        else:
            q_str = f"解不等式： ${a}x + {b} < {c}$" # a是負的
            # ax < c - b -> 除以負數 -> x > (c-b)/a
            boundary = (c - b) / a
            ans_str = f"$x > {boundary:.1f}$"
            detail = "係數為負數，移項除法時不等號方向改變 ($< \u2192 >$)。"
            
    return {"topic": "代數-一次方程式/不等式", "question": q_str, "answer": ans_str, "detail": detail}

def generate_system_eq():
    """二元一次聯立方程式"""
    # 先決定答案 x, y
    x = random.randint(-10, 10)
    y = random.randint(-10, 10)
    
    # 隨機產生係數
    a1 = random.randint(1, 5); b1 = random.randint(1, 5)
    a2 = random.randint(1, 5); b2 = random.randint(-5, -1)
    
    c1 = a1*x + b1*y
    c2 = a2*x + b2*y
    
    q_str = f"解聯立方程式： $\\begin{{cases}} {a1}x + {b1}y = {c1} \\\\ {a2}x {b2}y = {c2} \\end{{cases}}$"
    # 注意：b2是負數，顯示時要處理符號
    # 為了簡化顯示邏輯，直接顯示 b2 (如 -3y)
    
    # 修正顯示格式
    eq1 = f"{a1}x + {b1}y = {c1}"
    b2_sign = "+" if b2 > 0 else "" 
    eq2 = f"{a2}x {b2_sign}{b2}y = {c2}"
    q_str = f"解聯立方程式： (1) ${eq1}$ , (2) ${eq2}$"
    
    ans_str = f"$x={x}, y={y}$"
    detail = "可使用代入消去法或加減消去法，消去其中一個未知數求解。"
    
    return {"topic": "代數-聯立方程式", "question": q_str, "answer": ans_str, "detail": detail}

def generate_polynomials_quadratics():
    """乘法公式、多項式與一元二次方程式"""
    p_type = random.choice(['mul_formula', 'factor', 'solve_quad'])
    
    if p_type == 'mul_formula':
        # 乘法公式展開
        a = random.randint(1, 9)
        sign = random.choice(['+', '-'])
        q_str = f"展開： $(x {sign} {a})^2$"
        mid = 2 * a
        last = a * a
        sign_mid = '+' if sign == '+' else '-'
        ans_str = f"$x^2 {sign_mid} {mid}x + {last}$"
        detail = "和(差)的平方公式：$(a \pm b)^2 = a^2 \pm 2ab + b^2$"
        
    elif p_type == 'factor':
        # 因式分解 x^2 + (a+b)x + ab
        r1 = random.randint(1, 9)
        r2 = random.randint(1, 9)
        # 隨機正負
        if random.random() > 0.5: r1 = -r1
        if random.random() > 0.5: r2 = -r2
        
        mid = r1 + r2
        const = r1 * r2
        mid_str = f"+{mid}x" if mid >=0 else f"{mid}x"
        const_str = f"+{const}" if const >=0 else f"{const}"
        
        q_str = f"因式分解： $x^2 {mid_str} {const_str}$"
        
        sign1 = "+" if r1 > 0 else ""
        sign2 = "+" if r2 > 0 else ""
        ans_str = f"$(x {sign1}{r1})(x {sign2}{r2})$"
        detail = "利用十字交乘法，找出乘積為常數項、和為一次項係數的兩個數。"
        
    else:
        # 解一元二次方程式 (x-r1)(x-r2)=0
        r1 = random.randint(-9, 9)
        r2 = random.randint(-9, 9)
        # 避免 0
        if r1 == 0: r1 = 1
        
        mid = -(r1 + r2)
        const = r1 * r2
        mid_str = f"+{mid}x" if mid >=0 else f"{mid}x"
        const_str = f"+{const}" if const >=0 else f"{const}"
        
        q_str = f"解一元二次方程式： $x^2 {mid_str} {const_str} = 0$"
        ans_str = f"$x = {r1}$ 或 $x = {r2}$"
        detail = "先因式分解，若 $(x-a)(x-b)=0$，則 $x=a$ 或 $x=b$。"
        
    return {"topic": "代數-多項式與二次方程式", "question": q_str, "answer": ans_str, "detail": detail}

def generate_function_coordinates():
    """函數與直角坐標"""
    f_type = random.choice(['quadrant', 'linear_func'])
    
    if f_type == 'quadrant':
        x = random.randint(-10, 10)
        y = random.randint(-10, 10)
        if x == 0: x = 1
        if y == 0: y = -1
        q_str = f"點 P({x}, {y}) 位於直角坐標平面的第幾象限？"
        
        if x > 0 and y > 0: ans_str = "第一象限"
        elif x < 0 and y > 0: ans_str = "第二象限"
        elif x < 0 and y < 0: ans_str = "第三象限"
        else: ans_str = "第四象限"
        detail = "判斷 (x, y) 的正負號：(+,+)一, (-,+)二, (-,-)三, (+,-)四。"
        
    else:
        # 函數值 f(x) = ax + b
        a = random.randint(-5, 5)
        b = random.randint(-10, 10)
        target_x = random.randint(-5, 5)
        q_str = f"若函數 $f(x) = {a}x + {b}$，求 $f({target_x})$ 之值。"
        val = a * target_x + b
        ans_str = f"{val}"
        detail = f"將 $x={target_x}$ 代入函數： ${a}({target_x}) + {b} = {val}$"
        
    return {"topic": "代數-坐標與函數", "question": q_str, "answer": ans_str, "detail": detail}

# --- 領域三：幾何 (Geometry) ---

def generate_geometry_advanced():
    """幾何綜合 (三角形、平行、勾股、圓)"""
    g_type = random.choice(['pythagoras', 'angle_tri', 'circle_arc'])
    
    if g_type == 'pythagoras':
        # 勾股數 (3,4,5), (5,12,13), (6,8,10), (8,15,17)
        triples = [(3,4,5), (5,12,13), (6,8,10), (8,15,17)]
        a, b, c = random.choice(triples)
        q_str = f"直角三角形兩股長分別為 {a}, {b}，求斜邊長。"
        ans_str = f"{c}"
        detail = "畢氏定理：斜邊平方 = 兩股平方和 ($c^2 = a^2 + b^2$)。"
        
    elif g_type == 'angle_tri':
        # 三角形內角和
        a1 = random.randrange(30, 80, 5)
        a2 = random.randrange(30, 80, 5)
        q_str = f"三角形兩內角為 {a1}° 與 {a2}°，求第三個內角。"
        a3 = 180 - a1 - a2
        ans_str = f"{a3}°"
        detail = "三角形內角和為 180 度。"
        
    else:
        # 圓形：求圓周長或面積 (以 Pi 表示)
        r = random.randint(2, 10)
        ask = random.choice(['area', 'len'])
        if ask == 'area':
            q_str = f"半徑為 {r} 的圓，其面積為何？(以 $\\pi$ 表示)"
            ans_str = f"{r*r}\\pi"
            detail = "圓面積公式 = $\\pi r^2$"
        else:
            q_str = f"半徑為 {r} 的圓，其圓周長為何？(以 $\\pi$ 表示)"
            ans_str = f"{2*r}\\pi"
            detail = "圓周長公式 = $2 \\pi r$"
            
    return {"topic": "幾何-綜合應用", "question": q_str, "answer": ans_str, "detail": detail}

# --- 領域四：統計與機率 (Statistics) ---

def generate_statistics_prob():
    """統計數據與機率"""
    s_type = random.choice(['stats', 'prob'])
    
    if s_type == 'stats':
        # 平均數、中位數
        nums = [random.randint(10, 99) for _ in range(5)]
        nums.sort() # 排序方便算中位數
        q_target = random.choice(['mean', 'median'])
        nums_str = ", ".join(map(str, nums))
        
        if q_target == 'mean':
            # 為了好算，微調最後一個數字讓總和整除 5
            curr_sum = sum(nums)
            remainder = curr_sum % 5
            if remainder != 0:
                nums[-1] -= remainder # 微調
                nums_str = ", ".join(map(str, nums)) # 更新字串
            
            q_str = f"數據：{nums_str}。求算術平均數。"
            ans_val = sum(nums) // 5
            ans_str = f"{ans_val}"
            detail = "平均數 = 總和 $\\div$ 個數。"
        else:
            # 中位數
            q_str = f"數據：{nums_str}。求中位數。"
            ans_str = f"{nums[2]}" # 5個數的中間是第3個
            detail = "將資料由小到大排列，位於正中間的數即為中位數。"
            
    else:
        # 機率 (骰子或抽球)
        red = random.randint(2, 6)
        blue = random.randint(2, 6)
        total = red + blue
        q_str = f"袋中有 {red} 紅球、{blue} 藍球，隨機取出一球，求取出「紅球」的機率。"
        ans_str = f"$\\frac{{{red}}}{{{total}}}$"
        detail = f"機率 = 目標個數 / 總個數 = {red} / ({red}+{blue})。"
        
    return {"topic": "統計與機率", "question": q_str, "answer": ans_str, "detail": detail}


# ==========================================
# Part 2: 題型策略地圖 (TOPIC_MAPPING)
# ==========================================
# 這是擴充後的選單，涵蓋四大領域
TOPIC_MAPPING = {
    "數與量 - 基礎運算 (指數/科學記號)": generate_number_basic,
    "數與量 - 因數與倍數": generate_factors_multiples,
    "數與量 - 數列與級數": generate_progression,
    "代數 - 一次方程式與不等式": generate_linear_algebra_basic,
    "代數 - 二元一次聯立方程式": generate_system_eq,
    "代數 - 多項式與二次方程式": generate_polynomials_quadratics,
    "代數 - 坐標與函數": generate_function_coordinates,
    "幾何 - 圖形與證明 (勾股/圓/角)": generate_geometry_advanced,
    "統計與機率": generate_statistics_prob
}

def generate_exam_data(selected_topics, num_questions):
    if not selected_topics: return []
    exam_list = []
    # 為了混合均勻，如果選擇多個單元，依序循環產生
    for i in range(num_questions):
        # 輪流選擇單元，確保分佈平均
        topic_name = selected_topics[i % len(selected_topics)]
        generator_func = TOPIC_MAPPING[topic_name]
        exam_list.append(generator_func())
    
    # 打亂順序，讓考卷看起來更隨機
    random.shuffle(exam_list)
    return exam_list

# ==========================================
# Part 3: PDF 匯出功能 (The Exporter)
# ==========================================

class PDFExport(FPDF):
    def footer(self):
        self.set_y(-15)
        try:
            self.set_font("TaipeiSans", '', 10)
        except:
            self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(exam_data, custom_title, mode="student"):
    pdf = PDFExport()
    pdf.add_page()
    
    # 字型處理
    font_path = 'TaipeiSansTCBeta-Regular.ttf'
    font_ready = False
    
    if os.path.exists(font_path):
        try:
            pdf.add_font('TaipeiSans', '', font_path, uni=True)
            pdf.set_font("TaipeiSans", '', 14)
            font_ready = True
        except Exception as e:
            print(f"字型載入失敗: {e}")
    
    if not font_ready:
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, "Error: Chinese font not found (TaipeiSansTCBeta-Regular.ttf)", ln=True)
        pdf.ln(10)

    # 標題
    suffix = "(學生卷)" if mode == "student" else "(解答卷)"
    full_title = f"{custom_title} {suffix}"
    pdf.cell(0, 10, full_title, ln=True, align='C')
    pdf.ln(10)
    
    # 試題
    for idx, item in enumerate(exam_data):
        # 簡單清洗 LaTeX
        clean_q = item['question'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\times', 'x').replace('\\div', '÷').replace('\\le', '<=')
        clean_a = item['answer'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\pi', 'π').replace('\\times', 'x')
        
        # 顯示題目
        # [topic] 簡化顯示，只取 "-" 後面的字以免太長
        short_topic = item['topic'].split('-')[-1] if '-' in item['topic'] else item['topic']
        question_text = f"Q{idx+1}. [{short_topic}] {clean_q}"
        pdf.multi_cell(0, 10, question_text)
        
        if mode == "student":
            pdf.ln(25) 
        else:
            pdf.set_text_color(255, 0, 0) # Red
            pdf.multi_cell(0, 8, f"Ans: {clean_a}")
            
            # [修正處] 確保使用 set_font_size 以避免 TypeError
            pdf.set_font_size(10)
            pdf.set_text_color(100, 100, 100) # Gray
            pdf.multi_cell(0, 8, f"解析: {item['detail']}")
            
            pdf.set_text_color(0, 0, 0) # Reset
            if font_ready: pdf.set_font("TaipeiSans", '', 14)
            else: pdf.set_font("Arial", '', 14)
            pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# Part 4: Streamlit UI
# ==========================================

def main():
    st.title("📝 全方位國中數學出題系統")
    st.markdown("### 108課綱對應版 - 支援數與量、代數、幾何、統計")
    st.markdown("---")

    # 1. 初始化 Session State (確保選項不會消失的關鍵!)
    all_topics = list(TOPIC_MAPPING.keys())
    if "selected_topics" not in st.session_state:
        # 預設選前兩個單元
        st.session_state.selected_topics = all_topics[:2]

    # 2. 定義全選的 Callback 函數
    def toggle_all():
        if st.session_state.use_all_topics:
            st.session_state.selected_topics = all_topics
        else:
            # 取消全選時，恢復為預設前兩個 (或您想要清空也可以)
            st.session_state.selected_topics = all_topics[:2]

    with st.sidebar:
        st.header("⚙️ 試卷設定")
        custom_title = st.text_input("試卷標題", value="數學單元評量")
        
        # 全選功能 (綁定 key 和 callback)
        st.checkbox("全選所有單元", key="use_all_topics", on_change=toggle_all)
            
        # 多選單 (綁定 key，讓 Session State 自動管理)
        selected_topics = st.multiselect(
            "選擇單元 (可複選)",
            options=all_topics,
            key="selected_topics" 
        )
        
        num_questions = st.slider("題目數量", 5, 50, 10)
        generate_btn = st.button("🚀 建立新考卷", type="primary")
        
        st.info("💡 包含：指數律、GCD/LCM、等差數列、聯立方程式、十字交乘、幾何證明題型等。")

    if "exam_data" not in st.session_state:
        st.session_state["exam_data"] = []
    
    if generate_btn:
        if not selected_topics:
            st.error("請至少選擇一個單元！")
        else:
            with st.spinner("題目運算中..."):
                st.session_state["exam_data"] = generate_exam_data(selected_topics, num_questions)
            st.success(f"成功生成 {len(st.session_state['exam_data'])} 題！")

    if st.session_state["exam_data"]:
        st.subheader(f"👀 {custom_title} - 試題預覽")
        
        # 顯示前 3 題
        for i, q in enumerate(st.session_state["exam_data"][:3]):
            with st.expander(f"第 {i+1} 題 ({q['topic']})"):
                st.write(f"**題目**： {q['question']}")
                st.write(f"**答案**： {q['answer']}")
                st.caption(f"解析： {q['detail']}")
        
        if len(st.session_state["exam_data"]) > 3:
            st.info(f"... 還有 {len(st.session_state['exam_data'])-3} 題，請下載 PDF 查看完整版。")

        st.divider()
        
        safe_title = custom_title.replace(" ", "_")
        col1, col2 = st.columns(2)
        
        with col1:
            pdf_student = create_pdf(st.session_state["exam_data"], custom_title, mode="student")
            st.download_button(
                label="📄 下載學生版 (題目卷)",
                data=pdf_student,
                file_name=f"{safe_title}_學生版.pdf",
                mime="application/pdf"
            )
            
        with col2:
            pdf_parent = create_pdf(st.session_state["exam_data"], custom_title, mode="parent")
            st.download_button(
                label="👨‍🏫 下載家長版 (含解析)",
                data=pdf_parent,
                file_name=f"{safe_title}_解答版.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
