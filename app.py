
import streamlit as st
from datetime import date, datetime, timedelta
import math
import hashlib

try:
    from lunardate import LunarDate
except ImportError:
    LunarDate = None

st.set_page_config(
    page_title="Vận Số Hằng Ngày - Ất Hợi 1995",
    page_icon="🔮",
    layout="wide",
)

# =========================
# THÔNG TIN CỐ ĐỊNH
# =========================
BIRTH_LUNAR_DAY = 1
BIRTH_LUNAR_MONTH = 10
BIRTH_LUNAR_YEAR = 1995
ZODIAC = "Ất Hợi"
ELEMENT = "Sơn Đầu Hỏa (nạp âm: Sơn Đầu Hỏa)"
# Lưu ý: đây là app tham khảo văn hóa/tử vi, không phải công cụ dự đoán kết quả xổ số.

# Can Chi
HEAVENLY_STEMS = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
EARTHLY_BRANCHES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]

# Ngũ hành theo thiên can / địa chi
STEM_ELEMENT = {
    "Giáp": "Mộc", "Ất": "Mộc", "Bính": "Hỏa", "Đinh": "Hỏa",
    "Mậu": "Thổ", "Kỷ": "Thổ", "Canh": "Kim", "Tân": "Kim",
    "Nhâm": "Thủy", "Quý": "Thủy"
}
BRANCH_ELEMENT = {
    "Tý": "Thủy", "Sửu": "Thổ", "Dần": "Mộc", "Mão": "Mộc",
    "Thìn": "Thổ", "Tỵ": "Hỏa", "Ngọ": "Hỏa", "Mùi": "Thổ",
    "Thân": "Kim", "Dậu": "Kim", "Tuất": "Thổ", "Hợi": "Thủy"
}

ELEMENT_CYCLE = ["Mộc", "Hỏa", "Thổ", "Kim", "Thủy"]

# Tương sinh: a -> b nghĩa là a sinh b
GENERATES = {"Mộc": "Hỏa", "Hỏa": "Thổ", "Thổ": "Kim", "Kim": "Thủy", "Thủy": "Mộc"}
CONTROLS = {"Mộc": "Thổ", "Thổ": "Thủy", "Thủy": "Hỏa", "Hỏa": "Kim", "Kim": "Mộc"}

# 12 giờ địa chi
TIME_BRANCHES = [
    ("Tý", "23:00–00:59"), ("Sửu", "01:00–02:59"), ("Dần", "03:00–04:59"),
    ("Mão", "05:00–06:59"), ("Thìn", "07:00–08:59"), ("Tỵ", "09:00–10:59"),
    ("Ngọ", "11:00–12:59"), ("Mùi", "13:00–14:59"), ("Thân", "15:00–16:59"),
    ("Dậu", "17:00–18:59"), ("Tuất", "19:00–20:59"), ("Hợi", "21:00–22:59"),
]

# =========================
# HÀM LỊCH
# =========================
def lunar_from_solar(d):
    if LunarDate is None:
        return None
    try:
        return LunarDate.fromSolarDate(d.year, d.month, d.day)
    except Exception:
        return None

def can_chi_year(year):
    return HEAVENLY_STEMS[(year - 4) % 10] + " " + EARTHLY_BRANCHES[(year - 4) % 12]

def can_chi_month(lunar_year, lunar_month):
    # Tháng Giêng là Dần. Can tháng phụ thuộc can năm.
    year_stem_index = (lunar_year - 4) % 10
    first_month_stem = {0:2, 5:2, 1:4, 6:4, 2:6, 7:6, 3:8, 8:8, 4:0, 9:0}[year_stem_index]
    stem_index = (first_month_stem + lunar_month - 1) % 10
    branch_index = (lunar_month + 1) % 12
    return HEAVENLY_STEMS[stem_index] + " " + EARTHLY_BRANCHES[branch_index]

def can_chi_day(d):
    # Công thức Can-Chi ngày theo JDN, dùng mốc phổ biến:
    # Can index = (JDN + 9) % 10, Chi index = (JDN + 1) % 12
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12*a - 3
    jdn = d.day + (153*m + 2)//5 + 365*y + y//4 - y//100 + y//400 - 32045
    stem = HEAVENLY_STEMS[(jdn + 9) % 10]
    branch = EARTHLY_BRANCHES[(jdn + 1) % 12]
    return stem + " " + branch

def parse_can_chi(cc):
    parts = cc.split()
    return parts[0], parts[1]

# =========================
# CHẤM ĐIỂM
# =========================
def relation_score(birth_branch, day_branch, birth_element, day_element):
    score = 0
    reasons = []

    if day_branch == birth_branch:
        score += 8
        reasons.append("Ngày đồng chi với tuổi Hợi.")
    # Tam hợp Hợi–Mão–Mùi
    elif {birth_branch, day_branch} <= {"Hợi", "Mão", "Mùi"}:
        score += 10
        reasons.append("Ngày có quan hệ tam hợp với Hợi.")
    # Lục hợp Hợi–Dần
    elif {birth_branch, day_branch} == {"Hợi", "Dần"}:
        score += 9
        reasons.append("Ngày có quan hệ lục hợp với Hợi.")
    # Lục xung Hợi–Tỵ
    elif {birth_branch, day_branch} == {"Hợi", "Tỵ"}:
        score -= 14
        reasons.append("Ngày Tỵ xung với Hợi.")
    # Hợi hại Thân
    elif {birth_branch, day_branch} == {"Hợi", "Thân"}:
        score -= 8
        reasons.append("Ngày Thân có quan hệ hại với Hợi.")

    if day_element == birth_element:
        score += 5
        reasons.append("Ngũ hành ngày đồng hành với mệnh tham khảo.")
    elif GENERATES.get(day_element) == birth_element:
        score += 8
        reasons.append("Ngũ hành ngày sinh cho mệnh.")
    elif GENERATES.get(birth_element) == day_element:
        score += 3
        reasons.append("Mệnh sinh cho ngũ hành ngày.")
    elif CONTROLS.get(day_element) == birth_element:
        score -= 8
        reasons.append("Ngũ hành ngày khắc mệnh.")
    elif CONTROLS.get(birth_element) == day_element:
        score -= 3
        reasons.append("Mệnh khắc ngũ hành ngày.")

    return score, reasons

def deterministic_bonus(d, salt):
    # Tạo dao động nhỏ, ổn định theo ngày; không phải xác suất trúng.
    raw = f"{d.isoformat()}|{salt}|{BIRTH_LUNAR_YEAR}"
    h = hashlib.sha256(raw.encode()).hexdigest()
    return (int(h[:8], 16) % 11) - 5

def daily_analysis(d):
    lunar = lunar_from_solar(d)
    year_cc = can_chi_year(d.year)
    day_cc = can_chi_day(d)
    day_stem, day_branch = parse_can_chi(day_cc)

    # Tuổi Ất Hợi: thiên can Ất/Mộc, địa chi Hợi/Thủy.
    birth_branch = "Hợi"
    birth_element = "Mộc"  # dùng Mộc làm mệnh hành tham khảo cho phần chấm tương sinh
    day_element = STEM_ELEMENT[day_stem]

    rel, reasons = relation_score(birth_branch, day_branch, birth_element, day_element)
    base = 65 + rel + deterministic_bonus(d, "base")
    total = max(35, min(95, base))

    tài_lộc = max(30, min(95, total + deterministic_bonus(d, "money")))
    công_việc = max(30, min(95, total + deterministic_bonus(d, "work")))
    tình_cảm = max(30, min(95, total + deterministic_bonus(d, "love")))
    gia_đạo = max(30, min(95, total + deterministic_bonus(d, "family")))
    may_mắn = max(30, min(95, total + deterministic_bonus(d, "luck")))
    rủi_ro = max(10, min(85, 100 - total + 10 + abs(deterministic_bonus(d, "risk"))))

    if total >= 80:
        label = "RẤT TỐT"
        advice = "Ngày có nhiều chỉ báo thuận lợi theo mô hình tham khảo. Phù hợp để ưu tiên việc quan trọng, nhưng vẫn nên quyết định dựa trên thực tế."
    elif total >= 68:
        label = "KHÁ TỐT"
        advice = "Ngày tương đối thuận. Nên chủ động ở những việc đã chuẩn bị kỹ và tránh quyết định nóng vội."
    elif total >= 55:
        label = "TRUNG BÌNH"
        advice = "Ngày ở mức cân bằng. Tập trung việc chắc chắn, hạn chế mạo hiểm và giữ kỷ luật tài chính."
    else:
        label = "THẬN TRỌNG"
        advice = "Ngày có một số chỉ báo bất lợi. Ưu tiên an toàn, kiểm tra kỹ thông tin và tránh quyết định tài chính bốc đồng."

    lucky_branches = ["Dần", "Mão", "Mùi"] if day_branch in ["Hợi", "Dần", "Mão", "Mùi"] else ["Dần", "Mão", "Mùi"]
    # Các số tham khảo được sinh ổn định từ ngày, không tuyên bố dự đoán kết quả.
    candidates = []
    seed = int(hashlib.sha256(f"{d.isoformat()}|{year_cc}|{day_cc}|AT-HOI-1995".encode()).hexdigest(), 16)
    used = set()
    for i in range(20):
        n = (seed // (i + 1) + i * 37 + total * 13) % 100
        n = int(n)
        if n not in used:
            used.add(n)
            candidates.append(f"{n:02d}")
    # Chọn 5 số từ danh sách ổn định
    numbers = candidates[:5]
    priority = candidates[5:7]

    good_hours = []
    for branch, hours in TIME_BRANCHES:
        if branch in lucky_branches:
            good_hours.append(f"{branch} ({hours})")
    if not good_hours:
        good_hours = [TIME_BRANCHES[(d.day + i) % 12][0] + " (" + TIME_BRANCHES[(d.day + i) % 12][1] + ")" for i in range(2)]

    return {
        "date": d,
        "lunar": lunar,
        "year_cc": year_cc,
        "month_cc": can_chi_month(lunar.year, lunar.month) if lunar else "—",
        "day_cc": day_cc,
        "day_element": day_element,
        "total": total,
        "label": label,
        "advice": advice,
        "tài_lộc": tài_lộc,
        "công_việc": công_việc,
        "tình_cảm": tình_cảm,
        "gia_đạo": gia_đạo,
        "may_mắn": may_mắn,
        "rủi_ro": rủi_ro,
        "reasons": reasons,
        "good_hours": good_hours,
        "numbers": numbers,
        "priority": priority,
    }

# =========================
# GIAO DIỆN
# =========================
st.title("🔮 HỆ THỐNG VẬN SỐ HẰNG NGÀY")
st.caption("Dành cho người sinh ngày 01/10/1995 âm lịch – Ất Hợi. Nội dung mang tính tham khảo văn hóa/giải trí, không đảm bảo dự đoán xổ số.")

with st.sidebar:
    st.header("👤 Thông tin cá nhân")
    st.write("**Ngày sinh âm lịch:** 01/10/1995")
    st.write("**Tuổi:** Ất Hợi")
    st.write("**Mục tiêu:** Đánh giá vận số theo từng ngày")
    st.divider()
    selected = st.date_input("📅 Chọn ngày muốn xem", value=date.today(), format="DD/MM/YYYY")
    show_numbers = st.checkbox("Hiện nhóm số tham khảo", value=True)
    st.info("Phần số chỉ là tham khảo giải trí. Không có công thức nào đảm bảo trúng xổ số.")

result = daily_analysis(selected)

# Header
col1, col2, col3 = st.columns([1.2, 1.2, 1])
with col1:
    st.metric("⭐ Tổng vận", f"{result['total']}/100")
with col2:
    st.metric("📅 Đánh giá", result["label"])
with col3:
    if result["lunar"]:
        l = result["lunar"]
        st.metric("🌙 Âm lịch", f"{l.day:02d}/{l.month:02d}/{l.year}")

st.subheader(f"📜 Luận ngày {selected.strftime('%d/%m/%Y')}")

if result["lunar"]:
    st.write(
        f"**Năm:** {result['year_cc']}  •  "
        f"**Tháng âm:** {result['month_cc']}  •  "
        f"**Ngày:** {result['day_cc']}  •  "
        f"**Ngũ hành ngày:** {result['day_element']}"
    )

st.success(result["advice"])

cols = st.columns(6)
metrics = [
    ("💰 Tài lộc", result["tài_lộc"]),
    ("💼 Công việc", result["công_việc"]),
    ("❤️ Tình cảm", result["tình_cảm"]),
    ("🏠 Gia đạo", result["gia_đạo"]),
    ("🍀 May mắn", result["may_mắn"]),
    ("⚠️ Rủi ro", result["rủi_ro"]),
]
for c, (name, value) in zip(cols, metrics):
    c.metric(name, f"{value}/100")

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("🧭 Các dấu hiệu chính")
    if result["reasons"]:
        for reason in result["reasons"]:
            st.write("• " + reason)
    else:
        st.write("• Ngày không có quan hệ nổi bật trong mô hình.")
with right:
    st.subheader("⏰ Khung giờ thuận tham khảo")
    for h in result["good_hours"]:
        st.write("• " + h)

st.divider()

st.subheader("🎲 Vận may lô đề – CHỈ THAM KHẢO")
st.warning(
    "Các con số dưới đây được tạo từ mô hình tham khảo theo ngày và thông tin tuổi, "
    "không phải dự đoán kết quả xổ số và không làm tăng xác suất trúng."
)

if show_numbers:
    ncols = st.columns(5)
    for c, n in zip(ncols, result["numbers"]):
        c.metric("Số tham khảo", n)

    st.write("**⭐ Nhóm ưu tiên tham khảo:** " + " – ".join(result["priority"]))
    st.caption("Không nên xem nhóm số này là tín hiệu chắc thắng hoặc căn cứ để tăng tiền cược.")

st.divider()

st.subheader("📊 Lịch xem nhanh 7 ngày")
rows = []
for i in range(7):
    d = selected + timedelta(days=i)
    r = daily_analysis(d)
    rows.append({
        "Ngày": d.strftime("%d/%m/%Y"),
        "Âm lịch": f"{r['lunar'].day:02d}/{r['lunar'].month:02d}" if r["lunar"] else "—",
        "Can–Chi ngày": r["day_cc"],
        "Tổng vận": r["total"],
        "Đánh giá": r["label"],
        "Tài lộc": r["tài_lộc"],
        "Công việc": r["công_việc"],
        "May mắn": r["may_mắn"],
    })

st.dataframe(rows, use_container_width=True, hide_index=True)

st.divider()

st.subheader("📌 Nguyên tắc sử dụng")
st.write(
    """
    1. Đây là công cụ tham khảo tử vi/phong thủy và giải trí.
    2. Điểm số được tổng hợp từ ngày sinh, Can–Chi, ngũ hành và quan hệ địa chi.
    3. Phần xổ số chỉ tạo nhóm số tham khảo ổn định theo ngày; không có khả năng biết trước kết quả quay số.
    4. Không dùng điểm vận số để quyết định vay tiền, tăng tiền cược hoặc đánh cược vượt khả năng tài chính.
    """
)

st.caption("Phiên bản 1.0 – Vận Số Hằng Ngày | Streamlit")
