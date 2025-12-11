import streamlit as st
import random
import math
from fpdf import FPDF
import os
import tempfile  # 新增：用於處理圖片暫存

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
# Part 2: 進階歷屆試題改編 (Advanced Exam Styles - Multi-Scenario)
# ==========================================

def generate_advanced_inequality():
    """進階-生活應用(不等式)：隨機選擇不同場景"""
    scenario = random.choice(['ticket', 'mobile_plan', 'saving_goal'])
    
    if scenario == 'ticket':
        # 情境 A: 門票優惠 (原版)
        price = random.choice([100, 200, 250, 300, 500])
        group_limit = random.choice([20, 30, 40, 50])
        discount_off = random.choice([10, 20, 30]) 
        discount_rate = (100 - discount_off) / 100
        threshold = math.ceil(group_limit * discount_rate)
        
        q_str = (f"遊樂園門票每張 {price} 元，{group_limit} 人以上(含)團體票打 {10-discount_off//10} 折。"
                 f"若團體不足 {group_limit} 人，人數至少多少時，直接買 {group_limit} 張團體票反而划算？")
        ans_str = f"{threshold} 人"
        detail = f"設人數 x。$x \\times {price} > {group_limit} \\times {price} \\times {discount_rate}$。"

    elif scenario == 'mobile_plan':
        # 情境 B: 電信資費比較
        # 方案 A: 月租高，通話費低； 方案 B: 月租低，通話費高
        base_a = random.randint(300, 600)
        rate_a = random.randint(2, 4)
        base_b = random.randint(100, 200)
        rate_b = random.randint(6, 9)
        
        # 臨界點： base_a + rate_a * x < base_b + rate_b * x
        # base_a - base_b < (rate_b - rate_a) * x
        diff_base = base_a - base_b
        diff_rate = rate_b - rate_a
        threshold = math.ceil(diff_base / diff_rate)
        
        q_str = (f"電信方案 A 月租費 {base_a} 元，每分鐘通話 {rate_a} 元；"
                 f"方案 B 月租費 {base_b} 元，每分鐘通話 {rate_b} 元。"
                 f"當每月通話時間超過多少分鐘時，選擇方案 A 會比較划算？")
        ans_str = f"{threshold} 分鐘"
        detail = f"設通話 x 分鐘。${base_a} + {rate_a}x < {base_b} + {rate_b}x$，移項解 x。"

    else:
        # 情境 C: 存錢買東西
        current_money = random.randint(1000, 5000)
        saving_per_week = random.randint(200, 500)
        target_price = random.randint(10000, 20000)
        
        # current + saving * x >= target
        needed = target_price - current_money
        weeks = math.ceil(needed / saving_per_week)
        
        q_str = (f"小明想買一台 {target_price} 元的筆電，他現在有 {current_money} 元，"
                 f"並計畫每週存 {saving_per_week} 元。至少需要幾週後他的存款才足夠買筆電？")
        ans_str = f"{weeks} 週"
        detail = f"設 x 週後。${current_money} + {saving_per_week}x \\ge {target_price}$。"

    return {"topic": "🔥 進階-不等式應用", "question": q_str, "answer": ans_str, "detail": detail}

def generate_advanced_sequence():
    """進階-規律探索(數列)：隨機選擇不同場景"""
    scenario = random.choice(['matchstick', 'auditorium', 'divisibility'])

    if scenario == 'matchstick':
        # 情境 A: 圖形規律 (火柴棒)
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

    elif scenario == 'auditorium':
        # 情境 B: 禮堂座位 (座位數遞增)
        a1 = random.randint(15, 30) # 第一排座位
        d = random.randint(2, 4)    # 每排增加
        row = random.randint(10, 20) # 問第幾排
        
        q_str = (f"表演廳座位區，第一排有 {a1} 個座位，之後每一排都比前一排多 {d} 個座位。"
                 f"請問第 {row} 排有多少個座位？")
        ans_val = a1 + (row - 1) * d
        ans_str = f"{ans_val} 個"
        detail = f"首項 {a1}，公差 {d}，求第 {row} 項。"

    else:
        # 情境 C: 倍數計數 (1~n 之間某數的倍數)
        limit = random.randint(100, 500)
        divisor = random.choice([3, 4, 6, 7, 8])
        remainder = random.randint(1, divisor-1)
        
        q_str = (f"在 1 到 {limit} 的整數中，除以 {divisor} 餘 {remainder} 的數共有幾個？")
        # 數列: remainder, remainder+divisor, ... <= limit
        # an = remainder + (n-1)*divisor <= limit
        # (n-1)*divisor <= limit - remainder
        # n-1 <= (limit - remainder) // divisor
        count = (limit - remainder) // divisor + 1
        ans_str = f"{count} 個"
        detail = f"找出數列：{remainder}, {remainder+divisor}, {remainder+2*divisor}... 利用通項公式逆推項數。"

    return {"topic": "🔥 進階-數列規律", "question": q_str, "answer": ans_str, "detail": detail}

def generate_advanced_quadratics():
    """進階-二次函數應用：隨機選擇不同場景"""
    scenario = random.choice(['projectile', 'area_max', 'revenue_max'])

    if scenario == 'projectile':
        # 情境 A: 拋物線高度 (原版)
        t_vertex = random.randint(2, 5)
        max_h = random.randint(20, 80)
        a = -5 # 重力近似
        b = -2 * a * t_vertex
        c = a * t_vertex**2 + max_h
        
        q_str = (f"球被拋出後高度 $h$ 與時間 $t$ 關係為 $h(t) = {a}t^2 + {b}t + {c}$。"
                 f"請問第幾秒達到最高點？最高高度為多少？")
        ans_str = f"{t_vertex} 秒，{max_h} 公尺"
        detail = "配方法化為頂點式 $y = a(x-h)^2 + k$，頂點即為極值。"

    elif scenario == 'area_max':
        # 情境 B: 圍籬笆面積最大化
        # 周長固定，求矩形最大面積
        # 周長 P = 2(L+W), L+W = P/2 = S. Area = L*W = L*(S-L)
        s_half = random.randint(10, 40) * 2 # 半周長，偶數好算
        perimeter = s_half * 2
        # Max area when L = W = s_half / 2
        side = s_half // 2
        max_area = side * side
        
        q_str = (f"農夫想用長 {perimeter} 公尺的籬笆圍成一個長方形菜園(四邊都圍)。"
                 f"請問圍出的最大面積是多少平方公尺？")
        ans_str = f"{max_area} $m^2$"
        detail = f"設長 x，寬 {s_half}-x。面積 $A(x) = x({s_half}-x)$，配方求最大值(正方形時)。"

    else:
        # 情境 C: 定價與營收
        # 原價 p0, 銷量 q0。每漲價 x 元，銷量少 y 個。
        p0 = random.randint(50, 100)
        q0 = random.randint(200, 400)
        delta_p = 1 # 漲 1 元
        delta_q = random.randint(2, 5) # 少 delta_q 個
        
        # R(x) = (p0 + x)(q0 - delta_q * x)
        # 頂點 x = (q0/delta_q - p0) / 2
        # 為了讓數字漂亮，我們設計一下
        # 讓 (q0/delta_q - p0) 是偶數
        
        # 重新生成好算的數字
        delta_q = 2
        p0 = 100
        x_target = random.randint(10, 30) # 預設最佳漲價金額
        # 為了讓頂點在 x_target，我們回推 q0
        # x_vertex = (q0/2 - 100) / 2 = x_target -> q0/2 - 100 = 2*x_target -> q0 = 2*(2*x_target + 100)
        q0 = 2 * (2 * x_target + 100)
        
        max_rev = (p0 + x_target) * (q0 - delta_q * x_target)
        
        q_str = (f"某商品單價 {p0} 元時，可賣出 {q0} 個。若單價每調漲 1 元，銷量會減少 {delta_q} 個。"
                 f"請問定價應調漲多少元，才能獲得最大總營收？(營收=單價x銷量)")
        ans_str = f"{x_target} 元"
        detail = f"設調漲 x 元。營收 $R(x) = ({p0}+x)({q0}-{delta_q}x)$，展開配方求極值。"

    return {"topic": "🔥 進階-二次函數極值", "question": q_str, "answer": ans_str, "detail": detail}

def generate_advanced_system():
    """進階-聯立方程式應用：隨機選擇不同場景"""
    scenario = random.choice(['profit', 'age', 'speed'])

    if scenario == 'profit':
        # 情境 A: 買賣利潤 (原版)
        cost_a = random.randint(20, 50) * 10
        cost_b = random.randint(20, 50) * 10
        count_a = random.randint(5, 15)
        count_b = random.randint(5, 15)
        total_items = count_a + count_b
        # 售價
        sell_a = int(cost_a * 1.3)
        sell_b = int(cost_b * 1.2)
        total_rev = sell_a * count_a + sell_b * count_b
        
        q_str = (f"商店買進A、B兩商品共{total_items}件。A定價{sell_a}元，B定價{sell_b}元。"
                 f"全部賣完後總營收{total_rev}元。請問A商品有幾件？")
        ans_str = f"{count_a} 件"
        detail = f"設A有x件，B有({total_items}-x)件。${sell_a}x + {sell_b}({total_items}-x) = {total_rev}$。"

    elif scenario == 'age':
        # 情境 B: 父子年齡問題
        # 設現在子 x，父 y。 y = k1 * x + b1.  (y+n) = k2 * (x+n)
        son_now = random.randint(10, 15)
        diff = random.randint(20, 30)
        father_now = son_now + diff
        
        # 找一個未來/過去的時間點 n，使倍數是整數
        # 簡單設計：現在父是子 k 倍 (不一定整數)，n年後是 2 倍
        # (father_now + n) = 2 * (son_now + n)
        # father + n = 2son + 2n -> n = father - 2son
        n = father_now - 2 * son_now
        
        if n > 0:
            time_str = f"{n} 年後"
            rel_str = "2 倍"
        elif n < 0:
            time_str = f"{abs(n)} 年前"
            rel_str = "2 倍"
        else:
            # n=0 特殊狀況，改別的題目邏輯
            n = 5
            father_future = father_now + n
            son_future = son_now + n
            # 這裡改成問和差
            sum_age = father_now + son_now
            q_str = f"父子現在年齡和為 {sum_age} 歲。{n} 年後，父親年齡是兒子的 {father_future/son_future:.1f} 倍(非整數)。求父現年？"
            # 避免小數倍數太難，我們直接回傳簡單版
            q_str = f"父親比兒子大 {diff} 歲，{n} 年後父親年齡是兒子的 {(father_now+n)//(son_now+n)} 倍。求兒子現年？"
            # 重新計算倍數確保整數
            son_now = 10
            father_now = 40 # diff 30
            n = 20 # son 30, father 60 (2倍)
            diff = 30
            
        q_str = f"父親比兒子大 {diff} 歲。{abs(n)} 年後，父親年齡剛好是兒子的 2 倍。請問兒子現在幾歲？"
        ans_str = f"{son_now} 歲"
        detail = f"設子 x 歲，父 (x+{diff}) 歲。方程式：$(x+{diff}) + {n} = 2(x + {n})$。"

    else:
        # 情境 C: 順流逆流 (速率問題)
        # 船速 v_boat, 水速 v_water
        v_water = random.randint(2, 5)
        v_boat = random.randint(15, 25)
        dist = random.randint(30, 60) * 2 # 確保距離夠長
        
        # 順流速度 = v_boat + v_water
        # 逆流速度 = v_boat - v_water
        down_speed = v_boat + v_water
        up_speed = v_boat - v_water
        
        q_str = (f"一艘船在河中行駛，順流而下時速率為每小時 {down_speed} 公里，"
                 f"逆流而上時速率為每小時 {up_speed} 公里。請問水流速率為多少？")
        ans_str = f"{v_water} km/hr"
        detail = "設船速 x，水速 y。則 $\\begin{cases} x+y = " + str(down_speed) + " \\\\ x-y = " + str(up_speed) + " \\end{cases}$，解聯立求 y。"

    return {"topic": "🔥 進階-聯立方程式應用", "question": q_str, "answer": ans_str, "detail": detail}


# ==========================================
# Part 3: 題型策略地圖 (Updated Mapping)
# ==========================================

TOPIC_MAPPING = {
    # 基礎區
    "基礎 - 數與量 (運算/科學記號)": generate_number_basic,
    "基礎 - 代數 (方程式/不等式)": generate_linear_algebra_basic,
    "基礎 - 幾何 (角度/邊長)": generate_geometry_basic,
    # 進階區 (現在每個都會隨機出不同情境)
    "🔥 進階 - 生活應用 (不等式)": generate_advanced_inequality,
    "🔥 進階 - 規律探索 (數列)": generate_advanced_sequence,
    "🔥 進階 - 二次函數 (極值應用)": generate_advanced_quadratics,
    "🔥 進階 - 商業/速率 (聯立應用)": generate_advanced_system
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
    for idx, item in enumerate(exam_data):
        clean_q = item['question'].replace('$', '').replace('\\frac', '').replace('{', '').replace('}', '/').replace('\\times', 'x').replace('\\div', '÷').replace('\\le', '<=').replace('\\ge', '>=')
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

    # 2. 圖片試題區 (新增功能)
    if uploaded_images:
        pdf.add_page() # 新起一頁
        # 使用粗體或大標題
        if font_ready: pdf.set_font("TaipeiSans", '', 16)
        pdf.cell(0, 10, "--- 圖片試題區 ---", ln=True, align='C')
        pdf.ln(5)
        
        for img_file in uploaded_images:
            try:
                # 在雲端環境中，fpdf 需要實體檔案路徑，因此使用 tempfile
                img_file.seek(0) # 確保從頭讀取
                
                # 判斷副檔名
                file_ext = img_file.name.split('.')[-1].lower()
                if file_ext not in ['jpg', 'jpeg', 'png']:
                    file_ext = 'png' # 預設

                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                    tmp.write(img_file.read())
                    tmp_path = tmp.name
                
                # 計算適合的寬度，A4 寬度約 210mm，左右留邊
                # 這裡設定最大寬度 170mm，高度自動保持比例
                pdf.image(tmp_path, w=170)
                pdf.ln(10) # 圖片間的間隔
                
                # 刪除暫存檔
                os.remove(tmp_path)
            except Exception as e:
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 10, f"Error displaying image: {e}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# Part 5: Streamlit UI
# ==========================================

def main():
    st.title("📝 全方位國中數學出題系統 (Pro版)")
    st.markdown("### 包含基礎觀念與 **🔥 歷屆試題改編 (多情境版)**")
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
        
        # 圖片上傳區 (新增)
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
        
        selected_topics = st.multiselect(
            "選擇單元 (可複選)",
            options=all_topics,
            key="selected_topics"
        )
        
        num_questions = st.slider("題目數量", 5, 50, 10)
        generate_btn = st.button("🚀 建立新考卷", type="primary")
        
        st.info("🔥 PRO版特色：\n進階題型內建多種情境，並支援**圖片考題上傳**，直接整合進 PDF 考卷！")

    if "exam_data" not in st.session_state:
        st.session_state["exam_data"] = []
    
    if generate_btn:
        if not selected_topics:
            st.error("請至少選擇一個單元！")
        else:
            with st.spinner("正在生成多變素養題..."):
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
            
        if uploaded_files:
            st.success(f"另有 {len(uploaded_files)} 張圖片考題將合併於 PDF 後方。")

        st.divider()
        safe_title = custom_title.replace(" ", "_")
        col1, col2 = st.columns(2)
        with col1:
            # 傳遞 uploaded_files 給 create_pdf
            pdf_student = create_pdf(st.session_state["exam_data"], custom_title, mode="student", uploaded_images=uploaded_files)
            st.download_button("📄 下載學生版", pdf_student, f"{safe_title}_學生版.pdf", "application/pdf")
        with col2:
            # 傳遞 uploaded_files 給 create_pdf (家長版也附上題目圖，方便對照)
            pdf_parent = create_pdf(st.session_state["exam_data"], custom_title, mode="parent", uploaded_images=uploaded_files)
            st.download_button("👨‍🏫 下載家長版", pdf_parent, f"{safe_title}_解答版.pdf", "application/pdf")

if __name__ == "__main__":
    main()
