import requests
from bs4 import BeautifulSoup
import csv

# specify the target URL
target_url = "https://www.amazon.com/Apple-Watch-Starlight-Aluminum-Sport/dp/B09HF6H3X3/?th=1"

# send a get request to the target url
response = requests.get(target_url)

# check if the response status code is not 200 (OK)
if response.status_code != 200:
    # print an error message with the status code
    print(f"An error occurred with status {response.status_code}")
else:
    # get the page html content
    html_content = response.text

    # parse the html content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # find all elements with class name "a-profile-name"
    reviewer_names = soup.find_all("span", class_="a-profile-name")
    names_list = [name.text.strip() for name in reviewer_names]

    # find all elements with class name "review-title"
    review_titles = soup.find_all("a", class_="review-title")
    titles_list = [title.text.replace("5.0 out of 5 stars\n", "").strip() for title in review_titles]

    # find all elements with class name "review-text-content"
    review_texts = soup.find_all("span", class_="review-text")
    review_texts_list = [text.get_text(separator="\n").strip() for text in review_texts]

    # find all elements with class name "review-date"
    review_dates = soup.find_all("span", class_="review-date")
    review_dates_list = [date.text.strip() for date in review_dates]

    # find all elements with class name "review-rating"
    review_ratings = soup.find_all("i", class_="review-rating")
    review_ratings_list = [rating.text.strip() for rating in review_ratings]

    # find all img elements with class name "review-image-tile"
    review_images = soup.find_all("img", class_="review-image-tile")
    image_urls = [img["src"] for img in review_images]

    # create a dictionary to store the review details
    reviews = {
        "Reviewer Names": names_list,
        "Review Titles": titles_list,
        "Review Texts": review_texts_list,
        "Review Dates": review_dates_list,
        "Review Star Ratings": review_ratings_list,
        "Review Image URLs": image_urls
    }

    # print the dictionary
    print(reviews)

    # specify the CSV file name
    csv_file = "amazon_reviews.csv"
    # open the file in write mode
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        # create a CSV writer object
        writer = csv.writer(file)

        # write the header row
        writer.writerow(["Reviewer Name", "Review Title", "Review Text", "Review Date", "Star Rating"])

        # write the review data
        for i in range(len(names_list)):
            writer.writerow([
                names_list[i],
                titles_list[i] if i < len(titles_list) else "N/A",
                review_texts_list[i] if i < len(review_texts_list) else "N/A",
                review_dates_list[i] if i < len(review_dates_list) else "N/A",
                review_ratings_list[i] if i < len(review_ratings_list) else "N/A",
                image_urls[i] if i < len(image_urls) else "N/A"
            ])

    print(f"Data successfully exported to {csv_file}")
