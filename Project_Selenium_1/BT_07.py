import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from urllib.parse import quote

# 1) CẤU HÌNH
# Ta sẽ lọc lại để chỉ giữ Đại học Việt Nam.
MAIN_URL = "https://vi.wikipedia.org/wiki/" + quote(
    "Danh sách trường đại học, học viện và cao đẳng tại Việt Nam",
    safe=""
)

HEADERS = {"User-Agent": "Mozilla/5.0"}  # Giả lập trình duyệt thật để tránh bị chặn

# TỪ KHÓA cần loại (KHÔNG lấy cao đẳng, học viện)
BAD_KEYWORDS = ["cao đẳng", "học viện"]

# TỪ KHÓA giúp phát hiện TRƯỜNG NƯỚC NGOÀI
FOREIGN_KEYWORDS = [
    "malaysia","singapore","philippines","indonesia","thailand",
    "china","japan","korea","taiwan","australia","canada","usa","united states",
    "putra","universiti","universitas","university of","international","british",
    "australian","french","german","rmit","fulbright","vinuni"
]

# 2) HÀM LÀM SẠCH & HÀM LỌC

def clean_text(t):
    """Xóa ký tự thừa, bỏ [1], [2], bỏ xuống dòng → trả về text sạch"""
    if not t: return ""
    t = re.sub(r"\[\d+\]", "", t)  # Bỏ các ký hiệu kiểu [1]
    t = t.replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()  # Gom nhiều space thành 1


def extract_code(text):
    """Tách mã trường trong dấu ngoặc, ví dụ: 'ĐH Bách Khoa (BKA)' → 'BKA'"""
    m = re.search(r"\(([^)]+)\)", text)
    return m.group(1).strip() if m else ""


def is_foreign(text):
    """Kiểm tra text có chứa từ khóa nước ngoài hay không"""
    t = text.lower()
    return any(k in t for k in FOREIGN_KEYWORDS)


def is_vietnam_university(name):
    """Giữ lại đúng trường Đại học Việt Nam"""
    t = name.lower().strip()

    # 1) Loại cao đẳng, học viện
    if any(k in t for k in BAD_KEYWORDS):
        return False

    # 2) Loại trường nước ngoài
    if is_foreign(t):
        return False

    # 3) Chỉ nhận tên dạng:
    #    - "Đại học ..."
    #    - "Trường Đại học ..."
    return t.startswith("đại học") or t.startswith("trường đại học")

# 3) TẢI TRANG DANH SÁCH TỪ WIKIPEDIA
print("Tải trang:", MAIN_URL)
resp = requests.get(MAIN_URL, headers=HEADERS)
soup = BeautifulSoup(resp.text, "html.parser")

found = {}  # lưu các trường đã thu thập được (key = tên viết thường)


def add_school(name, url=""):
    """Hàm thêm trường vào danh sách sau khi đã lọc qua nhiều điều kiện"""

    name = clean_text(name)
    if not name:
        return

    # Kiểm tra có phải đại học Việt Nam hay không
    if not is_vietnam_university(name):
        return

    # Nếu URL chứa từ khóa nước ngoài → loại
    if url and is_foreign(url):
        return

    key = name.lower()
    if key not in found:
        found[key] = {
            "Tên trường": name,
            "Mã trường": extract_code(name),
            "URL Wikipedia": url,
            "Website": "",
            "Hiệu trưởng": ""
        }

# 4) QUÉT BẢNG WIKITABLE (cột 1 là tên trường)
print("Đang quét bảng danh sách...")
for table in soup.find_all("table", class_="wikitable"):
    for row in table.find_all("tr")[1:]:  # bỏ dòng tiêu đề
        cols = row.find_all("td")
        if not cols:
            continue

        name = clean_text(cols[0].get_text())
        a = cols[0].find("a", href=True)
        url = "https://vi.wikipedia.org" + a["href"] if a else ""

        add_school(name, url)

# 5) QUÉT DANH SÁCH DẠNG <ul> – nhiều trường nằm ở dạng này
print("Đang quét danh sách UL...")
for ul in soup.find_all("ul"):
    for li in ul.find_all("li", recursive=False):
        text = clean_text(li.get_text())
        name = text.split(" - ")[0]  # Lấy phần trước dấu "-" nếu có
        a = li.find("a", href=True)
        url = "https://vi.wikipedia.org" + a["href"] if a else ""

        add_school(name, url)

# 6) VÀO TRANG RIÊNG TỪNG TRƯỜNG → LẤY INFOBOX
def crawl_infobox(url):
    """Vào trang của trường để lấy Website + Hiệu trưởng trong Infobox"""
    info = {"Website": "", "Hiệu trưởng": ""}

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        sp = BeautifulSoup(r.text, "html.parser")

        box = sp.find("table", class_="infobox")
        if not box:
            return info

        for tr in box.find_all("tr"):
            th, td = tr.find("th"), tr.find("td")
            if not th or not td:
                continue

            key = th.text.lower()
            val = clean_text(td.get_text(" "))

            # Lấy website chính thức
            if "website" in key:
                a = td.find("a", href=True)
                info["Website"] = a["href"] if a else val

            # Lấy thông tin hiệu trưởng
            if "hiệu trưởng" in key or "rector" in key:
                info["Hiệu trưởng"] = val

        return info

    except:
        return info


print("Bắt đầu cào từng trường (Infobox)...")
keys = list(found.keys())

for i, key in enumerate(keys, start=1):
    rec = found[key]
    url = rec["URL Wikipedia"]

    if url:
        print(f"[{i}/{len(keys)}] {rec['Tên trường']}")
        info = crawl_infobox(url)
        rec["Website"] = info["Website"]
        rec["Hiệu trưởng"] = info["Hiệu trưởng"]
        time.sleep(0.1)  # Tránh spam, tránh bị chặn

# 7) XUẤT EXCEL
df = pd.DataFrame(found.values())
df = df.drop_duplicates(subset=["Tên trường"]).sort_values("Tên trường")

df.to_excel("Danh_sach_Dai_hoc_VietNam.xlsx", index=False)

print("Số lượng Đại học Việt Nam thu được:", len(df))
print("Save: Danh_sach_Dai_hoc_VietNam.xlsx")
