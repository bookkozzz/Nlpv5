from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

# กำหนด Service โดยใช้ msedgedriver.exe จากตำแหน่งที่คุณติดตั้ง
service = Service("C:/Users/Judy/Downloads/edgedriver_win64/msedgedriver.exe")

# สร้างตัวเลือก Edge
options = Options()

# เปิดการใช้งาน Edge WebDriver โดยใช้ Service
driver = webdriver.Edge(service=service, options=options)

# เปิดหน้า Lazada ที่ต้องการ
driver.get("https://my.lazada.co.th/pdp/review/getReviewList?itemId=224504567&pageSize=5&filter=1&sort=0&pageNo=0")

# รอให้หน้าเว็บโหลด
import time
time.sleep(5)

# ดึงค่า nc_app_key จากหน้า HTML
nc_app_key = driver.find_element(By.ID, "nc_app_key").get_attribute("value")
print(f"nc_app_key: {nc_app_key}")

# ดึงค่า NCTOKENSTR จากตัวแปร JavaScript ที่ฝังในหน้า HTML
nctokenstr = driver.execute_script("return window._config_.NCTOKENSTR")
print(f"NCTOKENSTR: {nctokenstr}")

# ดึงค่า site_key หรือค่าอื่นๆ ที่เกี่ยวข้องจาก JavaScript
site_key = driver.execute_script("return window._config_.NCAPPKEY")
print(f"site_key: {site_key}")

# ปิดการทำงานของ WebDriver
driver.quit()
