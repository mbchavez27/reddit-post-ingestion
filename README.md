# Reddit Comments Ingestion

A Python script that scrapes posts from a subreddit and exports all their **comments** to a CSV file — ready for data analysis, sentiment analysis, or research.

No Reddit API key or credentials required. Uses Reddit's public `.json` endpoints directly.

When you run the script, it will **ask you interactively** for the subreddit, sort order, and number of posts.

---

## What It Does

1. Prompts you for subreddit name, sort order, and post limit
2. Fetches posts from the subreddit via Reddit's public JSON endpoint
3. For each post, recursively fetches all comments (including nested replies)
4. Exports everything to a single CSV file (`{subreddit}_comments.csv`)

---

## What It Looks Like When You Run It

```
==================================================
       Reddit Comments Ingestion
==================================================

Subreddit name (without r/): python
Sort by hot/new/rising/top (default: hot): hot
Number of posts to scrape (default: 25): 10

Scraping r/python | sort: hot | limit: 10
Found 10 post(s).

  [1/10] Fetching comments for: What's the best way to learn Python in 2026?
            42 comment(s) collected.
  [2/10] Fetching comments for: Daily Thread - General Discussion
            128 comment(s) collected.
...

Saving 487 total comment(s)...
Saved 487 rows to python_comments.csv

Done! Output: python_comments.csv
```

---

## Output CSV Format

| Column | Description |
|---|---|
| `post_id` | ID of the parent post this comment belongs to |
| `id` | Unique comment ID |
| `author` | Reddit username (or `[deleted]` if account is gone) |
| `body` | Comment text |
| `score` | Reddit upvote score |
| `created_utc` | Timestamp as Unix epoch (seconds since 1970-01-01 UTC) |

Example output filename:
```
python_comments.csv
```

---

## Project Files

```
reddit-post-ingestion/
├── reddit_comments_ingestion.py   <- the script
├── pyproject.toml                 <- project metadata + dependencies
├── .gitignore                     <- keeps caches and venvs out of Git
└── README.md
```

---

## Setup (One Time)

### Step 1 — Install `uv` (if you don't have it)

[`uv`](https://docs.astral.sh/uv/) handles Python and package installation automatically. You only need to do this once.

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2 — Install dependencies

```bash
uv add requests
```

Or with pip:

```bash
pip install requests
```

---

## Running the Script

### With `uv` (recommended)

```bash
uv run reddit_comments_ingestion.py
```

### With pip (traditional)

```bash
python reddit_comments_ingestion.py
```

---

## Runtime Prompts Explained

| Prompt | What to enter |
|---|---|
| **Subreddit name** | Just the name, no `r/` prefix (e.g. `python`, `dlsu`, `MachineLearning`) |
| **Sort by** | `hot`, `new`, `rising`, or `top` |
| **Number of posts** | How many posts to pull. Keep under 50 for speed |

---

## Rate Limiting

The script includes a **1.5-second delay** between requests. This is intentional — Reddit will temporarily block you if you send requests too fast. Do not remove this.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Request failed: 429` | You're being rate-limited. Wait a few minutes and try again with a lower post count. |
| `No data to save` | The subreddit may be private or non-existent. Check the name. |
| Fewer comments than expected | Some posts have locked threads or deleted comments that Reddit hides. |
| CSV opens garbled in Excel | Open Excel → Data → From Text/CSV → select UTF-8 encoding. |

---

## Dependencies

| Package | Purpose |
|---|---|
| [`requests`](https://docs.python-requests.org/) | HTTP requests to Reddit's JSON endpoints |

Only one external dependency. Everything else is Python stdlib (`csv`, `time`).
