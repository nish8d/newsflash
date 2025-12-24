import trafilatura
from newspaper import Article
import re

def clean_text_artifacts(text):
    """
    Cleans common news artifacts: ads, disclaimers, and subscription text.
    """
    # Ensure text is a string before processing
    if not text or not isinstance(text, str):
        return ""

    # 1. REMOVE ADVERTISEMENT LINES
    # Case insensitive, standalone "Advertisement"
    text = re.sub(r'(?m)^\s*Advertisement\s*$', '', text, flags=re.IGNORECASE)

    # 2. REMOVE SYNDICATED FEED DISCLAIMERS ("Hard Cut")
    # Matches "(This content is sourced...)" and cuts off EVERYTHING after it.
    disclaimer_pattern = r'\(\s*This content is sourced.*?\)'
    match = re.search(disclaimer_pattern, text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        text = text[:match.start()]

    # 3. REMOVE AGENCY TAGS
    # Removes "(ANI)" or similar simple agency tags.
    text = re.sub(r'\(\s*ANI\s*\)', '', text, flags=re.IGNORECASE)

    # 4. REMOVE "PREMIUM/SUBSCRIPTION" BOILERPLATE
    # Removes lines containing specific "call to action" phrases.
    junk_phrases = [
        "Unlock Exclusive Insights",
        "Take your experience further with Premium",
        "Member Only Benefits",
        "Already a Member? Sign In",
        "Subscribe now",
        "Read more with a subscription"
    ]
    
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        if any(phrase.lower() in line.lower() for phrase in junk_phrases):
            continue
        clean_lines.append(line)
    
    text = '\n'.join(clean_lines)

    # 5. FINAL FORMATTING
    # Collapse multiple empty lines into exactly two (standard paragraph spacing)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def scrape_news_standardized(url):
    print(f"Processing: {url} ...")#
    text_body = ""

    # --- METHOD 1: Trafilatura (Primary) ---
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted_text = trafilatura.extract(downloaded, include_comments=False)
            if extracted_text and len(extracted_text) > 100:
                text_body = extracted_text
    except Exception:
        pass 

    # --- METHOD 2: Newspaper3k (Fallback) ---
    if not text_body:
        try:
            article = Article(url)
            article.download()
            article.parse()
            text_body = article.text
        except Exception as e:
            return f"Error extracting text: {e}"

    # --- METHOD 3: The Cleanup ---
    return clean_text_artifacts(text_body)

# --- Usage ---
if __name__ == "__main__":
    link = ""
    print(scrape_news_standardized(link))