# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "praw>=7.7",
#   "pandas>=2.0",
#   "python-dotenv>=1.0",
# ]
# ///
"""
Reddit Post Ingestion
=================
Extracts structured post data (URL, title, date, author, content)
from subreddit searches into clean CSV datasets.

Credentials are loaded from a .env file (see .env.example).
Search parameters are entered interactively at runtime.

Run with uv (no manual install needed):
    uv run reddit_post_ingestion.py

Or traditionally:
    pip install praw pandas python-dotenv
    python reddit_post_ingestion.py
"""

import time
import os
import sys
import praw
import pandas as pd
from dotenv import load_dotenv

# ─────────────────────────────────────────
# 1. Load credentials from .env
# ─────────────────────────────────────────

load_dotenv()  # looks for .env in the same directory as this script

CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT    = os.getenv("REDDIT_USER_AGENT")

if not all([CLIENT_ID, CLIENT_SECRET, USER_AGENT]):
    print("❌ Missing Reddit credentials.")
    print("   Create a .env file in the same folder as this script with:")
    print("     REDDIT_CLIENT_ID=your_client_id")
    print("     REDDIT_CLIENT_SECRET=your_client_secret")
    print("     REDDIT_USER_AGENT=reddit_post_ingestion/1.0 by your_username")
    print()
    print("   See .env.example for reference.")
    sys.exit(1)

# ─────────────────────────────────────────
# 2. Prompt for search parameters
# ─────────────────────────────────────────

VALID_SORT = {"relevance", "top", "comments", "new", "hot"}

print()
print("=" * 50)
print("       Reddit Post Ingestion 🔍")
print("=" * 50)
print()

# --- Keyword ---
while True:
    keyword = input("🔑 Enter search keyword (e.g. graduation): ").strip()
    if keyword:
        break
    print("   ⚠️  Keyword cannot be empty. Try again.")

# --- Subreddit ---
while True:
    subreddit_input = input("📌 Enter subreddit name without r/ (e.g. dlsu): ").strip().lstrip("r/")
    if subreddit_input:
        break
    print("   ⚠️  Subreddit cannot be empty. Try again.")

# --- Sort by ---
print(f"   Sort options: {', '.join(sorted(VALID_SORT))}")
while True:
    sort_by = input("📊 Sort results by (default: relevance): ").strip().lower() or "relevance"
    if sort_by in VALID_SORT:
        break
    print(f"   ⚠️  Invalid sort option. Choose from: {', '.join(sorted(VALID_SORT))}")

# --- Number of posts ---
while True:
    n_posts_input = input("🔢 Number of posts to collect (default: 5, max recommended: 50): ").strip() or "5"
    if n_posts_input.isdigit() and int(n_posts_input) > 0:
        n_posts = int(n_posts_input)
        break
    print("   ⚠️  Please enter a positive whole number.")

print()
print(f"▶️  Searching r/{subreddit_input} for '{keyword}' | sort: {sort_by} | limit: {n_posts}")
print()

# ─────────────────────────────────────────
# 3. Connect to Reddit & search
# ─────────────────────────────────────────

reddit = praw.Reddit(
    client_id     = CLIENT_ID,
    client_secret = CLIENT_SECRET,
    user_agent    = USER_AGENT,
)

subreddit      = reddit.subreddit(subreddit_input)
search_results = list(subreddit.search(keyword, sort=sort_by, limit=n_posts))

if not search_results:
    raise SystemExit("❌ No threads found for this keyword. Try a different keyword or sort option.")

print(f"   Found {len(search_results)} post(s).\n")

# ─────────────────────────────────────────
# 4. Extract posts + comments
# ─────────────────────────────────────────

def extract_thread_data(submission):
    """Return a list of row dicts — one for the post, one per comment."""
    rows = []

    # Original post
    rows.append({
        "post_url" : f"https://www.reddit.com{submission.permalink}",
        "title"    : submission.title,
        "author"   : str(submission.author) if submission.author else "[deleted]",
        "date"     : pd.Timestamp(submission.created_utc, unit="s", tz="UTC")
                       .strftime("%Y-%m-%d %H:%M:%S"),
        "text"     : submission.selftext,
        "score"    : submission.score,
        "type"     : "post",
    })

    # All comments (flattened)
    try:
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            rows.append({
                "post_url" : f"https://www.reddit.com{submission.permalink}",
                "title"    : submission.title,
                "author"   : str(comment.author) if comment.author else "[deleted]",
                "date"     : pd.Timestamp(comment.created_utc, unit="s", tz="UTC")
                               .strftime("%Y-%m-%d %H:%M:%S"),
                "text"     : comment.body,
                "score"    : comment.score,
                "type"     : "comment",
            })
    except Exception as e:
        print(f"   ⚠️  Could not load comments: {e}")

    return rows


all_rows = []

for i, submission in enumerate(search_results, start=1):
    url = f"https://www.reddit.com{submission.permalink}"
    print(f"🔄 Processing post {i}/{len(search_results)}: {url}")

    try:
        rows = extract_thread_data(submission)
        all_rows.extend(rows)
        print(f"   ✅ {len(rows)} row(s) (1 post + {len(rows) - 1} comments)")
    except Exception as e:
        print(f"   ⚠️  Skipped — {e}")

    if i < len(search_results):
        time.sleep(2)  # polite delay between requests

# ─────────────────────────────────────────
# 5. Save to CSV
# ─────────────────────────────────────────

if not all_rows:
    raise SystemExit("❌ No data collected. Nothing to save.")

df = pd.DataFrame(
    all_rows,
    columns=["post_url", "title", "author", "date", "text", "score", "type"],
)

output_dir  = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(output_dir, f"reddit_{subreddit_input}_{keyword}_top{n_posts}_posts.csv")

df.to_csv(output_file, index=False, encoding="utf-8-sig")  # utf-8-sig = Excel-safe UTF-8

print(f"\n✅ Done! {len(df)} total rows exported to:\n   {output_file}")
