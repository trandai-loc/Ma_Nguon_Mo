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

# Lấy ra tất cả thẻ ul
ul_tags = driver.find_elements(By.TAG_NAME, "ul")
print(len(ul_tags))

# Chọn thẻ ul thứ 21
ul_painters = ul_tags[20] # List start with index=0

# Lấy ra tất cả thẻ <li> thuộc ul_painters
li_tags = ul_painters.find_elements(By.TAG_NAME, "li")

# Tạo danh sách các url
links = [tag.find_element(By.TAG_NAME, "a").get_attribute("href") for tag in li_tags]

# Tạo danh sách các title
titles = [tag.find_element(By.TAG_NAME, "a").get_attribute("title") for tag in li_tags]

# In ra url
for link in links:
    print(link)

# In ra title
for title in titles:
    print(title)

# Đóng webdriver
driver.quit()
