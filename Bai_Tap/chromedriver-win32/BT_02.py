from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Khởi tạo webdriver
driver = webdriver.Chrome()

# Mở trang
url = "https://en.wikipedia.org/wiki/List_of_painters_by_name"
driver.get(url)

# Đợi 2 giây để trang tải
time.sleep(2)

# Lấy tất cả các thẻ <a> trong phần nội dung chính
tags = driver.find_elements(By.XPATH, "//div[@class='mw-parser-output']//ul/li/a")

# Tạo danh sách các liên kết
links = [tag.get_attribute("href") for tag in tags if tag.get_attribute("href") and "List_of_painters" in tag.get_attribute("href")]

# Xuất thông tin
for link in links:
    print(link)

# Đóng webdriver
driver.quit()
