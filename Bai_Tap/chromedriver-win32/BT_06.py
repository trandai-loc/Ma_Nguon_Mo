from pygments.formatters.html import webify 
from selenium import webdriver
from selenium.webdriver.common.by import By 
import time
import pandas as pd
import re

# 1. Tại nơi chứa links vaf tạo dataframe rỗng
all_links = []
d = pd.DataFrame ({'name': [], 'birth': [], 'death': [], 'nationality':[]})


# 2. Lay ra tat ca duong dan de truy cap den painters
# Khởi tạo Webdriver
for i in range (70, 71): 
    driver = webdriver.Chrome ()
    url = "https://en.wikipedia.org/wiki/List of painters by name beginning with $22"+chr(i)+"22" 
    try:
        
        # Mở trang
        driver.get(url)
        
        # Đợi một chút để trang tải
        time.sleep(3)
        
        #Lay ra tat cac ca the ul
        ul_tags= driver.find_elements (By.TAG_NAME, "ul") 
        print (len (ul_tags))
        
        # Chon the ul thu 21
        ul_painters = ul_tags [20] # list start with index=0
        
        # Lay ra tat ca the <li> thuoc ul_painters
        li_tags = ul_painters.find_elements (By. TAG_NAME, "li")
        
        # Tao danh sach cac url
        links = [tag.find_element (By. TAG_NAME, "a").get_attribute("href") for tag in li_tags] 
        for x in links:
            all_links.append(x)
    except:
        print("Error!")

# Dong webdrive
driver.quit()

# 3. Lay thong tin cua tung hoa si
count = 0;
for link in all_links:
    if  (count > 3):
        break
    count = count +1;

    print(link)
    try:
        # Khoi tao webdriver
        driver = webdriver.Chrome()

        # Mo trang
        url = link
        driver.get(url)

        # Doi 2 giay
        time.sleep(2)

        # Lay ten hoa si
        try:
            name = driver.find_element(By.TAG_NAME, "h1").text
        except:
            name = ""

        # Lay ngay sinh
        try:
            birth_element = driver.find_element(By.XPATH, "//th[text()='Born']/following-sibling::td")
            birth = birth_element.text
            birth = re.findall(r'[0-9]{1,2}+\s+[A-Za-z]+\s+[0-9]{4}', birth) [0] # regex
        except:
            birth = ""

        # Lay ngay mat
        try:
            nationality_element = driver.find_element(By.XPATH, "//th[text()='Nationality']/following-sibling::td")
            nationality = nationality_element.text
        except:
            nationality = ""
        
        # Tao dictionary thong tin cua hoa si
        painter = {'name' : name, 'birth' : birth, 'death' : death, 'nationality' : nationality}

        # Chuyen doi dictionary thanh dataframe
        painter_df = pd.DataFrame([painter])

        # Them thong tin vao DF chinh
        d = pd.concat([d, painter_df], ignore_index=True)

        # Dong web driver
        driver.quit()

    except:
        pass

# 4. In thong tin
print(d)

# determining the name of the file
file_name = 'Painters.xlsx'

# saving the excel
d.to_excel(file_name)
print('DataFrame is written to Excel File successfully.')

