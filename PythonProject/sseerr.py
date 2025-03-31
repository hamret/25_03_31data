from selenium import webdriver as wd
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import time
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
import pandas as pd
from datetime import datetime


def dong_amazon_reviews(url):
    options = Options()
    options.add_argument("--headless")  # 브라우저 창 띄우지 않기
    options.add_argument("--window-size=1920x1080")  # 화면 크기
    options.add_argument("disable-gpu")  # GPU 가속 비활성화 (윈도우 전용)

    # Chromedriver의 경로를 Service 객체로 설정
    service = Service(r'C:\Users\108-0\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe')

    # WebDriver 객체 생성
    driver = wd.Chrome(service=service, options=options)

    # 지정된 URL 열기
    driver.get(url)
    driver.implicitly_wait(10)
    res = driver.page_source
    obj = bs(res, 'html.parser')

    # 리뷰 총 개수 가져오기
    review_summary = obj.select('div[data-testid="review-views-pagination"]')
    if not review_summary:
        print("Warning: Unable to locate the review summary on the page.")
        total_reviews = 0  # 기본 값 설정
    else:
        # 총 리뷰 수 추출
        review_text = review_summary[0].get_text().strip()
        total_reviews = int(re.findall(r'\d+', review_text)[-1])  # 전체 리뷰 수 가져오기

    titles = []
    stars = []
    dates = []
    contents = []

    while len(titles) < total_reviews:
        time.sleep(3)  # 페이지 로드 대기
        source = driver.page_source  # 현재 페이지 소스 가져오기
        bs_obj = bs(source, "html.parser")

        # **리뷰 타이틀 가져오기**
        for i in bs_obj.findAll('a', {'data-hook': 'review-title'}):
            titles.append(i.get_text().strip())

        # **리뷰 날짜 가져오기**
        for n in bs_obj.findAll('span', {'data-hook': 'review-date'}):
            nn = ''.join(n.get_text().split(' ')[-3:])
            date = datetime.strptime(nn, '%B%d,%Y').date()
            dates.append(date)

        # **리뷰 내용 가져오기**
        for a in bs_obj.findAll('span', {'data-hook': 'review-body'}):
            contents.append(a.get_text().strip())

        # **리뷰 평점 가져오기**
        for u in bs_obj.findAll('i', {'data-hook': 'review-star-rating'}):
            stars.append(int(u.get_text()[0]))

        for u in bs_obj.findAll('i', {'data-hook': 'cmps-review-star-rating'}):
            stars.append(int(u.get_text()[0]))

        # 다음 페이지 버튼 클릭
        next_button = driver.find_elements(By.XPATH, '//*[@id="cm_cr-pagination_bar"]/ul/li[2]/a')
        if next_button:
            next_button[0].click()
        else:
            print("No more pages to fetch.")  # 다음 페이지 없을 경우 출력
            break

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="a-autoid-3"]/span/input'))  # 특정 요소 나타날 때까지 대기
        )

    driver.close()
    driver.quit()

    # 데이터 프레임 생성
    df = pd.DataFrame({'Date': dates, 'Rating': stars, "Title": titles, "Body": contents})

    return df


# 요청 URL
url = 'https://www.amazon.com/Apple-Watch-Starlight-Aluminum-Sport/dp/B09HF6H3X3/ref=sr_1_1?crid=2WWJ7XQ4YPGF&dib=eyJ2IjoiMSJ9.JgqQlvc3AwXDY7zAZ7orjCYMBW3pe1bSbtkqnmdhjb8fd3wGT0q1JOY_n1d2cgbbmkeHVVqc-Us9njZ61X5R0-W-9kP9kTGIgbWD8ZfVzArl5axrLWRO3IIgDJrhyENnN3mwA0JRyLqdOF-0jOp11FV1nJLssiPVFCCZuApZgdYal6-92Vzge9UltkN6h8K669ekrDhN7WPqhKpnB15pt9BC3nUQ0DfaD9CTDNox6-I.UQxrxUz0WNGVVing2p3u2lcazaQoEKuYTw0cHSlk39o&dib_tag=se&keywords=apple&qid=1743399408&sprefix=apple%2B%2Caps%2C272&sr=8-1&th=1'

# 리뷰 데이터 가져오기ㅗ
data = dong_amazon_reviews(url)

# CSV 파일로 저장
data.to_csv('Apple_Watch_Reviews.csv', index=False)
