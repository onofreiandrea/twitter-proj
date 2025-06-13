import requests
import json
import time
from collections import defaultdict
import re

def get_tweet_text(tweet_id):
    """Fetch a single tweet from Twitter's web interface"""
    url = f"https://twitter.com/i/status/{tweet_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Try to find the tweet text in the HTML
            # Twitter's HTML structure might have changed, so we try a few patterns
            patterns = [
                r'<div class="css-901oao r-1nao33i r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0">(.*?)</div>',
                r'<div class="css-901oao r-1nao33i r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0" dir="auto">(.*?)</div>',
                r'<div class="css-901oao r-1nao33i r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0" dir="ltr">(.*?)</div>'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return {
                        'id': tweet_id,
                        'text': match.group(1),
                        'url': url
                    }
            
            print(f"Could not find tweet text in HTML for {tweet_id}")
            return None
            
    except Exception as e:
        print(f"Error fetching tweet {tweet_id}: {str(e)}")
        return None

def read_tweet_ids(filename):
    """Read tweet IDs from file and group by user"""
    user_tweet_ids = defaultdict(list)
    with open(filename, 'r') as f:
        for line in f:
            user_id, tweet_id = line.strip().split()
            user_tweet_ids[user_id].append(tweet_id)
    return user_tweet_ids

def tweet_exists(tweet_id):
    url = f"https://x.com/anyuser/status/{tweet_id}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    return r.status_code, url

def main():
    user_tweet_ids = read_tweet_ids('jobs-tweetids')
    sample_user = next(iter(user_tweet_ids))
    sample_tweets = user_tweet_ids[sample_user][:5]
    print(f"Checking existence for user {sample_user}'s first 5 tweets:")
    for tid in sample_tweets:
        status, url = tweet_exists(tid)
        if status == 200:
            print(f"Tweet {tid} exists: {url}")
        elif status == 404:
            print(f"Tweet {tid} does NOT exist (404): {url}")
        else:
            print(f"Tweet {tid} returned status {status}: {url}")
        time.sleep(1)

if __name__ == "__main__":
    main()
