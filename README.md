# Reddit Subreddit Scraper 🔍

A Python script that searches a subreddit by keyword and exports all matching **posts and their comments** to a CSV file — ready for data analysis, sentiment analysis, or research.

Originally written in R using `RedditExtractoR`, this version uses Python + [PRAW](https://praw.readthedocs.io/) (the official Reddit API wrapper). It is completely **free to use** and works within Reddit's standard API rate limits.

When you run the script, it will **ask you what to search for** — no need to edit any code. Your Reddit API credentials are stored safely in a `.env` file that never gets committed to Git.

---

## What It Does

1. Loads your Reddit API credentials from a `.env` file
2. Prompts you interactively for search parameters (keyword, subreddit, sort, number of posts)
3. Searches the subreddit and collects matching posts + all their comments
4. Exports everything to a structured CSV file

---

## What It Looks Like When You Run It

```
==================================================
       Reddit Subreddit Scraper 🔍
==================================================

🔑 Enter search keyword (e.g. graduation): thesis
📌 Enter subreddit name without r/ (e.g. dlsu): dlsu
   Sort options: comments, hot, new, relevance, top
📊 Sort results by (default: relevance): top
🔢 Number of posts to collect (default: 5, max recommended: 50): 10

▶️  Searching r/dlsu for 'thesis' | sort: top | limit: 10

   Found 10 post(s).

🔄 Processing post 1/10: https://www.reddit.com/r/dlsu/...
   ✅ 24 row(s) (1 post + 23 comments)
...

✅ Done! 187 total rows exported to:
   /your/path/reddit_dlsu_thesis_top10_posts.csv
```

---

## Output CSV Format

| Column | Description |
|---|---|
| `post_url` | Direct link to the Reddit thread |
| `title` | Title of the post |
| `author` | Reddit username (or `[deleted]` if account is gone) |
| `date` | Timestamp in `YYYY-MM-DD HH:MM:SS` format (UTC) |
| `text` | Post body or comment text |
| `score` | Reddit upvote score |
| `type` | Either `post` or `comment` |

The file is saved as **UTF-8 with BOM** (`utf-8-sig`) so it opens correctly in Excel — important for non-ASCII characters.

Example output filename:
```
reddit_dlsu_thesis_top10_posts.csv
```

---

## Project Files

```
📁 your-folder/
├── reddit_scraper.py   ← the script
├── .env                ← your credentials (you create this, never commit it)
├── .env.example        ← safe template to show what .env should look like
├── .gitignore          ← keeps .env and CSVs out of Git
└── README.md
```

---

## Setup (One Time)

### Step 1 — Get your Reddit API credentials (free, 2 minutes)

1. Log in to Reddit and go to **https://www.reddit.com/prefs/apps**
2. Scroll down and click **"create another app..."**
3. Fill in the form:
   - **Name:** anything (e.g. `my_scraper`)
   - **Type:** select **script**
   - **Redirect URI:** `http://localhost:8080`
4. Click **"create app"**
5. On the app listing, copy:
   - The string **under the app name** → `client_id`
   - The string next to **"secret"** → `client_secret`

### Step 2 — Create your `.env` file

In the same folder as `reddit_scraper.py`, create a file named exactly `.env` (no extension) and fill it in:

```env
REDDIT_CLIENT_ID=paste_your_client_id_here
REDDIT_CLIENT_SECRET=paste_your_client_secret_here
REDDIT_USER_AGENT=reddit_scraper/1.0 by your_reddit_username
```

You can use `.env.example` as a starting point — just copy it and rename it to `.env`.

> ⚠️ Never share your `.env` file or commit it to Git. The `.gitignore` in this project already excludes it.

### Step 3 — Install `uv` (if you don't have it)

[`uv`](https://docs.astral.sh/uv/) handles Python and package installation automatically. You only need to do this once.

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Running the Script

### With `uv` (recommended — no virtual env or pip needed)

```bash
uv run reddit_scraper.py
```

`uv` reads the dependencies declared at the top of the script and installs them automatically in an isolated environment. Nothing else needed.

### With pip (traditional)

```bash
pip install praw pandas python-dotenv
python reddit_scraper.py
```

---

## Runtime Prompts Explained

| Prompt | What to enter |
|---|---|
| **Search keyword** | The word or phrase to search for (e.g. `graduation`, `enrollment`, `thesis defense`) |
| **Subreddit name** | Just the name, no `r/` prefix (e.g. `dlsu`, `phcareers`, `Philippines`) |
| **Sort by** | How to rank results — `relevance` is usually best for research; `top` gives the most upvoted |
| **Number of posts** | How many posts to pull. Keep under 50 for speed and to stay within rate limits |

---

## Rate Limiting

The script includes a **2-second delay** between each post request. This is intentional — Reddit's API will temporarily block you if you send requests too fast. Do not remove this.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `❌ Missing Reddit credentials` | Your `.env` file is missing or has wrong variable names. Check it matches `.env.example` exactly. |
| `received 401 HTTP response` | Your `client_id` or `client_secret` is incorrect. Re-copy them from Reddit. |
| `❌ No threads found` | Try a different keyword or sort option. The subreddit may have no posts matching that term. |
| CSV opens garbled in Excel | Open Excel → Data → From Text/CSV → select UTF-8 encoding. The script uses `utf-8-sig` which Excel should detect automatically. |
| Script exits immediately | Make sure you're running from the same folder as your `.env` file. |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| [`praw`](https://praw.readthedocs.io/) | ≥ 7.7 | Official Reddit API wrapper |
| [`pandas`](https://pandas.pydata.org/) | ≥ 2.0 | Data structuring and CSV export |
| [`python-dotenv`](https://pypi.org/project/python-dotenv/) | ≥ 1.0 | Loads credentials from `.env` file |

All free and open-source.
