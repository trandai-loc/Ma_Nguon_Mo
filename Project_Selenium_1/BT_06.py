import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# 1) CẤU HÌNH CƠ BẢN
CHROMEDRIVER_PATH = "D:/MaNguonMo/Project_Selenium_1/chromedriver.exe"
LETTER_RANGE = range(65, 66)

# URL danh sách họa sĩ theo ký tự
BASE_LIST_URL = ("https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22{}%22"
)

# Thời gian nghỉ tránh bị chặn
REQUEST_DELAY = 2.0

# 2) HÀM TIỆN ÍCH: LÀM SẠCH – CHUẨN HÓA

MONTHS = {
    "January":"01","February":"02","March":"03","April":"04","May":"05","June":"06",
    "July":"07","August":"08","September":"09","October":"10","November":"11","December":"12"
}

def normalize_date(text: str) -> str:
    """
    Chuẩn hóa ngày tháng:
    - Trả về dạng YYYY-MM-DD nếu có
    - Chỉ năm YYYY nếu không rõ ngày
    - Tự động nhận dạng nhiều định dạng khác nhau
    """
    if not text:
        return ""
    t = text.strip()

    # Dạng ISO: 1923-03-24
    m_iso = re.match(r"(\d{4})(?:-(\d{2})-(\d{2}))?", t)
    if m_iso:
        yyyy = m_iso.group(1)
        mm = m_iso.group(2)
        dd = m_iso.group(3)
        return f"{yyyy}-{mm}-{dd}" if mm and dd else yyyy

    # Dạng: March 24, 1923
    m_long = re.match(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", t)
    if m_long:
        month = MONTHS.get(m_long.group(1), "")
        day = int(m_long.group(2))
        year = m_long.group(3)
        return f"{year}-{month}-{day:02d}" if month else year

    # Dạng: 24 March 1923
    m_long2 = re.match(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", t)
    if m_long2:
        day = int(m_long2.group(1))
        month = MONTHS.get(m_long2.group(2), "")
        year = m_long2.group(3)
        return f"{year}-{month}-{day:02d}" if month else year

    # Chỉ 1 năm hoặc năm mơ hồ
    m_year = re.search(r"(\d{4})", t)
    return m_year.group(1) if m_year else t


def clean_text(s: str) -> str:
    """Xóa ký tự thừa, dấu xuống dòng, ký hiệu [1], [2]..."""
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\[\d+\]", "", s)  # bỏ footnote
    return s


def infer_nationality_from_intro(text: str) -> str:
    """
    Đoán quốc tịch từ đoạn mô tả đầu tiên.
    Ví dụ: "French painter" → French
    """
    if not text:
        return ""

    m = re.search(r"\b([A-Z][a-z]+)\s+(?:artist|painter)\b", text)
    if m:
        return m.group(1)

    m2 = re.search(r"was an?\s+([A-Z][a-z]+)", text)
    return m2.group(1) if m2 else ""


def extract_born_died_from_paren(text: str) -> tuple[str, str]:
    """
    Tìm phần ngày tháng trong dấu ngoặc: (1909–1977)
    Hoặc (October 5, 1946 – December 7, 2004)
    """
    if not text:
        return "", ""

    # Lấy nội dung trong ngoặc
    m = re.search(r"\(([^)]+)\)", text)
    if not m:
        return "", ""
    content = m.group(1)

    # Tách theo dấu – hoặc -
    parts = re.split(r"\s+[–-]\s+", content)
    if len(parts) == 2:
        birth_raw, death_raw = parts
        return normalize_date(birth_raw), normalize_date(death_raw)

    return normalize_date(content), ""

# 3) KHỞI TẠO SELENIUM
def build_driver() -> webdriver.Chrome:
    """Tạo Selenium Chrome driver (chế độ headless)."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

# 4) THU THẬP LINK TRANG PROFILE
def collect_profile_links() -> list[str]:
    """
    Mở từng trang danh sách theo chữ cái A, B, C...
    Lấy tất cả link họa sĩ.
    """
    links = []
    driver = build_driver()

    try:
        for code in LETTER_RANGE:
            letter = chr(code)
            url = BASE_LIST_URL.format(letter)
            driver.get(url)
            time.sleep(REQUEST_DELAY)

            # Tất cả list painter nằm trong class div-col
            divs = driver.find_elements(By.CLASS_NAME, "div-col")

            for div in divs:
                li_tags = div.find_elements(By.TAG_NAME, "li")
                for li in li_tags:
                    try:
                        a_tag = li.find_element(By.TAG_NAME, "a")
                        href = a_tag.get_attribute("href")

                        # Loại trừ trang disambiguation
                        if href and "/wiki/" in href and not href.endswith("(disambiguation)"):
                            links.append(href)

                    except:
                        continue

            print(f"[{letter}] thu được: {len(links)} link")

    finally:
        driver.quit()

    # Loại trùng
    seen = set()
    unique = []
    for h in links:
        if h not in seen:
            unique.append(h)
            seen.add(h)

    return unique

# 5) TRÍCH XUẤT THÔNG TIN TỪ TRANG PROFILE
def extract_info_from_html(html: str) -> dict:
    """Phân tích HTML bằng BeautifulSoup để lấy Name, Birth, Death, Nationality."""
    soup = BeautifulSoup(html, "html.parser")

    # ----------- Lấy tên (thường nằm trong <h1>) -----------
    name = ""
    h1 = soup.find("h1")
    if h1:
        name = clean_text(h1.get_text())

    birth, death, nationality = "", "", ""

    # ----------- Tìm infobox -----------
    infobox = soup.find("table", class_=re.compile(r"infobox"))
    if infobox:

        # --- Born ---
        th_born = infobox.find("th", string=re.compile(r"\bBorn\b", re.I))
        if th_born:
            td_born = th_born.find_next_sibling("td")
            if td_born:
                born_text = clean_text(td_born.get_text(" ", strip=True))

                # Nếu có <span class="bday"> thì lấy ngày chuẩn
                bday = td_born.find(class_=re.compile(r"\bbday\b"))
                birth = normalize_date(bday.get_text()) if bday else normalize_date(born_text)

        # --- Died ---
        th_died = infobox.find("th", string=re.compile(r"\bDied\b", re.I))
        if th_died:
            td_died = th_died.find_next_sibling("td")
            if td_died:
                death = normalize_date(clean_text(td_died.get_text(" ", strip=True)))

        # --- Nationality ---
        th_nat = infobox.find("th", string=re.compile(r"Nationality|Citizenship", re.I))
        if th_nat:
            td_nat = th_nat.find_next_sibling("td")
            if td_nat:
                nationality = clean_text(td_nat.get_text(" ", strip=True))


    # ----------- Bổ sung nếu infobox thiếu -----------
    if not birth:
        bday_span = soup.find("span", class_=re.compile(r"\bbday\b"))
        if bday_span:
            birth = normalize_date(bday_span.get_text())

    # Dự đoán từ bài mô tả
    if not nationality or not birth:
        first_p = soup.find("p")
        if first_p:
            intro = clean_text(first_p.get_text(" ", strip=True))
            if not birth and not death:
                b, d = extract_born_died_from_paren(intro)
                birth = birth or b
                death = death or d

            if not nationality:
                nationality = infer_nationality_from_intro(intro)

    return {
        "name": name,
        "birth": birth,
        "death": death,
        "nationality": nationality,
    }

# 6) CHẠY TOÀN BỘ QUY TRÌNH
def crawl_painters() -> pd.DataFrame:

    # 1) Thu link
    links = collect_profile_links()
    print(f"Tổng số link duy nhất: {len(links)}\n")

    # 2) Mở từng link và lấy thông tin
    records = []
    driver = build_driver()

    try:
        for idx, url in enumerate(links, 1):
            print(f"[{idx}/{len(links)}] Đang lấy: {url}")

            try:
                driver.get(url)
                time.sleep(REQUEST_DELAY)

                info = extract_info_from_html(driver.page_source)

                # Chỉ thêm nếu có thông tin
                if any(info.values()):
                    records.append(info)

            except Exception as e:
                print(f"Lỗi khi lấy {url}: {e}")
                continue

    finally:
        driver.quit()

    return pd.DataFrame(records)

# 7) MAIN
if __name__ == "__main__":
    df = crawl_painters()
    print(df.head())
    df.to_excel("Painters_1.xlsx", index=False)
    print("Đã lưu: Painters_1.xlsx")
