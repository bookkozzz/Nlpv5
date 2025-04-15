from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests

# ===== STEP 1: เปิด Browser ====
print("[DEBUG] Opening browser...")
options = Options()
options.add_argument("--start-maximized")  # เปิดหน้าจอขนาดใหญ่สุด
driver = webdriver.Edge(service=Service(), options=options)

# ===== STEP 2: เข้าไปที่ URL เพื่อดึงข้อมูล ====
product_url = "https://my.lazada.co.th/pdp/review/getReviewList?itemId=5386536770&pageSize=5&filter=1&sort=0&pageNo=0"
print(f"[DEBUG] Accessing URL: {product_url}")
driver.get(product_url)

# ===== STEP 3: รอ CAPTCHA (ถ้ามี) ====
print("[DEBUG] Waiting for CAPTCHA (if any)...")
time.sleep(8)  # รอให้ CAPTCHA โหลด

# ===== STEP 4: ตรวจสอบสถานะ URL ถ้าเป็น URL ที่ผิดปกติ เช่น มีคำว่า "punish" แสดงว่าติดบอท ====
current_url = driver.current_url
print(f"[DEBUG] Current URL: {current_url}")

if "punish" in current_url:
    print("[DEBUG] [!] Bot detected! Attempting to solve CAPTCHA...")

    # ===== STEP 5: ดึงค่า sitekey ถ้าติดบอท (หากมี CAPTCHA) ====
    sitekey = None
    try:
        # รอจนกว่า CAPTCHA จะโหลด
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='h-captcha']")))

        # ค้นหาค่า `sitekey` จากหน้าเว็บ (ดึงจาก window._config_)
        sitekey = driver.execute_script("return window._config_.NCAPPKEY")
        print(f"[DEBUG] Found sitekey: {sitekey}")
    except Exception as e:
        print(f"[DEBUG] Failed to find sitekey: {e}")
    
    if sitekey:
        # ===== STEP 6: ส่ง CAPTCHA ไป 2Captcha ด้วย `sitekey` ที่ดึงได้ ====
        API_KEY = "871f59955e0f7bb7bc7a7b49ec8ccee9"  # ใส่ API KEY ของคุณ
        page_url = driver.current_url  # ดึง URL ของหน้าเว็บจาก Selenium
        
        print(f"[DEBUG] Sending CAPTCHA to 2Captcha for URL: {page_url}")
        
        # ส่ง CAPTCHA ไป 2Captcha
        resp = requests.post("http://2captcha.com/in.php", data={
            'key': API_KEY,
            'method': 'hcaptcha',
            'sitekey': sitekey,
            'pageurl': page_url,
            'json': 1
        })
        request_id = resp.json().get("request")
        print(f"[DEBUG] CAPTCHA sent to 2Captcha successfully, Request ID: {request_id}")

        # รอผลลัพธ์จาก 2Captcha
        print("[DEBUG] Waiting for response from 2Captcha...")
        token = None
        for _ in range(20):
            time.sleep(5)
            res = requests.get(f"http://2captcha.com/res.php?key={API_KEY}&action=get&id={request_id}&json=1")
            if res.json().get("status") == 1:
                token = res.json().get("request")
                print("[DEBUG] [*] CAPTCHA solved successfully!")
                break
            print(f"[DEBUG] [*] CAPTCHA token not received yet, waiting 5 seconds...")

        # ===== STEP 7: ใส่ Token ลงใน CAPTCHA ถ้ามี ====
        if token:
            print(f"[DEBUG] [*] Filling CAPTCHA token into form: {token}")
            driver.execute_script(f'document.querySelector("[name=h-captcha-response]").innerHTML = "{token}";')
            driver.execute_script('document.querySelector("form").submit();')
            time.sleep(5)
        else:
            print("[DEBUG] [-] Unable to solve CAPTCHA")
    else:
        print("[DEBUG] [*] No sitekey found for CAPTCHA.")
else:
    print("[DEBUG] [*] No CAPTCHA detected, proceeding with data retrieval.")

    # ===== STEP 8: ดึง Cookies ==== 
    print("[DEBUG] Extracting cookies...")
    cookies = driver.get_cookies()
    x5secdata = None
    for cookie in cookies:
        if cookie['name'] == 'x5secdata':
            x5secdata = cookie['value']
            print(f"[DEBUG] [*] Found x5secdata: {x5secdata}")

    # ===== STEP 9: ใช้ x5secdata ดึงข้อมูลจาก URL ==== 
    if x5secdata:
        print("[DEBUG] Using x5secdata to retrieve data from URL...")
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Cookie': f'x5secdata={x5secdata};'
        }

        # ใช้ URL สำหรับดึงข้อมูลรีวิวสินค้า
        url = "https://my.lazada.co.th/pdp/review/getReviewList?itemId=5386536770&pageSize=5&filter=1&sort=0&pageNo=0"
        print(f"[DEBUG] Sending HTTP request to URL: {url}")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print("[DEBUG] [*] Data retrieval successful!")
            print(response.json())
        else:
            print(f"[DEBUG] [-] Data retrieval failed, Status Code: {response.status_code}")

# ปิดเบราว์เซอร์
print("[DEBUG] Closing browser...")
driver.quit()
