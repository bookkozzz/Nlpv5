from flask import Flask, render_template, request, jsonify
import requests
import re
import time

app = Flask(__name__)

API_KEY = '871f59955e0f7bb7bc7a7b49ec8ccee9'  # ใส่ API Key ของ 2Captcha
SITE_KEY = 'X82Y__f5e0f3869ee004caddd59c9f2946fb9a'  # ใส่ Google reCAPTCHA site key ของ Lazada

def extract_item_id(url):
    match = re.search(r'i(\d+)-s', url)
    if match:
        return match.group(1)
    return None

def solve_captcha(captcha_url):
    # ส่งคำขอไปยัง 2Captcha API เพื่อถอดรหัส CAPTCHA
    response = requests.post('http://2captcha.com/in.php', {
        'key': API_KEY,
        'method': 'userrecaptcha',
        'googlekey': SITE_KEY,  # ใส่ Google reCAPTCHA site key ที่ได้จาก Lazada
        'pageurl': captcha_url,
    })

    if response.text.startswith('OK'):
        request_id = response.text.split('|')[1]
        # รอจนกว่าจะได้คำตอบ
        for _ in range(5):  # ลอง 5 ครั้ง
            time.sleep(10)  # รอ 10 วินาที หรือสามารถปรับเวลาตามความเหมาะสม
            result = requests.get(f'http://2captcha.com/res.php?key={API_KEY}&action=get&id={request_id}')
            if result.text.startswith('OK'):
                return result.text.split('|')[1]  # ส่งรหัส CAPTCHA ที่ถอดได้
        print("[ERROR] Failed to get CAPTCHA solution after multiple attempts")
    else:
        print("[ERROR] 2Captcha request failed.")
    return None

def get_reviews(item_id, rating_filter):
    url = f"https://my.lazada.co.th/pdp/review/getReviewList?itemId={item_id}&pageSize=5&filter={rating_filter}&sort=0&pageNo=0"
    
    # เริ่มต้นการร้องขอ URL โดยไม่ผ่าน CAPTCHA
    response = requests.get(url)
    if 'captcha' in response.text:  # ตรวจสอบว่าเว็บตอบกลับมาว่ามี CAPTCHA
        print("[INFO] CAPTCHA detected, solving...")
        captcha_key = solve_captcha(url)  # เรียกใช้ฟังก์ชัน solve_captcha
        if captcha_key:
            print(f"[INFO] CAPTCHA solved, key: {captcha_key}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://www.lazada.co.th/',
                'g-recaptcha-response': captcha_key,  # ส่ง CAPTCHA key ที่ได้จาก 2Captcha
            }
            response = requests.get(url, headers=headers)
        else:
            return {"error": "Failed to solve CAPTCHA"}
    
    try:
        response.raise_for_status()
        json_data = response.json()
        return json_data
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred: {e}"}

def analyze_review_sentiment(review_text):
    banned_words = ['โกง', 'ปลอม', 'ไม่ดี', 'กาก']
    for word in banned_words:
        if word in review_text:
            return "Negative"
    return "Positive"

@app.route('/', methods=['GET', 'POST'])
def index():
    item_id = None
    reviews_data = []
    urls_to_request = []

    if request.method == 'POST':
        url = request.form['url']
        item_id = extract_item_id(url)

        if item_id:
            print(f"[INFO] Extracted item_id: {item_id}")

            for rating in [5, 4, 3, 2, 1]:
                api_url = f"https://my.lazada.co.th/pdp/review/getReviewList?itemId={item_id}&pageSize=5&filter={rating}&sort=0&pageNo=0"
                print(f"[DEBUG] Generated URL for rating {rating}: {api_url}")
                urls_to_request.append((api_url, rating))

            print(f"[DEBUG] All URLs to request: {[u[0] for u in urls_to_request]}")

            for api_url, rating in urls_to_request:
                reviews = get_reviews(item_id, rating)
                if 'error' in reviews:
                    return render_template('index.html', error=reviews['error'], item_id=item_id)
                if 'data' in reviews:
                    for review in reviews['data']['items']:
                        review_text = review.get('content', 'ไม่มีข้อความรีวิว')
                        sentiment = analyze_review_sentiment(review_text)
                        reviews_data.append({
                            'rating': rating,
                            'content': review_text,
                            'sentiment': sentiment
                        })
                else:
                    print(f"[WARNING] No data found in response for rating {rating}")

            return render_template('index.html', reviews=reviews_data, item_id=item_id, urls=[u[0] for u in urls_to_request])
        else:
            return render_template('index.html', error="ไม่สามารถดึงเลข ID จาก URL ได้", item_id=None)

    return render_template('index.html', reviews=None, item_id=None)

if __name__ == '__main__':
    app.run(debug=True)
