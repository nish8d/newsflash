import streamlit as st
import sys
import os
import json
import pandas as pd
from datetime import datetime

# --- 1. SETUP & IMPORTS ---
# Add pipeline folders to system path so Python can find them
sys.path.append(os.path.join(os.getcwd(), "news_pipeline"))
sys.path.append(os.path.join(os.getcwd(), "scraper"))  # <--- NEW: Added Scraper Path
sys.path.append(os.path.join(os.getcwd(), "flashcard_pipeline"))

# Import pipeline logic (handling potential path errors)
try:
    from news_pipeline.newspipe import get_all_news
    
    # <--- NEW: Import Scraper Logic
    # CHECK THIS: Ensure the function name inside run_content_pipeline.py matches this import.
    # If your function is named 'main', change this to: from scraper.run_content_pipeline import main as run_content_scraper
    from scraper.run_content_pipeline import run_pipeline as run_content_scraper 
    
    # We rename main to run_flashpipe to avoid confusion
    from flashcard_pipeline.flashpipe import main as run_flashpipe
except ImportError as e:
    st.error(f"Error finding pipeline files: {e}")
    st.stop()

RESULTS_FILE = "resultsgen.json"

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Flashcard News Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for sharper cards
st.markdown("""
<style>
    .stExpander { border: 1px solid #e0e0e0; border-radius: 8px; }
    .metric-box { background-color: #f0f2f6; padding: 10px; border-radius: 5px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR CONTROLLER ---
with st.sidebar:
    st.title("FlashPipe Control")
    st.markdown("---")
    
    keyword = st.text_input("Search Topic", value="")
    
    run_btn = st.button("Run Full Pipeline", type="primary", use_container_width=True)
    
    st.markdown("### Pipeline Status")
    status_container = st.container()

# --- 4. PIPELINE EXECUTION LOGIC ---
if run_btn:
    if not keyword:
        st.warning("Please enter a keyword.")
    else:
        try:
            # --- PHASE 1: NEWS FETCHING ---
            with status_container:
                st.info(f"1. Fetching news for: **{keyword}**...")
                
                # 1. Run News Pipeline
                news_data = get_all_news(keyword)
                
                # 2. Clean Data (Remove embeddings if present)
                for article in news_data:
                    article.pop("embedding", None)
                
                # 3. Save Intermediate JSON (Required for Scraper)
                with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(news_data, f, indent=2)
                
                st.success(f"News fetched: {len(news_data)} articles")

            # --- PHASE 2: CONTENT SCRAPING (NEW STEP) ---
            with status_container:
                st.info("2. Scraping article bodies...")
                
                # 4. Run Scraper Pipeline
                # This function reads RESULTS_FILE, scrapes the 'link' from each, 
                # adds the 'body' field, and saves the JSON back to RESULTS_FILE.
                run_content_scraper()
                
                st.success("Article content scraped!")

            # --- PHASE 3: FLASHCARD GENERATION ---
            with status_container:
                st.info("3. Generating flashcards (Mistral/Ollama)...")
                
                # 5. Run Flashcard Pipeline
                # This function reads the JSON (now containing 'body') and generates Q&A
                run_flashpipe()
                
                st.success("Flashcards generated!")
                
        except Exception as e:
            st.error(f"Pipeline Failed: {e}")

# --- 5. RESULTS DISPLAY ---
# We check if the file exists and load it to display the cards
if os.path.exists(RESULTS_FILE):
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        st.header(f"Results for: {keyword}")
        st.markdown(f"*Found {len(data)} generated cards*")
        st.divider()

        for idx, item in enumerate(data):
            # Create a nice container for each article
            with st.container(border=True):
                
                # --- TOP ROW: Image + Basic Info ---
                col_img, col_info = st.columns([1, 3])
                
                with col_img:
                    image_url = item.get("image")
                    
                    # LOGIC: Only attempt to load if it looks like a valid web URL
                    if image_url and isinstance(image_url, str) and image_url.startswith("http"):
                        try:
                            st.image(image_url, use_container_width=True)
                        except Exception:
                            # If the image fails to load (404 or format error), show nothing
                            st.empty()
                    else:
                        # If image is missing or is garbage data (like a timestamp), show nothing
                        st.empty()

                with col_info:
                    # TITLE & LINK
                    st.subheader(item.get("title", "No Title"))
                    st.markdown(f"**[Read Full Source]({item.get('link', '#')})**")
                    
                    # METADATA ROW
                    m1, m2, m3 = st.columns(3)
                    m1.caption(f"**Source:** {item.get('source', 'Unknown')}")
                    m2.caption(f"**Published:** {item.get('published_at', 'N/A')}")
                    m3.caption(f"**Relevance Score:** {round(item.get('score', 0), 2)}")

                # --- MIDDLE: Summary ---
                # NOTE: 'body' exists in JSON now, but we are deliberately NOT displaying it.
                st.markdown("Summary")
                st.write(item.get("summary", "No summary available."))

                # --- BOTTOM: The Flashcard (Q&A) ---
                st.markdown("---")
                st.markdown("Flashcard Knowledge")
                
                # Using 3 columns for key flashcard data
                f1, f2 = st.columns([1, 1])
                
                with f1:
                    st.info(f"Question:\n\n{item.get('question', 'Pending...')}")
                
                with f2:
                    # Answer hidden in expander for "Flashcard" feel
                    with st.expander("Reveal Answer", expanded=True):
                        st.write(item.get("answer", "Pending..."))
                
                # Context & Entities
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.caption("**Context:**")
                    st.write(item.get("context", ""))
                with c2:
                    st.caption("**Entity:**")
                    st.markdown(f"`{item.get('entity', '-')}`")
                with c3:
                    st.caption("**Person of Contact:**")
                    st.markdown(f"`{item.get('person_of_contact', '-')}`")

    except json.JSONDecodeError:
        st.info("Waiting for pipeline to generate valid results...")
    except Exception as e:
        st.error(f"Error reading results: {e}")
else:
    st.info("Enter a keyword in the sidebar and click Run to start.")