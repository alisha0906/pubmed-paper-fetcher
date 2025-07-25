# 📰 PubMed Paper Fetcher

**Find industry-authored biomedical papers in seconds**  
A fast, scriptable CLI that queries PubMed, detects papers with at least one **pharma / biotech author**, and exports the results as a tidy CSV.

---

## 🚀  Key Features

| Capability | Details |
|------------|---------|
| 🔍 **Flexible Query** | Accepts *any* PubMed query syntax (Boolean, MeSH, date ranges, etc.). |
| 🏢 **Industry Detection** | Flags authors whose affiliations look like companies (Inc, Ltd, Pharma, Biotech …) and ignores purely academic addresses. |
| 📑 **Rich CSV Output** | `PubmedID · Title · Publication Date · Non-academic Author(s) · Company Affiliation(s) · Corresponding Email` |
| 💬 **Verbose / Quiet Modes** | `-d` flag prints every API call and parsing step; default keeps output clean. |
| 💾 **Export or Pipe** | Print to console *or* save directly to a file with `-f results.csv`. |
| ⚡ **Progress Bar** | Live download progress via Rich. |
| ⏱️ **Fast, Parallel Batching** | Fetches up to 200 articles per API call (polite to NCBI). |
| 🛠 **Extensible Filters** | Company/academic keyword lists are centralised—swap in your own domain rules easily. |

---

## 🛠  Setup Instructions

### 1  Clone & create a virtual environment

```bash
git clone https://github.com/<YOUR_USER>/pubmed-paper-fetcher.git
cd pubmed-paper-fetcher

python -m venv .venv                      # optional but recommended
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

```

### 2 Install dependencies

```bash
python -m pip install -r requirements.txt
# (Optional) editable install so CLI works everywhere in the venv
python -m pip install -e .

```
### 3 Run the CLI
```bash
# Print to console
python -m pubmed_paper_fetcher "diabetes AND insulin"

# Save top 500 hits to CSV with debug logs
python -m pubmed_paper_fetcher -l 500 -d -f diabetes_industry.csv "diabetes AND insulin"

```
### 4 Reasoning Flow
                                     
a. ESearch – Retrieves up to N PubMed IDs for the user query

b. EFetch – Downloads full XML metadata in batches (≤ 300 IDs/request)

c. XML Parser – Extracts key fields & affiliation text

d. Industry Filter – Regex rules flag non-academic authors

e. Output Layer – Builds a DataFrame → saves to CSV or prints

### 5 Extending / Customising
Company keyword list → edit the COMPANY_KEYWORDS regex in fetcher.py.

Academic exclusions → tweak ACADEMIC_KEYWORDS.

JSON output – add a --json flag and call df.to_json().

Higher concurrency – wrap efetch calls with asyncio or ThreadPoolExecutor (respect NCBI rate limits!).

### 6 Credits
Powered by NCBI E-utilities, Requests, lxml, pandas, and Rich.

Built with ❤️ for researchers, data scientists, and competitive-intelligence teams.

Enjoy your PubMed Paper Fetcher and happy hunting! 🧪
