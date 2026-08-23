"""
Reddit Post & Comment Ingestion
================================

Scrapes posts and comments from a subreddit using Reddit's OAuth API,
exporting everything to a single CSV file with full metadata.

Uses Reddit's Android app public client ID — no app registration needed.

Setup
-----
    uv sync

Usage
-----
    uv run python reddit_comments_ingestion.py
"""

import csv
import json
import os
import time
import uuid
from datetime import datetime, timezone

import requests

FIELDNAMES = [
    "type",
    "id",
    "parent_id",
    "author",
    "author_fullname",
    "replying_to_user",
    "score",
    "created_time",
    "text",
    "media_url",
    "permalink",
    "subreddit",
    "gildings",
    "replies_count",
    "is_nsfw",
    "is_spoiler",
    "is_oc",
    "metadata_json",
]

ANDROID_CLIENT_ID = "ohXpoqrZYub1kg"
USER_AGENT = "android:com.reddit.frontpage:v2024.45.0 (by /u/research-bot)"


def prompt_default(prompt: str, default: str) -> str:
    user_input = input(f"{prompt} [{default}]: ").strip()
    return default if not user_input else user_input


def prompt_yes_no(prompt: str, default: bool = False) -> bool:
    default_str = "Y" if default else "N"
    user_input = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not user_input:
        return default
    return user_input in ("y", "yes")


def utc_to_iso(utc_seconds: float | None) -> str:
    if utc_seconds is None:
        return ""
    dt = datetime.fromtimestamp(utc_seconds, tz=timezone.utc)
    return dt.isoformat()


def resolve_media_url(data: dict) -> str:
    if data.get("is_self"):
        return ""
    if data.get("url"):
        return data["url"]
    if data.get("media") and isinstance(data["media"], dict):
        reddit_video = data["media"].get("reddit_video", {})
        if reddit_video.get("fallback_url"):
            return reddit_video["fallback_url"]
    if data.get("preview") and isinstance(data["preview"], dict):
        images = data["preview"].get("images", [])
        if images:
            source = images[0].get("source", {})
            if source.get("url"):
                return source["url"]
    return ""


def format_post_row(data: dict) -> dict:
    gildings = data.get("gildings", {})
    gildings_count = sum(v for v in gildings.values() if isinstance(v, (int, float))) if isinstance(gildings, dict) else gildings

    return {
        "type": "post",
        "id": data.get("name", data.get("id", "")),
        "parent_id": "",
        "author": data.get("author", ""),
        "author_fullname": data.get("author_fullname", ""),
        "replying_to_user": "",
        "score": data.get("score", 0),
        "created_time": utc_to_iso(data.get("created_utc")),
        "text": data.get("title", ""),
        "media_url": resolve_media_url(data),
        "permalink": f"https://www.reddit.com{data.get('permalink', '')}",
        "subreddit": data.get("subreddit", ""),
        "gildings": gildings_count,
        "replies_count": data.get("num_comments", 0),
        "is_nsfw": str(data.get("over_18", False)).lower(),
        "is_spoiler": str(data.get("spoiler", False)).lower(),
        "is_oc": str(data.get("is_original_content", False)).lower(),
        "metadata_json": json.dumps(data, ensure_ascii=False, default=str),
    }


def format_comment_row(data: dict, author_lookup: dict) -> dict:
    parent_id = data.get("parent_id", "")
    replying_to = author_lookup.get(parent_id, "")
    gildings = data.get("gildings", {})
    gildings_count = sum(v for v in gildings.values() if isinstance(v, (int, float))) if isinstance(gildings, dict) else gildings

    return {
        "type": "comment",
        "id": data.get("name", data.get("id", "")),
        "parent_id": parent_id,
        "author": data.get("author", ""),
        "author_fullname": data.get("author_fullname", ""),
        "replying_to_user": replying_to,
        "score": data.get("score", 0),
        "created_time": utc_to_iso(data.get("created_utc")),
        "text": data.get("body", ""),
        "media_url": "",
        "permalink": f"https://www.reddit.com{data.get('permalink', '')}",
        "subreddit": data.get("subreddit", ""),
        "gildings": gildings_count,
        "replies_count": 0,
        "is_nsfw": "",
        "is_spoiler": "",
        "is_oc": "",
        "metadata_json": json.dumps(data, ensure_ascii=False, default=str),
    }


class RedditClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._authenticate()

    def _authenticate(self):
        device_id = str(uuid.uuid4())
        resp = self.session.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(ANDROID_CLIENT_ID, ""),
            data={
                "grant_type": "https://oauth.reddit.com/grants/installed_client",
                "device_id": device_id,
            },
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        print("OAuth authenticated successfully.")

    def get_json(self, url: str, params: dict | None = None) -> dict:
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()


def scrape_subreddit(client: RedditClient, subreddit: str, limit: int = 100, sort: str = "hot"):
    after = None
    fetched = 0

    while fetched < limit:
        params = {"limit": min(100, limit - fetched), "raw_json": 1}
        if after:
            params["after"] = after

        url = f"https://oauth.reddit.com/r/{subreddit}/{sort}"

        try:
            data = client.get_json(url, params=params)
        except requests.HTTPError:
            break

        children = data["data"]["children"]
        if not children:
            break

        for child in children:
            if child["kind"] != "t3":
                continue
            yield child["data"]
            fetched += 1
            if fetched >= limit:
                break

        after = data["data"].get("after")
        if not after:
            break

        time.sleep(1.5)


def scrape_comments(client: RedditClient, subreddit: str, post_id: str) -> tuple[dict, list[dict], dict]:
    url = f"https://oauth.reddit.com/r/{subreddit}/comments/{post_id}"
    data = client.get_json(url, params={"raw_json": 1})

    post_data = None
    if data and data[0]["data"]["children"]:
        post_data = data[0]["data"]["children"][0]["data"]

    author_lookup = {}
    if post_data:
        author_lookup[post_data.get("id")] = post_data.get("author", "")

    comments = []
    if len(data) > 1:
        walk_comments(data[1]["data"]["children"], author_lookup, comments)

    return post_data, comments, author_lookup


def walk_comments(children, author_lookup, results):
    for child in children:
        if child["kind"] != "t1":
            continue
        c = child["data"]
        author_lookup[c.get("parent_id", "")] = c.get("author", "")
        results.append(c)
        replies = c.get("replies")
        if isinstance(replies, dict):
            walk_comments(replies["data"]["children"], author_lookup, results)


def save_to_csv(rows: list[dict], filename: str):
    if not rows:
        print("No data to save.")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {filename}")


def main():
    print("Reddit Post Ingestion Tool")
    print("━" * 50)

    subreddit = input("Enter subreddit name (without r/): ").strip()
    if not subreddit:
        print("Error: Subreddit name is required")
        return

    try:
        limit = int(prompt_default("Number of posts to fetch", "25"))
    except ValueError:
        limit = 25

    sort = prompt_default("Sort order (hot/new/rising/top)", "hot")
    if sort not in ("hot", "new", "rising", "top"):
        print(f"Invalid sort '{sort}', defaulting to hot")
        sort = "hot"

    keyword = prompt_default("Enter keyword to filter by (leave empty for no filter)", "")

    output_default = f"output/{subreddit}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output_file = prompt_default("Output file", output_default)

    print("━" * 50 + "\n")

    print(f"  Subreddit: r/{subreddit}")
    print(f"  Sort:      {sort}")
    print(f"  Limit:     {limit} posts")
    if keyword:
        print(f"  Keyword:   {keyword}")
    print()

    client = RedditClient()

    print("Fetching posts...")
    all_rows = []

    for i, post_data in enumerate(scrape_subreddit(client, subreddit, limit=limit, sort=sort), 1):
        post_id = post_data.get("id")
        title = post_data.get("title", "")

        title_matches = not keyword or keyword.lower() in title.lower()

        if not title_matches:
            print(f"  [{i}/{limit}] (filtered) Post: {title[:60]}...")
            continue

        post_row = format_post_row(post_data)
        all_rows.append(post_row)
        print(f"  [{i}/{limit}] Post: {title[:60]}...")

        print(f"         Fetching comments...")
        _, comment_data_list, author_lookup = scrape_comments(client, subreddit, post_id)
        for c in comment_data_list:
            if not keyword or keyword.lower() in c.get("body", "").lower():
                all_rows.append(format_comment_row(c, author_lookup))
        print(f"         {len(comment_data_list)} comment(s) collected.")
        time.sleep(1.5)

    print(f"\nTotal rows: {len(all_rows)} (posts + comments)")

    os.makedirs("output", exist_ok=True)
    print(f"Saving to {output_file}...")
    save_to_csv(all_rows, output_file)
    print("\nDone!")


if __name__ == "__main__":
    main()
