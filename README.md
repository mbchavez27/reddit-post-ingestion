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
Enter subreddit name (without r/): Philippines
Number of posts to fetch [25]:
Sort order (hot/new/rising/top) [hot]:
Required keywords (comma-separated, leave empty for none): rene
Optional keywords (comma-separated, leave empty for none): autopsy, ateneo
Output folder name [Philippines_batch]:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Subreddit: r/Philippines
  Sort:      hot
  Limit:     25 posts
  Required:  rene
  Optional:  autopsy, ateneo
```

Matching rule: **ALL required keywords AND at least 1 optional** (if any) must appear in the post title.

| Required | Optional | Post title | Match? |
|---|---|---|---|
| `rene` | `autopsy, ateneo` | "Rene Baterbonia autopsy results" | ✅ |
| `rene` | `autopsy, ateneo` | "Ateneo fan reacts to Rene incident" | ✅ |
| `rene` | `autopsy, ateneo` | "General autopsy procedures" | ❌ no rene |
| `rene` | `autopsy, ateneo` | "Ateneo wins UAAP" | ❌ no rene |

Each post is saved as a separate CSV inside the folder:

```
output/UAAP_batch/
├── abc123_megathread_uaap_season_87.csv
├── def456_uaap_highlights_thread.csv
└── ghi789_random_basketball_question.csv
```

---

## Batch Ingestion

For fetching multiple posts from a CSV or TXT file of Reddit URLs:

```bash
uv run python batch_reddit_ingestion.py
```

### Supported input formats

| Format | Description |
|---|---|
| `.csv` | Auto-detects URL column (`url`, `link`, `reddit_url`, `post_url`, `post_link`) or scans all cells |
| `.txt` | One URL per line, `#` comments supported |

### Supported URL formats

- `https://www.reddit.com/r/SUBREDDIT/comments/POST_ID/slug/`
- `https://www.reddit.com/comments/POST_ID`
- Raw post IDs

### Interactive prompts

```
Reddit Batch Ingestion Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enter path to CSV or TXT file: posts.txt
Enter column name (or press Enter to auto-detect):
Required keywords (comma-separated, leave empty for none): rene
Optional keywords (comma-separated, leave empty for none): autopsy, ateneo
Output mode (all/per) [all]:
Output file [output/batch_20260823_123456.csv]:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Output modes

| Mode | Description |
|---|---|
| `all` | All posts + comments merged into a single CSV |
| `per` | One CSV per post in a user-named folder (e.g. `output/my_batch/abc123.csv`) |

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
Enter subreddit name (without r/): Philippines
Number of posts to fetch [25]: 50
Sort order (hot/new/rising/top) [hot]:
Required keywords (comma-separated, leave empty for none): rene
Optional keywords (comma-separated, leave empty for none): autopsy, ateneo
Output folder name [Philippines_batch]:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Subreddit: r/Philippines
  Sort:      hot
  Limit:     50 posts
  Required:  rene
  Optional:  autopsy, ateneo

OAuth authenticated successfully.
Fetching posts...
  [1/50] Post: "MEATHREAD: Divine Adili and Rene Baterbonia..."
         Fetching comments...
         Saved 129 rows to output/Philippines_batch/abc123_meathread_divine_adili.csv
  [2/50] (filtered) Post: "Ateneo wins UAAP..."
  [3/50] Post: "Rene spotted at Ateneo campus..."
         Fetching comments...
         Saved 45 rows to output/Philippines_batch/def456_rene_spotted_ateneo.csv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Done! 8 posts, 312 comments
Output: output/Philippines_batch/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

The tool supports required + optional keyword matching on post titles:

- **Required keywords**: ALL must appear in the post title
- **Optional keywords**: at least 1 must appear (if any are provided)
- Posts that don't match are skipped entirely (saves API calls)
- All comments for matching posts are included (no comment filtering)
- Leave both prompts empty to fetch everything (no filter)

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
