from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# geckodriver
gecko_path = r"D:/MaNguonMo/Project_Selenium_2/geckodriver.exe"
ser = Service(gecko_path)

# Firefox options
options = webdriver.firefox.options.Options()
options.binary_location = "C:/Program Files/Mozilla Firefox/firefox.exe"
options.headless = False

# Khởi tạo driver
driver = webdriver.Firefox(options=options, service=ser)
driver.maximize_window()

url = "https://nhathuoclongchau.com.vn/thuc-pham-chuc-nang"
driver.get(url)
time.sleep(2)

# Tìm body
body = driver.find_element(By.TAG_NAME, "body")

# CLICK NÚT "Xem thêm sản phẩm"
for k in range(20):  # thử 20 lần (vì trang load động)
    try:
        # Chờ spinner biến mất
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "custom-estore-spinner"))
        )
    except:
        pass

    time.sleep(1)

    # Tìm nút "Xem thêm sản phẩm"
    buttons = driver.find_elements(By.TAG_NAME, "button")

    clicked = False
    for btn in buttons:
        text = btn.text.strip().lower()

        if "xem thêm" in text and "sản phẩm" in text:
            # Cuộn tới nút
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)

            try:
                btn.click()
                clicked = True
                time.sleep(2)
            except:
                pass
            break

    if not clicked:
        break  # không còn nút load thêm → dừng

# CUỘN XUỐNG HẾT TRANG
for _ in range(80):
    body.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.01)

time.sleep(1)

# LẤY DANH SÁCH SẢN PHẨM (Chọn mua)
stt = []
ten = []
gia = []
hinh = []

buttons = driver.find_elements(By.XPATH, "//button[text()='Chọn mua']")
print("Tổng sản phẩm tìm thấy:", len(buttons))

for i, bt in enumerate(buttons, 1):
    # Tìm div cha chứa thông tin sản phẩm
    sp = bt
    for _ in range(3):
        sp = sp.find_element(By.XPATH, "./..")

    # Tên SP
    try:
        tsp = sp.find_element(By.TAG_NAME, "h3").text
    except:
        tsp = ""

    # Giá
    try:
        gsp = sp.find_element(By.CLASS_NAME, "text-blue-5").text
    except:
        gsp = ""

    # Ảnh
    try:
        img = sp.find_element(By.TAG_NAME, "img").get_attribute("src")
    except:
        img = ""

    # Thêm vào list
    if tsp != "":
        stt.append(i)
        ten.append(tsp)
        gia.append(gsp)
        hinh.append(img)

df = pd.DataFrame({
    "STT": stt,
    "Tên sản phẩm": ten,
    "Giá bán": gia,
    "Hình ảnh": hinh
})

df.to_excel("danh_sach_sp_long_chau.xlsx", index=False)

print("DONE! Đã lưu file Excel.")
driver.quit()
