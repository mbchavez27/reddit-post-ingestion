"""
Reddit Batch Post & Comment Ingestion
======================================

Reads a CSV of Reddit post URLs, fetches each post and its comments,
and exports to CSV — either merged or per-post.

Reuses the OAuth client and scraping logic from reddit_comments_ingestion.py.

Setup
-----
    uv sync

Usage
-----
    uv run python batch_reddit_ingestion.py
"""

import csv
import io
import re
import sys
import time
from pathlib import Path

from reddit_comments_ingestion import (
    FIELDNAMES,
    RedditClient,
    format_comment_row,
    format_post_row,
    save_to_csv,
    scrape_comments,
)


def prompt_default(prompt: str, default: str) -> str:
    user_input = input(f"{prompt} [{default}]: ").strip()
    return default if not user_input else user_input


def prompt_yes_no(prompt: str, default: bool = False) -> bool:
    default_str = "Y" if default else "N"
    user_input = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not user_input:
        return default
    return user_input in ("y", "yes")


def extract_reddit_post_id(url: str) -> tuple[str, str] | None:
    """Parse a Reddit URL and return (subreddit, post_id).

    Supports:
      - https://www.reddit.com/r/SUBREDDIT/comments/POST_ID/slug/
      - https://www.reddit.com/comments/POST_ID
      - Raw post IDs (returns None for subreddit)
    """
    url = url.strip()

    match = re.search(r"reddit\.com/r/(\w+)/comments/(\w+)", url)
    if match:
        return match.group(1), match.group(2)

    match = re.search(r"reddit\.com/comments/(\w+)", url)
    if match:
        return "_unknown", match.group(1)

    if re.match(r"^[a-z0-9]{5,}$", url):
        return "_unknown", url

    return None


def load_urls_from_csv(path: Path, column_hint: str | None = None) -> list[str]:
    """Read a CSV and extract Reddit post URLs, auto-detecting the column."""
    if not path.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)

    with path.open("r", encoding="utf-8", newline="") as handle:
        header_line: str | None = None
        while True:
            line = handle.readline()
            if line == "":
                break
            if line.strip():
                header_line = line
                break

        if not header_line:
            print("Error: CSV file is empty")
            sys.exit(1)

        remainder = handle.read()
        combined = header_line + remainder

        try:
            dialect = csv.Sniffer().sniff(combined[:8192], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(io.StringIO(combined), dialect)
        raw_headers = next(reader, [])
        headers = [str(h).strip().lstrip("\ufeff").lower() for h in raw_headers]

    rows = list(reader)

    col_index: int | None = None
    if column_hint:
        lower_hint = column_hint.strip().lower()
        try:
            col_index = headers.index(lower_hint)
        except ValueError:
            print(f"Column '{column_hint}' not found. Available columns: {', '.join(headers)}")
            sys.exit(1)
    else:
        known_names = ["url", "link", "reddit_url", "post_url", "post_link"]
        for name in known_names:
            try:
                col_index = headers.index(name)
                print(f"Auto-detected column: '{headers[col_index]}'")
                break
            except ValueError:
                continue

    urls: list[str] = []
    if col_index is not None:
        for row in rows:
            if col_index < len(row):
                val = str(row[col_index]).strip()
                if val:
                    urls.append(val)
    else:
        print("No known column found — scanning all cells for Reddit links...")
        seen: set[str] = set()
        url_pattern = re.compile(
            r"(?:https?://)?(?:www\.)?reddit\.com/\S+"
        )
        id_pattern = re.compile(r"^[a-z0-9]{5,}$")
        for row in rows:
            for cell in row:
                val = str(cell).strip()
                if not val or val in seen:
                    continue
                match = url_pattern.search(val)
                if match:
                    seen.add(val)
                    urls.append(match.group(0))
                elif id_pattern.match(val):
                    seen.add(val)
                    urls.append(val)

    if not urls:
        print("Error: No Reddit URLs or post IDs found in CSV")
        sys.exit(1)

    return urls


def main():
    print("Reddit Batch Ingestion Tool")
    print("━" * 50)

    csv_input = input("Enter path to CSV file: ").strip()
    csv_path = Path(csv_input).expanduser()

    column_hint = input(
        "Enter column name (or press Enter to auto-detect): "
    ).strip() or None

    keyword = prompt_default("Enter keyword to filter by (leave empty for no filter)", "")

    output_mode = prompt_default("Output mode (all/per)", "all")
    if output_mode not in ("all", "per"):
        print(f"Invalid mode '{output_mode}', defaulting to all")
        output_mode = "all"

    if output_mode == "all":
        from datetime import datetime
        output_default = f"output/batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_file = prompt_default("Output file", output_default)
        output_folder = None
    else:
        folder_name = prompt_default("Output folder name", "batch_output")
        output_folder = Path("output") / folder_name
        output_file = None

    print("━" * 50 + "\n")

    print("Loading URLs from CSV...")
    urls = load_urls_from_csv(csv_path, column_hint)
    print(f"Found {len(urls)} unique post URL(s)")
    if keyword:
        print(f"Keyword filter: {keyword}")
    print()

    if output_folder:
        output_folder.mkdir(parents=True, exist_ok=True)

    client = RedditClient()

    all_rows: list[dict] = []
    total_posts = 0
    total_comments = 0
    failures = 0

    for i, url in enumerate(urls, start=1):
        remaining = len(urls) - i
        print(f"\n[{i}/{len(urls)}] — {remaining} remaining")
        print("─" * 40)

        parsed = extract_reddit_post_id(url)
        if not parsed:
            print(f"  (skip) Could not parse URL: {url}")
            failures += 1
            continue

        subreddit, post_id = parsed
        print(f"  URL: {url}")
        print(f"  Subreddit: r/{subreddit} | Post ID: {post_id}")

        try:
            print("  Fetching post and comments...")
            post_data, comment_data_list, author_lookup = scrape_comments(
                client, subreddit, post_id
            )

            if not post_data:
                print("  (skip) Post not found or private")
                failures += 1
                continue

            title = post_data.get("title", "")
            title_matches = not keyword or keyword.lower() in title.lower()

            if not title_matches:
                print(f"  (filtered) Post: {title[:60]}...")
                continue

            post_row = format_post_row(post_data)
            post_comments = []
            for c in comment_data_list:
                if not keyword or keyword.lower() in c.get("body", "").lower():
                    post_comments.append(format_comment_row(c, author_lookup))

            print(f"  Post: {title[:60]}...")
            print(f"  {len(post_comments)} comment(s) collected.")

            if output_mode == "per":
                post_csv = output_folder / f"{post_id}.csv"
                save_to_csv([post_row] + post_comments, str(post_csv))
            else:
                all_rows.append(post_row)
                all_rows.extend(post_comments)

            total_posts += 1
            total_comments += len(post_comments)
            time.sleep(1.5)

        except Exception as e:
            print(f"  Error: {e}")
            failures += 1

    if output_mode == "all" and all_rows:
        os.makedirs("output", exist_ok=True)
        print(f"\nSaving to {output_file}...")
        save_to_csv(all_rows, output_file)

    print("\n" + "━" * 50)
    print(
        f"Batch complete: {total_posts} posts processed, "
        f"{total_comments} total comments, {failures} failure(s)"
    )
    if output_folder:
        print(f"Output: {output_folder}/")
    print("━" * 50)


if __name__ == "__main__":
    main()
