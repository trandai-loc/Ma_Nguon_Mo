from selenium import webdriver
from selenium.webdriver.firefox.service import Service
import time

# Đường dẫn đến file thực thi geckodriver
gecko_path = r"D:/MaNguonMo/Project_Selenium_2/geckodriver.exe"

# Khởi tạo đối tượng Service với đường dẫn geckodriver
ser = Service(gecko_path)

# Tạo tùy chọn cho Firefox
options = webdriver.firefox.options.Options()
options.binary_location = r"C:/Program Files/Mozilla Firefox/firefox.exe"  # chỉ dùng nếu cần
options.headless = False  # True nếu muốn chạy ngầm

# Khởi tạo Firefox driver
driver = webdriver.Firefox(service=ser, options=options)

# URL cần truy cập
url = 'http://pythonscraping.com/pages/javascript/ajaxDemo.html'

# Truy cập trang
driver.get(url)

# In ra nội dung trang trước khi chờ
print("Before: ================================\n")
print(driver.page_source)

# Tạm dừng khoảng 3 giây
time.sleep(3)

# In ra nội dung trang sau khi chờ
print("\n\n\n\nAfter: ================================\n")
print(driver.page_source)

# Đóng trình duyệt
driver.quit()
