from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import getpass
import pandas as pd

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

driver.get("https://voz.vn/")
time.sleep(3)

# ✅ Click vào đúng thẻ login bạn chỉ
login_btn = wait.until(EC.element_to_be_clickable(
    (By.CSS_SELECTOR, "a.p-navgroup-link--logIn")
))
login_btn.click()
time.sleep(2)

# Nhập tài khoản & mật khẩu (che bằng getpass)
username = input("Nhập tài khoản: ")
password = getpass.getpass("Nhập mật khẩu: ")

# Nhập vào form login của voz
wait.until(EC.presence_of_element_located((By.NAME, "login"))).send_keys(username)
wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password + Keys.ENTER)
time.sleep(5)

# Truy cập mục đăng bài
driver.get("https://voz.vn/forums/-/post-thread")
time.sleep(3)

# ---- LẤY DỮ LIỆU 1 BÀI VIẾT MỚI NHẤT ----
latest_post = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/threads/']"))
)

title = latest_post.text.strip()
link = latest_post.get_attribute("href")

df = pd.DataFrame([{"title": title, "link": link}])
print("🔥 Bài mới nhất:")
print(df)

df.to_excel("voz_latest_post.xlsx", index=False)
print("✅ Đã lưu file voz_latest_post.xlsx")

driver.quit()
