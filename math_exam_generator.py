import streamlit as st
import random
import math
from fpdf import FPDF
import os

# 1. 設定頁面配置
st.set_page_config(page_title="全方位數學自動出題系統", layout="wide", page_icon="📝")

# ==========================================
# Part 1: 基礎題目生成邏輯 (Basic Generators)
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
# Part 2: 進階歷屆試題改編 (Advanced Exam Styles)
# ==========================================

def generate_exam_ticket_problem():
    """試題改編：門票/費用優惠問題 (一元一次不等式應用)"""
    # 題目模版：團體票問題
    # 假設原價 p 元，超過 n 人打 d 折
    price = random.choice([100, 200, 250, 300, 500])
    group_limit = random.choice([20, 30, 40, 50])
    discount_off = random.choice([10, 20, 30]) # 10% off = 9折
    discount_rate = (100 - discount_off) / 100
    
    # 設計人數 x，使得「買團體票」比「按人數買」便宜
    # 買團體票價格 = price * group_limit * discount_rate
    # 按人數買價格 = price * x
    # 臨界點： x * price > price * group_limit * discount_rate  => x > group_limit * discount_rate
    
    threshold = math.ceil(group_limit * discount_rate)
    # 讓 x 在臨界點附近，增加混淆
    x_options = [threshold - 2, threshold - 1, threshold + 1, threshold + 2]
    x_val = random.choice(x_options)
    
    q_str = (f"某遊樂園門票每張 {price} 元，團體 {group_limit} 人以上(含)可享 {10-discount_off//10} 折優惠。"
             f"若一個不足 {group_limit} 人的團體，人數至少多少人時，直接購買 {group_limit} 張團體票反而比較划算？")
    
    ans_str = f"{threshold} 人"
    detail = (f"設人數為 $x$。若買團體票較便宜：\n"
              f"${price} \\times x > {price} \\times {group_limit} \\times {discount_rate}$ \n"
              f"$\\Rightarrow x > {group_limit * discount_rate}$，故至少 {threshold} 人。")
    
    return {"topic": "🔥 進階-生活應用(不等式)", "question": q_str, "answer": ans_str, "detail": detail}

def generate_exam_sequence_pattern():
    """試題改編：圖形與規律 (等差數列應用)"""
    # 題目模版：火柴棒/排座椅問題
    # 假設第 1 圖需 a 根，每多一圖加 d 根
    # 常見：正方形排列 (4, 7, 10...) -> a=4, d=3
    # 常見：三角形排列 (3, 5, 7...) -> a=3, d=2
    pattern_type = random.choice(['square', 'tri'])
    
    if pattern_type == 'square':
        shape_name = "正方形"
        a1 = 4
        d = 3
    else:
        shape_name = "三角形"
        a1 = 3
        d = 2
        
    n = random.randint(10, 50)
    q_str = (f"利用火柴棒排列相連的{shape_name}，排 1 個需 {a1} 根，排 2 個需 {a1+d} 根，"
             f"排 3 個需 {a1+2*d} 根... 依此規律，排 {n} 個{shape_name}共需幾根火柴棒？")
    
    ans_val = a1 + (n - 1) * d
    ans_str = f"{ans_val} 根"
    detail = (f"這是首項 $a_1={a1}$，公差 $d={d}$ 的等差數列。\n"
              f"$a_n = a_1 + (n-1)d = {a1} + ({n}-1)\\times{d} = {ans_val}$")

    return {"topic": "🔥 進階-規律探索(數列)", "question": q_str, "answer": ans_str, "detail": detail}

def generate_exam_quadratics_app():
    """試題改編：拋物線與最大值 (二次函數應用)"""
    # 題目模版：拋球高度問題 h(t) = -at^2 + bt + c
    # 設計頂點為整數
    # Vertex at t = -b/(2a)
    t_vertex = random.randint(2, 6)
    max_h = random.randint(20, 100)
    a = random.choice([-1, -2, -5]) # 重力係數相關，簡化為整數
    
    # 頂點式: y = a(t - t_vertex)^2 + max_h
    # 展開: y = a(t^2 - 2*t*tv + tv^2) + max_h
    # y = a*t^2 - 2*a*tv*t + (a*tv^2 + max_h)
    
    b = -2 * a * t_vertex
    c = a * (t_vertex ** 2) + max_h
    
    # 隨機問法：最大高度 或 幾秒後落地(較難，先問最大高度)
    q_str = (f"向上投擲一球，經 $t$ 秒後的高度 $h$ 公尺滿足函數關係式： "
             f"$h(t) = {a}t^2 + {b}t + {c}$。請問此球在發射後第幾秒達到最高點？該高度為何？")
    
    ans_str = f"{t_vertex} 秒，{max_h} 公尺"
    detail = (f"配方法求頂點：\n"
              f"提出係數 ${a}$，配成 $y = {a}(t - {t_vertex})^2 + {max_h}$。\n"
              f"當 $t={t_vertex}$ 時，有最大值 {max_h}。")

    return {"topic": "🔥 進階-二次函數應用", "question": q_str, "answer": ans_str, "detail": detail}

def generate_exam_profit_problem():
    """試題改編：利潤問題 (二元一次聯立 或 一元一次應用)"""
    # 題目：已知 A 產品成本 x，B 產品成本 y
    cost_a = random.randint(20, 100) * 10
    cost_b = random.randint(20, 100) * 10
    
    profit_rate_a = random.choice([0.2, 0.3, 0.4])
    profit_rate_b = random.choice([0.1, 0.2, 0.5])
    
    sell_a = int(cost_a * (1 + profit_rate_a))
    sell_b = int(cost_b * (1 + profit_rate_b))
    
    count_a = random.randint(5, 20)
    count_b = random.randint(5, 20)
    
    total_cost = cost_a * count_a + cost_b * count_b
    total_sell = sell_a * count_a + sell_b * count_b
    total_profit = total_sell - total_cost
    
    q_str = (f"商店買進 A、B 兩項商品共 {count_a + count_b} 件，已知 A 進價 {cost_a} 元，B 進價 {cost_b} 元。"
             f"若 A 商品依進價加 {int(profit_rate_a*10)}成 賣出，B 商品依進價加 {int(profit_rate_b*10)}成 賣出，"
             f"且最後總共賣得 {total_sell} 元。請問 A、B 各賣出幾件？(已知 A 賣出 {count_a} 件)")
             
    # 這裡故意把 A 的數量給出來當作已知條件，改成問 B 或是問總利潤，增加變化
    # 為了讓題目更有邏輯，我們設計成「求解聯立」的文字敘述
    
    # 重寫題目：隱藏件數，給總件數與總賣價
    q_str = (f"商店買進 A、B 兩項商品共 {count_a + count_b} 件。已知 A 進價 {cost_a} 元，B 進價 {cost_b} 元。"
             f"A 依進價加 {int(profit_rate_a*10)}成 訂價，B 依進價加 {int(profit_rate_b*10)}成 訂價。"
             f"全部賣出後總營收為 {total_sell} 元。請問 A 商品買進多少件？")
             
    ans_str = f"{count_a} 件"
    detail = (f"設 A 有 $x$ 件，B 有 ${count_a + count_b} - x$ 件。\n"
              f"A 售價=${sell_a}$，B 售價=${sell_b}$。\n"
              f"方程式：${sell_a}x + {sell_b}({count_a + count_b} - x) = {total_sell}$，解得 $x={count_a}$。")
    
    return {"topic": "🔥 進階-銷售利潤問題", "question": q_str, "answer": ans_str, "detail": detail}


# ==========================================
# Part 3: 題型策略地圖 (Updated Mapping)
# ==========================================

TOPIC_MAPPING = {
    # 基礎區
    "基礎 - 數與量 (運算/科學記號)": generate_number_basic,
    "基礎 - 代數 (方程式/不等式)": generate_linear_algebra_basic,
    "基礎 - 幾何 (角度/邊長)": generate_geometry_basic,
    # 進階區 (新增)
    "🔥 進階 - 生活應用 (門票優惠)": generate_exam_ticket_problem,
    "🔥 進階 - 規律探索 (圖形數列)": generate_exam_sequence_pattern,
    "🔥 進階 - 二次函數 (拋物線應用)": generate_exam_quadratics_app,
    "🔥 進階 - 商業應用 (利潤問題)": generate_exam_profit_problem
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
# Part 4: PDF 匯出功能
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
    
    for idx, item in enumerate(exam_data):
        clean_q = item['question'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\times', 'x').replace('\\div', '÷').replace('\\le', '<=')
        clean_a = item['answer'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\pi', 'π').replace('\\times', 'x')
        
        # 標題縮寫
        topic_show = item['topic']
        if "🔥" in topic_show:
            topic_show = "進階"
        elif "-" in topic_show:
            topic_show = topic_show.split('-')[1]
            
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

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# Part 5: Streamlit UI
# ==========================================

def main():
    st.title("📝 全方位國中數學出題系統 (Pro版)")
    st.markdown("### 包含基礎觀念與 **🔥 歷屆試題改編**")
    st.markdown("---")

    all_topics = list(TOPIC_MAPPING.keys())
    if "selected_topics" not in st.session_state:
        st.session_state.selected_topics = all_topics[:4] # 預設選一些基礎跟進階

    def toggle_all():
        if st.session_state.use_all_topics:
            st.session_state.selected_topics = all_topics
        else:
            st.session_state.selected_topics = []

    with st.sidebar:
        st.header("⚙️ 試卷設定")
        custom_title = st.text_input("試卷標題", value="會考衝刺練習")
        
        st.checkbox("全選所有單元", key="use_all_topics", on_change=toggle_all)
        
        selected_topics = st.multiselect(
            "選擇單元 (可複選)",
            options=all_topics,
            key="selected_topics"
        )
        
        num_questions = st.slider("題目數量", 5, 50, 10)
        generate_btn = st.button("🚀 建立新考卷", type="primary")
        
        st.info("🔥 進階題型說明：\n包含門票優惠問題、圖形數列規律、二次函數投擲問題、利潤銷售問題。這些都是歷屆會考常見的素養題型。")

    if "exam_data" not in st.session_state:
        st.session_state["exam_data"] = []
    
    if generate_btn:
        if not selected_topics:
            st.error("請至少選擇一個單元！")
        else:
            with st.spinner("正在生成素養題與運算題..."):
                st.session_state["exam_data"] = generate_exam_data(selected_topics, num_questions)
            st.success(f"成功生成 {len(st.session_state['exam_data'])} 題！")

    if st.session_state["exam_data"]:
        st.subheader(f"👀 {custom_title} - 試題預覽")
        
        for i, q in enumerate(st.session_state["exam_data"][:3]):
            with st.expander(f"Q{i+1} [{q['topic']}]"):
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
            st.download_button("📄 下載學生版", pdf_student, f"{safe_title}_學生版.pdf", "application/pdf")
        with col2:
            pdf_parent = create_pdf(st.session_state["exam_data"], custom_title, mode="parent")
            st.download_button("👨‍🏫 下載家長版", pdf_parent, f"{safe_title}_解答版.pdf", "application/pdf")

if __name__ == "__main__":
    main()
