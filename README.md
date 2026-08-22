# Portfolio

Data analysis, data engineering, and database projects in Python and SQL: working with data that doesn't fit in memory, optimising algorithms and query performance, designing databases from scratch, and investigating why data that looks fine isn't.

---

## Projects

### `Python - Analysing Stock Prices`
Nineteen years of daily NASDAQ prices (1,363 tickers, 5.4 million ticker-days) downloaded, benchmarked, and analysed.

**Ingestion benchmark.** Six loaders across a 2×3 grid: pandas and PyArrow, each run serially, on threads and on processes, with output structure held identical so the comparison isolates the method. Best result **5.4× faster than a naive loop**, and the grid shows the two parsers want opposite concurrency models, because pandas holds Python's interpreter lock while parsing and PyArrow releases it.

**Data-quality investigation.** An average closing price of $20 trillion led back, via a ruled-out suspicion of my own `float32` schema, to Yahoo's split adjustment: prices are restated in today's share count, so serial reverse splitters carry an enormous cumulative factor. Three rounds of correction reduced the error by fourteen orders of magnitude without eliminating it. Yahoo does not retain corporate actions for delisted instruments, and those are disproportionately the ones that reverse-split. Ratios survive what levels do not, so returns are the only trustworthy answer here.

**Libraries:** `pandas`, `pyarrow`, `numpy`, `matplotlib`, `yfinance`, `multiprocessing`, `csv`, `re`

---

### `Python - Analysing Wikipedia Pages`
A map/reduce framework built from scratch over a **961 MB subset of ~6,600 Wikipedia articles**, using `multiprocessing` to parallelise work across CPU cores and benchmarked against a single-process baseline.

On top of that framework, a homemade `grep` developed across three iterations, each driven by validating output against real `grep` and diagnosing the gap:

1. **Exact matching** — returns the lines in each file containing the target word. Verification against actual `grep` output showed a shortfall.
2. **Caseless matching** — diagnosed the first cause of the shortfall (case sensitivity) and corrected it.
3. **Full occurrence indexing** — diagnosed the second cause: a line containing the target word twice was still counted once. A `find_match_index` helper walks `str.find` forward from each hit to capture every occurrence, returning `(line, character index)` tuples.

Results are exported to CSV with a 15-character context window reconstructed around each match, then loaded back for review.

Mapper and reducer logic is factored into importable `.py` modules rather than left in the notebook.

**Libraries:** `multiprocessing`, `functools`, `itertools`, `importlib`, `pandas`, `csv`, `os`, `time`, `math`

---

### `Python - Loans Data`
Memory optimisation on LendingClub 2007 lending data. Dynamically sizes read chunks to ~5 MB, profiles dtypes across every chunk, and detects a column that parses as numeric in some chunks and string in others — tracing it to three malformed spacer rows. Converts low-cardinality strings to `category`, parses datetimes, strips formatting characters and downcasts numerics, **reducing the in-memory footprint roughly 3x**. Ends with a reusable cleaner function.

**Libraries:** `pandas`, `numpy`

---

### `Python and PostgreSQL - Crime Database`
Database design and administration for a Boston crime dataset, built from scratch. Samples the source CSV to size column types appropriately, including a custom `weekday` enumerated type and a length-fitted description field. Bulk-loads via `copy_expert`, revokes public schema privileges, then creates `readonly` and `readwrite` role groups with a user in each — verified by querying `pg_roles` and `information_schema.table_privileges`.

**Libraries:** `psycopg2`, `csv`

---

### `Python - Laptops`
An exercise in algorithmic complexity. Builds an `Inventory` class over a laptop catalogue, then improves three operations and empirically benchmarks each against its naive version:

| Operation | Before | After | Method |
|---|---|---|---|
| Lookup by ID | O(n) | O(1) | Dictionary index |
| Gift-card pair matching | O(n²) | O(n) | Set membership |
| Budget filtering | O(n) | O(log n) | Binary search on sorted prices |

Also handles unknown file encoding via `chardet` at load time.

**Libraries:** `csv`, `chardet`, `time`, `random`, `matplotlib`

---

### `SQL - Stores Database`
A SQL-only analysis of a scale-model retailer's sales database. Documents the schema and its relationships, profiles table sizes via `PRAGMA_TABLE_INFO`, then answers three commercial questions using CTEs, a created view and correlated subqueries:

- **What to restock** — crosses stock-depletion rate against product revenue performance
- **Who to target** — a `CustomersByRevenue` view ranking customers by realised profit
- **What to spend on acquisition** — new-customer proportions by month against average profit per customer

**Technologies:** SQLite, SQL (CTEs, views, correlated subqueries)

---

### `Python and SQLite3 - Fundraising Deals`
Crunchbase startup funding data analysed under a deliberate memory constraint: read in chunks, written to a SQLite database, then queried in SQL rather than held in a DataFrame. Explores funding rounds, investment types and amounts raised.

**Libraries:** `pandas`, `sqlite3`

---

### `Python - eBay Car Sales`
Cleaning and exploration of used-car listings from eBay Kleinanzeigen. Standardises column names to snake_case, drops three zero-variance columns, strips currency and distance characters from `price` and `odometer`, and removes implausible records — £0 listings, seven-figure outliers, and registration years reading 1000 and 9999. Concludes with mean price and mileage by brand for brands above 5% market share.

**Libraries:** `pandas`, `numpy`

---

### `Python - Gender Gap in Degrees`
Data visualisation of women's share of US bachelor's degrees, 1968–2011, across 17 majors. Uses small-multiple line charts with a colourblind-safe palette and stripped chart junk to make 17 series readable at once.

**Libraries:** `pandas`, `matplotlib`

---

### `Python - Job Outcomes of Students`
Exploratory analysis of US graduate earnings by major, working through scatter plots, histograms, a scatter matrix and bar plots to test whether popular majors earn more and whether gender composition tracks median wage.

**Libraries:** `pandas`, `matplotlib`

---

### `Python - Hacker News`
Compares Ask HN and Show HN posts to find which attracts more engagement and when to post. Buckets comment counts by hour of creation; finds 3 p.m. EST performs best at ~38.6 comments per post.

**Libraries:** `csv`, `datetime`

---

### `Python - App Data`
An early project recommending an app genre to build for, using only native Python. Cleans the Apple App Store and Google Play datasets by hand — de-duplicating on review count, filtering non-English titles by character code, isolating free apps — then builds frequency tables by genre.

**Libraries:** `csv`

---

## Notes

Several of the projects began as guided exercises hosted by Dataquest and were extended from there.