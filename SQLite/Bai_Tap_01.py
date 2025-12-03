import sqlite3

# 1. Kết nối tới cơ sở dữ liệu
conn = sqlite3.connect("inventory.db")

# Tạo đối tượng 'cursor' để thực thi các câu lệnh sql
cursor = conn.cursor()

# 2. Thao tác với Database va table

# Lệnh SQL để tạo bảng product
sql1 = """
CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    quantity INTEGER
)
"""

# Thực thi câu lệnh tạo bảng
cursor.execute(sql1)
conn.commit() # Lưu thay đổi vào db

# 3. CRUD
# 3.1. Thêm (INSERT)
products_data = [
    ("Laptop A100", 999.99, 15),
    ("Mouse Wireless X", 25.50, 50),
    ("Monitor 27-inch", 249.00, 10)
]

# Lệnh SQL để chèn dữ liệu. Dùng '?' để tránh lỗi SQL Injection
sql2 = """
INSERT INTO product (name, price, quantity)
VALUES (?,?,?)
"""

# Thêm nhiều bản ghi cùng lúc
cursor.executemany(sql2, products_data)
conn.commit() # Lưu thay đổi

# 3.2. Read (SELECT)
sql3 = "SELECT * FROM product"

# Thực thi truy vấn 
cursor.execute(sql3)

# Lấy tất cả kết quả
all_products = cursor.fetchall()

# In tiêu đề
print(f"{'ID':<4} | {'Tên Sản Phẩm':<20} |{'Giá':<10} | {'Số Lượng':<10}")

# Lặp và in ra
for p in all_products:
    print(f"{p[0]:<4} | {p[1]:<20} | {p[2]:< 10} | {p[3]:< 10}")

# 3.3 UPDATE
sql4 = "UPDATE product SET quantity = 20 WHERE id = 1"
cursor.execute(sql4)
conn.commit()

# 3.4 DELETE
sql5 = "DELETE FROM product WHERE id = 2"
cursor.execute(sql5)
conn.commit()

conn.close()