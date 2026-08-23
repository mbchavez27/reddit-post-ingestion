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
uv run python reddit_comments_ingestion.py
```

The tool runs interactively — it will prompt you for all options:

```
Reddit Post Ingestion Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enter subreddit name (without r/): UAAP
Number of posts to fetch [25]:
Sort order (hot/new/rising/top) [hot]:
Enter keyword to filter by (leave empty for no filter): UAAP
Output file [output/UAAP_20260823_123456.csv]:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Subreddit: r/UAAP
  Sort:      hot
  Limit:     25 posts
  Keyword:   UAAP
```

---

## Batch Ingestion

For fetching multiple posts from a CSV of Reddit URLs:

```bash
uv run python batch_reddit_ingestion.py
```

### Supported URL formats

- `https://www.reddit.com/r/SUBREDDIT/comments/POST_ID/slug/`
- `https://www.reddit.com/comments/POST_ID`
- Raw post IDs

### Interactive prompts

```
Reddit Batch Ingestion Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enter path to CSV file: posts.csv
Enter column name (or press Enter to auto-detect):
Enter keyword to filter by (leave empty for no filter):
Output mode (all/per) [all]:
Output file [output/batch_20260823_123456.csv]:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Output modes

| Mode | Description |
|---|---|
| `all` | All posts + comments merged into a single CSV |
| `per` | One CSV per post in a user-named folder (e.g. `output/my_batch/abc123.csv`) |

The tool auto-detects the URL column (`url`, `link`, `reddit_url`, `post_url`, `post_link`) or scans all cells for Reddit links.

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
Reddit Post Ingestion Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enter subreddit name (without r/): UAAP
Number of posts to fetch [25]: 50
Sort order (hot/new/rising/top) [hot]:
Enter keyword to filter by (leave empty for no filter): UAAP
Output file [output/UAAP_20260821_074038.csv]:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Subreddit: r/UAAP
  Sort:      hot
  Limit:     50 posts
  Keyword:   UAAP

OAuth authenticated successfully.
Fetching posts...
  [1/50] Post: MEGATHREAD: UAAP Season 87...
         Fetching comments...
         42 comment(s) collected.
  [2/50] (filtered) Post: Random basketball question...
  [3/50] Post: UAAP highlights thread...
         Fetching comments...
         18 comment(s) collected.

Total rows: 61 (posts + comments)
Saving to output/UAAP_20260821_074038.csv...
Saved 61 rows to output/UAAP_20260821_074038.csv

Done!
```

---

## Project Files

```
reddit-post-ingestion/
├── reddit_comments_ingestion.py   <- single-subreddit scraper
├── batch_reddit_ingestion.py      <- CSV-driven batch scraper
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

## Keyword Filtering

The tool supports case-insensitive keyword filtering across posts and comments:

- **Posts**: filtered by title before fetching comments (saves API calls)
- **Comments**: filtered by body text after fetching
- Leave the keyword prompt empty to fetch everything (no filter)

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

Only one external dependency. Everything else is Python stdlib (`csv`, `json`, `os`, `time`, `uuid`).
