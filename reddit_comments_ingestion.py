"""
Reddit Comments Ingestion — No API Key Required
=================================================

Scrapes posts from a subreddit and fetches all comments for each post,
exporting everything to a single CSV file per subreddit.

Uses Reddit's public .json endpoints — no OAuth credentials or app
registration needed.

Setup
-----
    uv add requests
    # or
    pip install requests

Usage
-----
    uv run reddit_comments_ingestion.py
    # or
    python reddit_comments_ingestion.py
"""

import csv
import os
import time

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) reddit-comments-ingestion/1.0"
}


def scrape_subreddit(subreddit: str, limit: int = 100, sort: str = "hot"):
    """
    Fetches posts from a subreddit via Reddit's public .json endpoint.
    Yields dicts of post data.
    """
    after = None
    base_url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    fetched = 0

    while fetched < limit:
        params = {"limit": min(100, limit - fetched)}
        if after:
            params["after"] = after

        resp = requests.get(base_url, headers=HEADERS, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"Request failed: {resp.status_code} — {resp.text[:200]}")
            break

        data = resp.json()
        children = data["data"]["children"]
        if not children:
            break

        for child in children:
            p = child["data"]
            yield {
                "id": p.get("id"),
                "title": p.get("title"),
                "author": p.get("author"),
                "score": p.get("score"),
                "num_comments": p.get("num_comments"),
                "created_utc": p.get("created_utc"),
                "permalink": f"https://reddit.com{p.get('permalink')}",
            }
            fetched += 1
            if fetched >= limit:
                break

        after = data["data"].get("after")
        if not after:
            break

        time.sleep(1.5)


def scrape_comments(subreddit: str, post_id: str, post_title: str = ""):
    """
    Fetches comments for a single post via its .json endpoint.
    Recursively walks nested reply trees.
    Yields dicts of comment data with post_id and post_title fields.
    """
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/.json"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    def walk(children):
        for child in children:
            if child["kind"] != "t1":
                continue
            c = child["data"]
            yield {
                "post_id": post_id,
                "post_title": post_title,
                "id": c.get("id"),
                "author": c.get("author"),
                "body": c.get("body"),
                "score": c.get("score"),
                "created_utc": c.get("created_utc"),
            }
            replies = c.get("replies")
            if isinstance(replies, dict):
                yield from walk(replies["data"]["children"])

    if len(data) > 1:
        yield from walk(data[1]["data"]["children"])


def filter_by_keywords(comments: list[dict], keywords: list[str]) -> list[dict]:
    """
    Filters comments by case-insensitive substring match against
    the comment body and post title. Returns matching comments
    with an added 'matched_keyword' column.
    """
    filtered = []
    for comment in comments:
        text = f"{comment.get('body', '')} {comment.get('post_title', '')}".lower()
        for kw in keywords:
            if kw.lower() in text:
                filtered.append({**comment, "matched_keyword": kw})
                break
    return filtered


def save_to_csv(rows, filename: str):
    rows = list(rows)
    if not rows:
        print("No data to save.")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {filename}")


def main():
    print("=" * 50)
    print("       Reddit Comments Ingestion")
    print("=" * 50)
    print()

    subreddit = input("Subreddit name (without r/): ").strip()
    if not subreddit:
        print("No subreddit provided. Exiting.")
        return

    name = input("Your name/label (for filename): ").strip()
    if not name:
        print("No name provided. Exiting.")
        return

    sort_options = ("hot", "new", "rising", "top")
    sort = input(f"Sort by {'/'.join(sort_options)} (default: hot): ").strip() or "hot"
    if sort not in sort_options:
        print(f"Invalid sort '{sort}'. Must be one of: {', '.join(sort_options)}")
        return

    limit_input = input("Number of posts to scrape (default: 25): ").strip()
    limit = int(limit_input) if limit_input.isdigit() else 25

    keywords_input = input("Crisis event keywords (comma-separated): ").strip()
    keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
    if not keywords:
        print("No keywords provided. Exiting.")
        return

    print(f"\nScraping r/{subreddit} | sort: {sort} | limit: {limit}")
    print(f"Keywords: {', '.join(keywords)}")

    posts = list(scrape_subreddit(subreddit, limit=limit, sort=sort))
    print(f"Found {len(posts)} post(s).\n")

    all_comments = []
    for i, post in enumerate(posts, 1):
        print(f"  [{i}/{len(posts)}] Fetching comments for: {post['title'][:60]}...")
        comments = list(scrape_comments(subreddit, post["id"], post_title=post["title"]))
        all_comments.extend(comments)
        print(f"            {len(comments)} comment(s) collected.")
        time.sleep(1.5)

    print(f"\nFiltering {len(all_comments)} comment(s) by {len(keywords)} keyword(s)...")
    matched = filter_by_keywords(all_comments, keywords)
    print(f"  {len(matched)} of {len(all_comments)} comment(s) matched.")

    os.makedirs("output", exist_ok=True)
    output_file = f"output/{subreddit}_{name}_crisis_comments.csv"
    print(f"\nSaving...")
    save_to_csv(matched, output_file)
    print(f"\nDone! Output: {output_file}")


if __name__ == "__main__":
    main()
