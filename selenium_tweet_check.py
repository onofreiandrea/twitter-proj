from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import random

# List of tweet IDs to check (replace with your own or read from file)
tweet_ids = ["439377153302360064", "439378342307831811"]

# Set up Chrome options for headless mode (no window)
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--window-size=1200,800')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
chrome_options.add_argument('--referrer=https://x.com/')

# Path to your ChromeDriver (if not in PATH, specify the full path)
driver = webdriver.Chrome(options=chrome_options)

def check_tweet(tweet_id):
    url = f"https://x.com/anyuser/status/{tweet_id}"
    driver.get(url)
    time.sleep(random.uniform(2, 4))  # Random delay to simulate human behavior
    try:
        # Try to find the tweet text element
        tweet_element = driver.find_element(By.XPATH, '//div[@data-testid="tweetText"]')
        tweet_text = tweet_element.text
        print(f"Tweet {tweet_id} exists!")
        print(f"Text: {tweet_text}\n")
        return True, tweet_text
    except NoSuchElementException:
        print(f"Tweet {tweet_id} does NOT exist or is not accessible.\n")
        return False, None
    except Exception as e:
        print(f"Error for tweet {tweet_id}: {e}\n")
        return False, None

for tid in tweet_ids:
    check_tweet(tid)
    time.sleep(random.uniform(1, 3))  # Random delay between tweets

driver.quit() 