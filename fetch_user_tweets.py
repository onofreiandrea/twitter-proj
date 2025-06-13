from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time
import random
import json
from collections import defaultdict
import os

def create_driver():
    """Create a new Chrome driver with fresh options"""
    chrome_options = Options()
    chrome_options.add_argument('--window-size=1200,800')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    chrome_options.add_argument('--referrer=https://x.com/')
    return webdriver.Chrome(options=chrome_options)

def login_to_twitter(driver, username, password):
    """Login to Twitter"""
    print("Logging in to Twitter...")
    driver.get("https://twitter.com/i/flow/login")
    time.sleep(3)  # Wait for page to load
    
    try:
        # Enter username
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_input.send_keys(username)
        
        # Click Next
        next_button = driver.find_element(By.XPATH, "//span[text()='Next']")
        next_button.click()
        time.sleep(2)
        
        # Enter password
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_input.send_keys(password)
        
        # Click Login
        login_button = driver.find_element(By.XPATH, "//span[text()='Log in']")
        login_button.click()
        
        # Wait for login to complete
        time.sleep(5)
        print("Login successful!")
        return True
        
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

def read_tweet_ids(filename):
    """Read tweet IDs from file and group by user"""
    user_tweet_ids = defaultdict(list)
    with open(filename, 'r') as f:
        for line in f:
            user_id, tweet_id = line.strip().split()
            user_tweet_ids[user_id].append(tweet_id)
    return user_tweet_ids

def load_progress(filename):
    """Load existing progress if any"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                content = f.read().strip()
                if not content:  # If file is empty
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            print(f"Warning: Progress file {filename} is invalid. Starting fresh.")
            return {}
    return {}

def save_progress(filename, data):
    """Save progress to file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def fetch_tweet_with_retry(driver, tweet_id, max_retries=3):
    """Fetch a single tweet using Selenium with retries"""
    url = f"https://x.com/anyuser/status/{tweet_id}"
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} for tweet {tweet_id}")
            driver.get(url)
            
            # Wait for the page to load (up to 10 seconds)
            wait = WebDriverWait(driver, 10)
            
            # Try different selectors for the tweet text
            selectors = [
                '//div[@data-testid="tweetText"]',
                '//article[@data-testid="tweet"]//div[@lang]',
                '//div[contains(@class, "css-901oao")]'
            ]
            
            for selector in selectors:
                try:
                    tweet_element = wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    tweet_text = tweet_element.text
                    if tweet_text:  # Only return if we got some text
                        print(f"Found tweet {tweet_id} with selector: {selector}")
                        return {
                            'id': tweet_id,
                            'text': tweet_text,
                            'url': url
                        }
                except (TimeoutException, StaleElementReferenceException):
                    continue
            
            print(f"Could not find tweet text for {tweet_id} on attempt {attempt + 1}")
            time.sleep(random.uniform(2, 4))  # Wait before retry
            
        except Exception as e:
            print(f"Error on attempt {attempt + 1} for tweet {tweet_id}: {str(e)}")
            time.sleep(random.uniform(2, 4))  # Wait before retry
    
    print(f"Failed to fetch tweet {tweet_id} after {max_retries} attempts")
    return None

def main():
    # Get Twitter credentials
    username = input("Enter your Twitter username/email: ")
    password = input("Enter your Twitter password: ")
    
    # Initialize progress tracking
    progress_file = 'user_tweets_progress.json'
    user_tweets = load_progress(progress_file)
    
    # Read all tweet IDs
    user_tweet_ids = read_tweet_ids('jobs-tweetids')
    
    # Counter for tweets processed in current session
    tweets_in_session = 0
    MAX_TWEETS_PER_SESSION = 100  # Create new session after this many tweets
    
    # Create initial driver and login
    driver = create_driver()
    if not login_to_twitter(driver, username, password):
        print("Failed to login. Exiting...")
        driver.quit()
        return
    
    try:
        # Process each user
        for user_id, tweet_ids in user_tweet_ids.items():
            # Skip if we already processed this user
            if user_id in user_tweets:
                print(f"Skipping user {user_id} - already processed")
                continue
                
            print(f"\nProcessing user {user_id}")
            user_tweets[user_id] = []
            failed_attempts = 0
            MAX_FAILED_ATTEMPTS = 5  # Skip user after this many failed attempts
            tweets_fetched_for_user = 0
            MAX_TWEETS_PER_USER = 21  # Limit tweets per user
            
            # Randomly select tweets for this user
            if len(tweet_ids) > MAX_TWEETS_PER_USER:
                print(f"User has {len(tweet_ids)} tweets, randomly selecting {MAX_TWEETS_PER_USER}")
                tweet_ids = random.sample(tweet_ids, MAX_TWEETS_PER_USER)
            
            # Keep track of which tweets we've tried
            tried_tweets = set()
            current_tweet_index = 0
            
            # Process tweets until we have 20 or hit max failures
            while tweets_fetched_for_user < MAX_TWEETS_PER_USER and failed_attempts < MAX_FAILED_ATTEMPTS:
                # Check if we need a new session
                if tweets_in_session >= MAX_TWEETS_PER_SESSION:
                    print("\nCreating new browser session...")
                    driver.quit()
                    time.sleep(random.uniform(5, 10))  # Longer delay before new session
                    driver = create_driver()
                    if not login_to_twitter(driver, username, password):
                        print("Failed to login in new session. Exiting...")
                        return
                    tweets_in_session = 0
                
                # Get next untried tweet
                while current_tweet_index < len(tweet_ids) and tweet_ids[current_tweet_index] in tried_tweets:
                    current_tweet_index += 1
                
                # If we've tried all tweets, break
                if current_tweet_index >= len(tweet_ids):
                    print(f"No more tweets to try for user {user_id}")
                    break
                
                tid = tweet_ids[current_tweet_index]
                tried_tweets.add(tid)
                current_tweet_index += 1
                
                tweet = fetch_tweet_with_retry(driver, tid)
                if tweet:
                    user_tweets[user_id].append(tweet)
                    tweets_in_session += 1
                    tweets_fetched_for_user += 1
                    failed_attempts = 0  # Reset failed attempts counter on success
                    print(f"Tweets fetched for user {user_id}: {tweets_fetched_for_user}/{MAX_TWEETS_PER_USER}")
                else:
                    failed_attempts += 1
                    if failed_attempts >= MAX_FAILED_ATTEMPTS:
                        print(f"\nSkipping user {user_id} - too many consecutive failed attempts ({failed_attempts})")
                        break
                    print(f"Tweet {tid} failed, trying another one...")
                
                time.sleep(random.uniform(2, 4))  # Longer delay between tweets
            
            # Save progress after each user
            save_progress(progress_file, user_tweets)
            print(f"Saved progress for user {user_id}")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        driver.quit()
        # Save final progress
        save_progress(progress_file, user_tweets)
        print("\nScript completed successfully!")

if __name__ == "__main__":
    main() 