# Reddit Post & Comment Ingestion

Scrapes posts and comments from a subreddit to CSV with full metadata — ready for crisis management pipelines, sentiment analysis, or research.

Uses Reddit's Android app OAuth (no app registration needed).

---

## Setup

```bash
# Clone the repo
git clone git@github.com:mbchavez27/reddit-post-ingestion.git
cd reddit-post-ingestion

# Sync dependencies
uv sync
```

That's it. `uv sync` installs Python and all dependencies automatically.

---

## Usage

```bash
# Basic — scrape 25 hot posts from r/UAAP
uv run reddit-ingest --subreddit UAAP

# Custom limit and sort
uv run reddit-ingest --subreddit UAAP --limit 50 --sort new

# Custom output path
uv run reddit-ingest --subreddit UAAP --limit 10 --output my_data.csv
```

Or run the script directly:

```bash
uv run reddit_comments_ingestion.py --subreddit UAAP --limit 25
```

---

## CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--subreddit` | *(required)* | Subreddit name without `r/` |
| `--limit` | `25` | Number of posts to scrape |
| `--sort` | `hot` | Sort order: `hot`, `new`, `rising`, `top` |
| `--output` | `output/{subreddit}_{timestamp}.csv` | Output CSV path |

---

## Output CSV Format

| Column | Description |
|---|---|
| `type` | `post` or `comment` |
| `id` | Full ID with type prefix (e.g. `t3_1uht4wn`) |
| `parent_id` | Parent post/comment ID (for thread hierarchy) |
| `author` | Reddit username |
| `author_fullname` | Reddit internal user ID (e.g. `t2_hr6jdj7b`) |
| `replying_to_user` | Username of the parent commenter |
| `score` | Upvote count |
| `created_time` | ISO 8601 timestamp |
| `text` | Post title or comment body |
| `media_url` | Image/video URL (posts only) |
| `permalink` | Full Reddit URL |
| `subreddit` | Subreddit name |
| `gildings` | Award count |
| `replies_count` | Number of replies (posts only) |
| `is_nsfw` | NSFW flag |
| `is_spoiler` | Spoiler flag |
| `is_oc` | Original content flag |
| `metadata_json` | Full Reddit API metadata blob |

---

## Example Output

```
==================================================
       Reddit Post & Comment Ingestion
==================================================
  Subreddit: r/UAAP
  Sort:      hot
  Limit:     1 posts

OAuth authenticated successfully.
Fetching posts...
  [1/1] Post: MEGATHREAD: Divine Adili and Rene Baterbonia...
         Fetching comments...
         128 comment(s) collected.

Total rows: 129 (posts + comments)
Saving to output/UAAP_20260821_074038.csv...
Saved 129 rows to output/UAAP_20260821_074038.csv

Done!
```

---

## Project Files

```
reddit-post-ingestion/
├── reddit_comments_ingestion.py   <- scraper source
├── pyproject.toml                 <- project metadata + dependencies
├── .gitignore                     <- ignores output/ and caches
├── uv.lock                        <- locked dependency versions
└── README.md
```

---

## How It Works

1. Authenticates via Reddit's Android app public OAuth client
2. Fetches posts from the subreddit using Reddit's API
3. For each post, recursively fetches all comments (including nested replies)
4. Exports posts + comments to a single CSV with full metadata

---

## Rate Limiting

The script includes a **1.5-second delay** between requests to avoid rate limits. Do not remove this.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `403 Forbidden` | Reddit may be temporarily blocking. Wait a few minutes. |
| `No data to save` | The subreddit may be private or non-existent. Check the name. |
| Fewer comments than expected | Some posts have locked threads or deleted comments. |
| CSV opens garbled in Excel | Open Excel -> Data -> From Text/CSV -> select UTF-8 encoding. |

---

## Dependencies

| Package | Purpose |
|---|---|
| [`requests`](https://docs.python-requests.org/) | HTTP requests to Reddit's API |

Only one external dependency. Everything else is Python stdlib (`csv`, `json`, `os`, `time`, `uuid`, `argparse`).
