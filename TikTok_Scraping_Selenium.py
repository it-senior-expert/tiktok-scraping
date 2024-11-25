from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import json
import re
import time


# Selenium setup
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--start-maximized')
options.add_argument('--disable-notifications')  # Disable notifications
options.add_argument('--disable-popup-blocking')  # Disable popup blocking
options.add_argument('--disable-infobars')  # Disable infobars
options.add_argument('--disable-blink-features=AutomationControlled')  # Prevent detection
driver = webdriver.Chrome(service=service, options=options)


# Utility functions
def extract_hashtags(description):
    """Extracts hashtags from a given description."""
    return re.findall(r'#\w+', description)


def convert_to_number(value):
    """Converts shorthand notations like 'K' and 'M' into numbers."""
    if value.endswith("M"):
        return float(value[:-1]) * 1000000
    elif value.endswith("K"):
        return float(value[:-1]) * 1000
    try:
        return int(value)
    except ValueError:
        return 0


def scrape_tiktok(keyword):
    """Scrapes TikTok user data for the given keyword."""
    search_url = f'https://www.tiktok.com/search/user?q={keyword}'
    driver.get(search_url)

    # Handle potential popups or banners
    time.sleep(3)

    # Extract user profile links
    user_links = driver.find_elements(By.XPATH, '//*[@data-e2e="search-user-info-container"]')
    all_videos = []


    for link in user_links[:]:  # Limit to first 3 profiles for efficiency
        try:
            profile_url = link.get_attribute('href')
            driver.get(profile_url)
            channel_name = profile_url.split('@')[-1]
            time.sleep(3)

            video_elements = driver.find_elements(By.CSS_SELECTOR, 'div.css-8dx572-DivContainer-StyledDivContainerV2')
            # Extract subscriber count
            subscriber_element = driver.find_element(By.XPATH, '//*[@data-e2e="followers-count"]').text

            total_view = 0
            for video in video_elements[:50]:
                number_view = video.find_element(By.CSS_SELECTOR, 'strong.css-dirst9-StrongVideoCount').text
                number_view_int = convert_to_number(number_view)
                total_view += number_view_int
            
            for video in video_elements[:50]:  # Limit to 50 videos per profile
                video_data = {
                    "Keyword": keyword,
                    "Channel_name": channel_name,
                }

                try:
                    video_data['Subscriber'] = subscriber_element
                except Exception:
                    video_data['Subscriber'] = 'N/A'

                # Extract title
                try:
                    description_text = video.find_element(By.XPATH, '..//picture/img')
                    video_data['Title'] = description_text.get_attribute('alt')
                except Exception:
                    video_data['Title'] = 'N/A'

                # Extract thumbnail URL
                try:
                    thumbnail_element = video.find_element(By.XPATH, '//*[@imagex-version="0.3.10"]')
                    video_data['Thumbnail'] = thumbnail_element.get_attribute('srcset')
                except Exception:
                    video_data['Thumbnail'] = 'N/A'

                # Extract views
                try:
                    views_element = video.find_element(By.CSS_SELECTOR, 'strong.css-dirst9-StrongVideoCount')
                    video_data['Views'] = views_element.text
                except Exception:
                    video_data['Views'] = 'N/A'

                # Extract avatar URL
                try:
                    avatar_element = video.find_element(By.XPATH, '//*[@imagex-version="0.3.10"]')
                    video_data['Avatar'] = avatar_element.get_attribute('src')
                except Exception:
                    video_data['Avatar'] = 'N/A'

                # Calculate score
                try:
                    like_element = video.find_element(By.CSS_SELECTOR, 'strong.css-dirst9-StrongVideoCount')
                    likes = convert_to_number(like_element.text)
                    video_data['Score'] = likes / (total_view/len(video_elements) if video_data['Views'] else 1)
                except Exception:
                    video_data['Score'] = 'N/A'

                all_videos.append(video_data)

        except Exception as e:
            print(f"Error scraping profile: {e}")
            continue

        if(len(all_videos) > 10000):
            return all_videos

    return all_videos


# Main script
input_file_path = './sample_5k.json'
output_file_path = './trending_videos_selenium.csv'

try:
    with open(input_file_path, 'r') as file:
        keywords = json.load(file)
except Exception as e:
    print(f"Error loading keywords: {e}")
    keywords = []

scraped_data = []

for keyword in keywords:
    scraped_data.extend(scrape_tiktok(keyword))

df = pd.DataFrame(scraped_data)
df.to_csv(output_file_path, index=False)

print(f"Data saved to {output_file_path}")

driver.quit()
