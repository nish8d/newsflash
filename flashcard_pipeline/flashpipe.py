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
    """Save results with backup."""
    # Create backup before overwriting
    """
    if os.path.exists(NEWS_JSON_PATH):
        backup_path = NEWS_JSON_PATH.replace(".json", "_backup.json")
        with open(backup_path, "w", encoding="utf-8") as f:
            with open(NEWS_JSON_PATH, "r", encoding="utf-8") as original:
                f.write(original.read())
        print(f"Backup saved to {backup_path}")
    """
    with open(NEWS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Updated resultsgen.json saved.")


def process_single_article(args):
    """Process a single article (for parallel execution)."""
    idx, article, generator = args
    title = article.get("title", "Untitled Article")
    
    article_payload = {
        "title": article.get("title", ""),
        "summary": article.get("summary", ""),
        "published_at": article.get("published_at", ""),
        "source": article.get("source", ""),
    }

    try:
        result = generator.generate_for_article(article_payload)
        
        # Update article with flashcard data
        article["question"] = result.get("question", "")
        article["answer"] = result.get("answer", "")
        article["context"] = result.get("context", "")
        article["entity"] = result.get("entity", "")
        article["person_of_contact"] = result.get("person_of_contact", "")
        
        return idx, article, None, title
        
    except Exception as e:
        # Ensure keys exist even on failure
        article["question"] = ""
        article["answer"] = ""
        article["context"] = ""
        article["entity"] = ""
        article["person_of_contact"] = ""
        
        return idx, article, str(e), title


def main():
    print("Enhanced Flashcard Pipeline Started\n")
    print("=" * 60)
    
    start_time = time.time()
    
    # Load articles
    articles = load_news_json()
    total_articles = len(articles)
    print(f"Loaded {total_articles} articles\n")
    
    # Initialize generator (shared across threads)
    generator = FlashcardGenerator(
        model="mistral",
        temperature=0.3,  # Slightly creative but still focused
        max_retries=2
    )
    
    # Determine optimal number of workers
    # Ollama typically handles 2-4 concurrent requests well
    max_workers = min(4, os.cpu_count() or 1)
    print(f"Using {max_workers} parallel workers\n")
    
    # Prepare arguments for parallel processing
    tasks = [(idx, article, generator) for idx, article in enumerate(articles, start=1)]
    
    # Track results
    successful = 0
    failed = 0
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
                idx, updated_article, error, title = future.result()
                
                # Update the article in the list
                articles[idx - 1] = updated_article
                
                if error:
                    failed += 1
                    errors.append(f"Article {idx} ({title[:50]}...): {error}")
                    pbar.set_postfix({"✓": successful, "✗": failed})
                else:
                    successful += 1
                    pbar.set_postfix({"✓": successful, "✗": failed})
                
                pbar.update(1)
    
    # Save results
    print(f"\n{'=' * 60}")
    save_updated_results(articles)
    
    # Print summary
    elapsed_time = time.time() - start_time
    print(f"\nSUMMARY")
    print(f"{'=' * 60}")
    print(f"Successful: {successful}/{total_articles}")
    print(f"Failed: {failed}/{total_articles}")
    print(f"Time: {elapsed_time:.2f}s ({elapsed_time/total_articles:.2f}s per article)")
    
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for error in errors[:5]:  # Show first 5 errors
            print(f"   • {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
    
    print(f"\n{'=' * 60}")
    print("Pipeline Finished!")


if __name__ == "__main__":
    main()