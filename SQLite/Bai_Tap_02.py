import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
import pandas as pd
import re
import os
import sys

######################################################
## CẤU HÌNH
######################################################
DB_FILE = 'Painters_Data.db'
TABLE_NAME = 'painters_info'
LETTER = "F"        # Thay đổi ký tự nếu muốn (ví dụ "A", "B", ...)
MAX_TO_SCRAPE = 50  # Giới hạn số họa sĩ để test; đặt None để lấy tất cả
HEADLESS = False    # True nếu muốn chạy ẩn

# Xóa DB cũ nếu muốn bắt đầu lại
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"Đã xóa file DB cũ: {DB_FILE}")

# Tạo kết nối SQLite
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

create_table_sql = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    name TEXT PRIMARY KEY,
    birth TEXT,
    death TEXT,
    nationality TEXT,
    source_url TEXT
);
"""
cursor.execute(create_table_sql)
conn.commit()

######################################################
## HỖ TRỢ CHO SELENIUM
######################################################
def make_driver(headless=HEADLESS):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
    # Tùy chọn thêm để ổn định
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    # Tùy chọn user-agent (không bắt buộc)
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    try:
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(30)
        return driver
    except WebDriverException as e:
        print("Không thể khởi tạo Chrome WebDriver:", e)
        sys.exit(1)

def safe_quit_driver(driver):
    try:
        if driver:
            driver.quit()
    except:
        pass

######################################################
## II. LẤY DANH SÁCH LINKS HỌA SĨ
######################################################
print("\n--- Bắt đầu Lấy Đường dẫn ---")
all_links = []

driver = make_driver()

try:
    list_url = f"https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22{LETTER}%22"
    print("Mở URL:", list_url)
    driver.get(list_url)
    time.sleep(2)

    # Cách an toàn: tìm phần nội dung chính và lấy các <ul> trực tiếp bên trong .mw-parser-output
    try:
        content = driver.find_element(By.CSS_SELECTOR, "#mw-content-text .mw-parser-output")
        # Lấy tất cả các liên kết trong các <ul> con (li > a)
        ul_items = content.find_elements(By.CSS_SELECTOR, "ul > li > a")
        for a in ul_items:
            try:
                href = a.get_attribute("href")
                title = a.get_attribute("title") or ""
                # Lọc liên kết hợp lệ tới trang wiki (bỏ các anchor, file:, help:, ...)
                if href and "/wiki/" in href and not any(x in href for x in [":", "#"]):
                    all_links.append(href)
            except Exception:
                continue
    except NoSuchElementException:
        print("Không tìm được #mw-content-text .mw-parser-output. Thử lấy tất cả các <a> trong bài.")
        anchors = driver.find_elements(By.CSS_SELECTOR, "a")
        for a in anchors:
            href = a.get_attribute("href")
            if href and "/wiki/" in href and not any(x in href for x in [":", "#"]):
                all_links.append(href)

finally:
    safe_quit_driver(driver)

# Loại bỏ trùng lặp, giữ thứ tự xuất hiện
seen = set()
all_links = [x for x in all_links if not (x in seen or seen.add(x))]

print(f"Hoàn tất lấy đường dẫn. Tổng cộng {len(all_links)} links đã tìm thấy (unique).")

######################################################
## III. CÀO THÔNG TIN VÀ LƯU VÀO SQLITE
######################################################
print("\n--- Bắt đầu Cào và Lưu Trữ Tức thời ---")
driver = make_driver()

count = 0
for link in all_links:
    if MAX_TO_SCRAPE is not None and count >= MAX_TO_SCRAPE:
        break
    count += 1

    name = birth = death = nationality = ""
    try:
        driver.get(link)
        time.sleep(1.2)  # pause ngắn cho trang load

        # 1. Tên họa sĩ (thẻ h1)
        try:
            name = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            name = ""

        # Tìm bảng infobox (nhiều trang dùng class "infobox" hoặc "infobox vcard")
        # Sử dụng XPath linh hoạt cho Born/Died/Nationality
        def extract_field(label):
            try:
                el = driver.find_element(By.XPATH, f"//th[contains(normalize-space(.), '{label}')]/following-sibling::td")
                return el.text.strip()
            except:
                return ""

        raw_born = extract_field("Born")
        raw_died = extract_field("Died")
        raw_nat = extract_field("Nationality")

        # Hàm giúp trích ngày theo nhiều định dạng
        def find_date(text):
            if not text:
                return ""
            # 1) tìm ngày đầy đủ như '12 June 1900' hoặc '12 June, 1900'
            m = re.search(r'\b[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}\b', text)
            if m:
                return m.group(0)
            # 2) tìm năm 4 chữ số (nếu không có ngày-tháng)
            m2 = re.search(r'\b(1[5-9][0-9]{2}|20[0-2][0-9]|190[0-9])\b', text)
            if m2:
                return m2.group(0)
            return text.split('\n')[0].strip()

        birth = find_date(raw_born)
        death = find_date(raw_died)

        # nationality: lấy dòng đầu tiên, loại bỏ chú thích trong ngoặc vuông
        if raw_nat:
            nationality = raw_nat.split('\n')[0].strip()
            nationality = re.sub(r'\[.*?\]', '', nationality).strip()
        else:
            # Nếu không có trường nationality, thử dò trong dòng Born (ví dụ có 'Born: 12 June 1900, Paris, France')
            if raw_born:
                # tìm thành phố, quốc gia sau dấu phẩy cuối cùng
                parts = raw_born.split(',')
                if len(parts) >= 2:
                    possible = parts[-1].strip()
                    # Nếu trông giống tên quốc gia (ký tự chữ), nhận làm nationality
                    if re.match(r'^[A-Za-z\-\s]+$', possible):
                        nationality = possible

        # Ghi vào DB (INSERT OR IGNORE để tránh duplicate theo name)
        insert_sql = f"INSERT OR IGNORE INTO {TABLE_NAME} (name, birth, death, nationality, source_url) VALUES (?, ?, ?, ?, ?);"
        cursor.execute(insert_sql, (name, birth, death, nationality, link))
        conn.commit()
        print(f"[{count}] Lưu: {name} | birth: {birth} | death: {death} | nat: {nationality}")

    except Exception as e:
        print(f"Lỗi khi xử lý {link}: {e}")
        continue

# đóng driver
safe_quit_driver(driver)
print("\nHoàn tất quá trình cào và lưu dữ liệu tức thời.")

######################################################
## IV. TRUY VẤN MẪU VÀ IN KẾT QUẢ
######################################################
print("\n--- Thực thi các truy vấn mẫu ---")
def run_query(q, desc=None, show_n=10):
    if desc:
        print(f"\n-- {desc} --")
    cur = conn.cursor()
    cur.execute(q)
    rows = cur.fetchall()
    # In bảng nhỏ gọn
    for r in rows[:show_n]:
        print(r)
    # Trả DataFrame để dùng tiếp nếu cần
    cols = [d[0] for d in cur.description] if cur.description else []
    try:
        df = pd.DataFrame(rows, columns=cols)
    except:
        df = None
    return df

# A. Thống kê & toàn cục
df_total = run_query(f"SELECT COUNT(*) FROM {TABLE_NAME};", "1) Tổng số họa sĩ đã lưu")
df_head5 = run_query(f"SELECT * FROM {TABLE_NAME} LIMIT 5;", "2) 5 dòng đầu")
df_nations = run_query(f"SELECT DISTINCT nationality FROM {TABLE_NAME};", "3) Các quốc tịch duy nhất", show_n=50)

# B. Lọc & tìm kiếm
df_F = run_query(f"SELECT name FROM {TABLE_NAME} WHERE name LIKE 'F%';", "4) Họa sĩ có tên bắt đầu bằng 'F'")
df_french = run_query(f"SELECT name, nationality FROM {TABLE_NAME} WHERE nationality LIKE '%French%';", "5) Quốc tịch chứa 'French'")
df_no_nat = run_query(f"SELECT name FROM {TABLE_NAME} WHERE nationality = '' OR nationality IS NULL;", "6) Họa sĩ không có quốc tịch")
df_birth_death = run_query(f"SELECT name, birth, death FROM {TABLE_NAME} WHERE birth <> '' AND death <> '';", "7) Họa sĩ có cả ngày sinh và ngày mất", show_n=50)
df_like = run_query(f"SELECT * FROM {TABLE_NAME} WHERE name LIKE '%Fales%';", "8) Tìm tên chứa 'Fales'")

# C. Nhóm & sắp xếp
df_sorted = run_query(f"SELECT name FROM {TABLE_NAME} ORDER BY name COLLATE NOCASE ASC;", "9) Tên sắp xếp A-Z", show_n=50)
df_group = run_query(f"SELECT nationality, COUNT(*) AS cnt FROM {TABLE_NAME} GROUP BY nationality ORDER BY cnt DESC;", "10) Đếm theo quốc tịch", show_n=50)

print("\n--- Kết thúc truy vấn mẫu ---")

# Đóng kết nối cuối cùng
conn.close()
print("\nĐã đóng kết nối cơ sở dữ liệu.")
