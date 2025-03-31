import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 제품 ASIN
asin = "B09HF6H3X3"

# 요청에 사용할 헤더
custom_headers = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "Gecko/20100101 Firefox/135.0"
    )
}


# URL에서 soup 객체를 생성하는 함수
def get_soup(url):
    response = requests.get(url, headers=custom_headers)

    if response.status_code != 200:
        print(f"Error in getting webpage: {response.status_code}")
        exit(-1)

    return BeautifulSoup(response.text, "lxml")


# 리뷰 데이터를 추출하는 함수
def extract_review(review, is_local=True):
    # 안전하게 요소를 가져오도록 처리
    author = review.select_one(".a-profile-name")
    author = author.text.strip() if author else "Unknown Author"

    rating_element = review.select_one(".review-rating > span")
    rating = (
        rating_element.text.replace("out of 5 stars", "").strip()
        if rating_element
        else "No Rating"
    )

    date_element = review.select_one(".review-date")
    date = date_element.text.strip() if date_element else "Unknown Date"

    # 지역(local) 또는 글로벌(global)에 따라 처리
    if is_local:
        title_element = review.select_one(".review-title")
        title = (
            title_element.select_one("span:not([class])").text.strip()
            if title_element and title_element.select_one("span:not([class])")
            else "No Title"
        )
        content = ' '.join(
            review.select_one(".review-text").stripped_strings
        ) if review.select_one(".review-text") else "No Content"
        img_selector = ".review-image-tile"
    else:
        title_element = review.select_one(".review-title")
        title = (
            title_element.select_one(".cr-original-review-content").text.strip()
            if title_element and title_element.select_one(".cr-original-review-content")
            else "No Title"
        )
        content_section = review.select_one(".review-text")
        content = ' '.join(
            content_section.select_one(".cr-original-review-content").stripped_strings
        ) if content_section and content_section.select_one(".cr-original-review-content") else "No Content"
        img_selector = ".linkless-review-image-tile"

    verified_element = review.select_one("span.a-size-mini")
    verified = verified_element.text.strip() if verified_element else "Not Verified"

    image_elements = review.select(img_selector)
    images = (
        [img.attrs["data-src"] for img in image_elements]
        if image_elements else []
    )

    return {
        "type": "local" if is_local else "global",
        "author": author,
        "rating": rating,
        "title": title,
        "content": content.replace("Read more", ""),
        "date": date,
        "verified": verified,
        "images": images
    }


# soup 객체에서 리뷰를 추출하는 함수
def get_reviews(soup):
    reviews = []

    # 지역(local) 리뷰와 글로벌(global) 리뷰를 가져옴
    local_reviews = soup.select("#cm-cr-dp-review-list > li")
    global_reviews = soup.select("#cm-cr-global-review-list > li")

    # 각각 데이터 처리
    for review in local_reviews:
        reviews.append(extract_review(review, is_local=True))

    for review in global_reviews:
        reviews.append(extract_review(review, is_local=False))

    return reviews


# 모든 페이지의 리뷰를 가져오는 함수
def fetch_all_reviews(base_url):
    reviews = []

    # 첫 번째 페이지를 처리
    page = 1
    current_url = base_url

    while current_url:  # 다음 페이지가 있을 때 계속 반복
        print(f"Fetching page {page}...")
        soup = get_soup(current_url)
        reviews.extend(get_reviews(soup))

        # 다음 페이지 링크가 있는지 확인
        next_page_link = soup.select_one("li.a-last > a")
        if next_page_link and "href" in next_page_link.attrs:
            next_page_url = next_page_link.attrs["href"]
            current_url = f"https://www.amazon.com{next_page_url}"
            page += 1

            # 아마존 요청에 제한이 있을 수 있으니 잠시 대기
            time.sleep(1)

        else:
            # 더 이상 다음 페이지가 없으면 종료
            print(f"No more pages. Collected {len(reviews)} reviews.")
            current_url = None

    return reviews


def main():
    # 첫 리뷰 페이지 URL
    base_url = f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_othr_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"

    # 모든 페이지의 리뷰를 가져옴
    reviews = fetch_all_reviews(base_url)

    # 데이터를 DataFrame으로 저장
    df = pd.DataFrame(reviews)
    df.to_csv(f"reviews_{asin}.csv", index=False)
    print(f"Saved {len(reviews)} reviews to 'reviews_{asin}.csv'")


if __name__ == "__main__":
    main()
