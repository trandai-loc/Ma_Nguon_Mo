from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import getpass
import pandas as pd

gecko_path = r"D:/MaNguonMo/Project_Selenium_2/geckodriver.exe"
ser = Service(gecko_path)

options = webdriver.firefox.options.Options()
options.binary_location = "C:/Program Files/Mozilla Firefox/firefox.exe"
options.headless = True

email = input("Nhập tài khoản (email): ")
password_input = getpass.getpass("Nhập mật khẩu (sẽ được ẩn): ")

driver = webdriver.Firefox(options=options, service=ser)
wait = WebDriverWait(driver, 20)

try:
    # === 1. vào thẳng trang login DEV.TO ===
    driver.get("https://dev.to/enter")
    time.sleep(3)

    # === 2. nhập email ===
    email_input = wait.until(EC.presence_of_element_located((By.ID, "user_email")))
    email_input.send_keys(email)

    # === 3. nhập mật khẩu ===
    pwd_input = wait.until(EC.presence_of_element_located((By.ID, "user_password")))
    pwd_input.send_keys(password_input)

    # === 4. bấm login ===
    submit_btn = wait.until(EC.element_to_be_clickable((By.NAME, "commit")))
    submit_btn.click()
    time.sleep(10)

    print("Đăng nhập thành công!")

    # === 5. vào trang chủ để crawl bài mới nhất ===
    driver.get("https://dev.to/")
    time.sleep(5)

    # === 6. lấy 10 bài viết mới nhất ===
    posts = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.crayons-story__hidden-navigation-link"))
    )

    data = []
    for post in posts[:10]:  # chỉ lấy 10 bài đầu
        title = post.text.strip()
        link = post.get_attribute("href")
        data.append({"link": link})

    df = pd.DataFrame(data)
    print("\n10 bài viết mới nhất:")
    print(df)

    df.to_excel("devto_latest_10_posts.xlsx", index=False)
    print("Đã lưu file: devto_latest_10_posts.xlsx")

except TimeoutException:
    print("Không load được form hoặc bài viết!") 
except NoSuchElementException:
    print("Không tìm thấy bài viết!") 
finally:
    driver.quit()
