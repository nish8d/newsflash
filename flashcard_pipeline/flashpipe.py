# flashcard_pipeline/flashpipe.py

import os
import json
from dotenv import load_dotenv
from flashcard_generator import FlashcardGenerator
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
NEWS_JSON_PATH = os.path.join(ROOT_DIR, "resultsgen.json")


def load_news_json():
    """Load the list of articles from resultsgen.json."""
    if not os.path.exists(NEWS_JSON_PATH):
        raise FileNotFoundError(f"News JSON not found at: {NEWS_JSON_PATH}")

    with open(NEWS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected JSON to be a list of articles.")

    return data


def save_updated_results(data):
    """Save results immediately (no backup to avoid slowdown)."""
    with open(NEWS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def process_single_article(args):
    """Process a single article (for parallel execution)."""
    idx, article, generator = args
    title = article.get("title", "Untitled Article")
    
    # Skip if already processed (has summary and question)
    if article.get("summary") and article.get("question"):
        return idx, article, None, title, True  # True = skipped
    
    article_payload = {
        "title": article.get("title", ""),
        "body": article.get("body", ""),
        "published_at": article.get("published_at", ""),
        "source": article.get("source", ""),
    }

    try:
        result = generator.generate_for_article(article_payload)
        
        # Update article with flashcard data
        article["summary"] = result.get("summary", "")
        article["question"] = result.get("question", "")
        article["answer"] = result.get("answer", "")
        article["context"] = result.get("context", "")
        article["entity"] = result.get("entity", "")
        article["person_of_contact"] = result.get("person_of_contact", "")
        
        return idx, article, None, title, False
        
    except Exception as e:
        # Ensure keys exist even on failure
        article["summary"] = article.get("summary", "")
        article["question"] = article.get("question", "")
        article["answer"] = article.get("answer", "")
        article["context"] = article.get("context", "")
        article["entity"] = article.get("entity", "")
        article["person_of_contact"] = article.get("person_of_contact", "")
        
        return idx, article, str(e), title, False


def main():
    print("\nFlashcard Pipeline Started")
    print("-" * 40)
    
    start_time = time.time()
    
    # Load articles
    articles = load_news_json()
    total_articles = len(articles)
    
    # Check how many already have flashcards
    already_processed = sum(1 for a in articles if a.get("summary") and a.get("question"))
    to_process = total_articles - already_processed
    
    print(f"Loaded: {total_articles} articles")
    print(f"Already processed: {already_processed}")
    print(f"To process: {to_process}\n")
    
    if to_process == 0:
        print("All articles already processed.\n")
        return
    
    # Initialize generator
    generator = FlashcardGenerator(
        model="mistral",
        temperature=0.2,
        max_retries=3
    )
    
    # Determine optimal number of workers
    max_workers = min(6, os.cpu_count() or 2)
    print(f"Using {max_workers} workers\n")
    
    # Prepare arguments for parallel processing
    tasks = [(idx, article, generator) for idx, article in enumerate(articles, start=1)]
    
    # Track results
    successful = 0
    failed = 0
    skipped = 0
    errors = []
    
    # Process in parallel with progress bar
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_article = {
            executor.submit(process_single_article, task): task[0] 
            for task in tasks
        }
        
        # Process completed tasks with progress bar
        with tqdm(total=total_articles, desc="Processing", unit="article") as pbar:
            for future in as_completed(future_to_article):
                idx, updated_article, error, title, was_skipped = future.result()
                
                # Update the article in the list
                articles[idx - 1] = updated_article
                
                if was_skipped:
                    skipped += 1
                elif error:
                    failed += 1
                    errors.append(f"#{idx}: {error[:80]}")
                else:
                    successful += 1
                
                pbar.update(1)
                
                # Save progress every 10 articles
                if (successful + failed) % 10 == 0:
                    save_updated_results(articles)
    
    # Final save
    save_updated_results(articles)
    
    # Print summary
    elapsed_time = time.time() - start_time
    print(f"\n{'-' * 40}")
    print("Results:")
    print(f"  Successful: {successful}/{total_articles} ({successful/total_articles*100:.1f}%)")
    if skipped > 0:
        print(f"  Skipped: {skipped}")
    if failed > 0:
        print(f"  Failed: {failed} ({failed/total_articles*100:.1f}%)")
    print(f"\nTime: {elapsed_time:.1f}s ({elapsed_time/max(to_process, 1):.1f}s per article)")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors[:5]:
            print(f"  {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
    
    print("\nComplete.\n")


if __name__ == "__main__":
    main()