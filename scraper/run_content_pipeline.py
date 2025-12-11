import json
import os
import time
import random
from tqdm import tqdm  # Progress bar library

# Import your existing scraper function
# Since this script is in the same folder as mainscraper.py, we can import directly
try:
    from mainscraper import scrape_news_standardized
except ImportError:
    print("Error: Could not find mainscraper.py. Make sure it is in the same folder as this script.")
    exit()

def run_pipeline():
    # 1. SETUP PATHS
    # Get the directory where this script is located (scraper/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Calculate path to the JSON file (one level up)
    json_path = os.path.join(current_dir, '..', 'resultsgen.json')
    
    # 2. LOAD DATA
    print(f"Reading data from: {json_path}")
    if not os.path.exists(json_path):
        print("Error: resultsgen.json not found in the parent directory.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    print(f"Found {len(articles)} articles. Starting content scraping...")

    # 3. PROCESS ARTICLES
    # We use tqdm to show a progress bar in the terminal
    updated_count = 0
    
    for article in tqdm(articles, desc="Scraping Articles"):
        
        # Skip if 'body' already exists (useful if you re-run the script)
        if 'body' in article and article['body'] and len(article['body']) > 50:
            continue
            
        link = article.get('link')
        
        if link:
            # Call your standardized scraper
            try:
                # Scrape the body
                body_text = scrape_news_standardized(link)
                
                # Update the article object
                article['body'] = body_text
                updated_count += 1
                
                # Polite Delay: Wait 1-3 seconds to avoid getting IP banned by servers
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"\nFailed to scrape {link}: {e}")
                article['body'] = "" # Set empty body on failure so we don't crash
        else:
            article['body'] = ""

    # 4. SAVE RESULTS
    # We write back to the same file (updating it)
    print(f"\nScraping complete. Updated {updated_count} articles.")
    print("Saving updated JSON...")
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)
        
    print("Success! resultsgen.json has been updated with article bodies.")

if __name__ == "__main__":
    run_pipeline()
    