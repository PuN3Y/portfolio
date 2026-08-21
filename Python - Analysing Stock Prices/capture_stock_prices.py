import argparse
import csv
import logging
import os
import sys
import time

import yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

START_DATE = "2007-01-01"
END_DATE = "2026-01-01"
PRICES_DIR = "prices"
SYMBOLS_FILE = "nasdaqlisted.txt"
REQUEST_DELAY = 0.05
MAX_RETRIES = 1
PROGRESS_EVERY = 50
FAILED_LOG = "failed_symbols.csv"

COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]

def load_symbols(path, include_etfs=False):
    if not os.path.exists(path):
        sys.exit(
            f"No symbol list found at '{path}'.\n"
            "Use a plain list, NASDAQ's nasdaqlisted.txt, or --symbols AAPL MSFT ..."
        )

    with open(path, encoding="utf-8") as f:
        first = f.readline()
        f.seek(0)

        # NASDAQ listing files are pipe-delimited with a Symbol column
        if "|" in first and "Symbol" in first:
            reader = csv.DictReader(f, delimiter="|")
            symbols, dropped_test, dropped_etf = [], 0, 0

            for row in reader:
                symbol = (row.get("Symbol") or "").strip().upper()

                # Trailing footer line: "File Creation Time: ...|||||||"
                if not symbol or symbol.startswith("FILE CREATION"):
                    continue
                # Test tickers exist purely for exchange system checks
                if row.get("Test Issue", "").strip().upper() == "Y":
                    dropped_test += 1
                    continue
                if not include_etfs and row.get("ETF", "").strip().upper() == "Y":
                    dropped_etf += 1
                    continue
                # Suffixed symbols (warrants, preferred, classes) use different
                # conventions on Yahoo and mostly 404 — skip them
                if not symbol.isalpha():
                    continue

                symbols.append(symbol)

            print(
                f"Parsed NASDAQ listing: {len(symbols)} symbols "
                f"({dropped_test} test issues, {dropped_etf} ETFs excluded)"
            )
            return symbols

        # Plain one-per-line list
        return [
            line.strip().upper()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

def fetch_symbol(symbol, start, end, retry_empty=False):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.Ticker(symbol).history(
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
            )
            if not df.empty:
                return df, None
            if not retry_empty or attempt == MAX_RETRIES:
                return None, "no data returned"
        except Exception as exc:
            if attempt == MAX_RETRIES:
                return None, f"{type(exc).__name__}: {exc}"
        # Back off progressively rather than hammering a rate limit
        time.sleep(2 ** attempt)
    return None, "no data returned"

def write_csv(symbol, df, out_dir):
    path = os.path.join(out_dir, f"{symbol}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for date, row in df.iterrows():
            writer.writerow([
                date.strftime("%Y-%m-%d"),
                round(row["Open"], 4),
                round(row["High"], 4),
                round(row["Low"], 4),
                round(row["Close"], 4),
                round(row.get("Adj Close", row["Close"]), 4),
                int(row["Volume"]),
            ])
    return path

def main():
    parser = argparse.ArgumentParser(description="Download NASDAQ daily prices.")
    parser.add_argument("--symbols", nargs="+", help="Tickers to fetch (overrides symbols.txt)")
    parser.add_argument("--start", default=START_DATE, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", default=END_DATE, help="End date, YYYY-MM-DD")
    parser.add_argument("--out", default=PRICES_DIR, help="Output directory")
    parser.add_argument("--force", action="store_true", help="Re-download existing files")
    parser.add_argument("--symbol-file", default=SYMBOLS_FILE, help="Plain list or nasdaqlisted.txt")
    parser.add_argument("--include-etfs", action="store_true", help="Keep ETFs from a NASDAQ listing")
    parser.add_argument("--limit", type=int, help="Only fetch the first N symbols")
    parser.add_argument("--verbose", action="store_true", help="Print a line per symbol")
    parser.add_argument("--retry-empty", action="store_true", help="Retry empty results (distinguishes throttling from delisting)")
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY, help="Seconds between requests")
    args = parser.parse_args()

    symbols = args.symbols or load_symbols(args.symbol_file, args.include_etfs)
    symbols = [s.upper() for s in symbols]
    if args.limit:
        symbols = symbols[:args.limit]
    os.makedirs(args.out, exist_ok=True)

    print(f"{len(symbols)} symbols | {args.start} to {args.end} | -> {args.out}/")

    # Resume: anything already written is skipped unless --force
    pending = [
        s for s in symbols
        if args.force or not os.path.exists(os.path.join(args.out, f"{s}.csv"))
    ]
    skipped = len(symbols) - len(pending)
    if skipped:
        print(f"{skipped} already downloaded, {len(pending)} to fetch")
    print()

    downloaded, failures = 0, []
    started = time.monotonic()

    for i, symbol in enumerate(pending, 1):
        df, reason = fetch_symbol(symbol, args.start, args.end, args.retry_empty)

        if df is None:
            failures.append((symbol, reason))
            if args.verbose:
                print(f"  {symbol}: {reason}")
        else:
            write_csv(symbol, df, args.out)
            downloaded += 1
            if args.verbose:
                print(f"  {symbol}: {len(df)} rows")

        # One line per PROGRESS_EVERY symbols keeps the notebook readable
        if not args.verbose and (i % PROGRESS_EVERY == 0 or i == len(pending)):
            rate = i / max(time.monotonic() - started, 1e-9)
            print(
                f"{i:,}/{len(pending):,} processed | "
                f"{downloaded:,} ok | {len(failures):,} failed | "
                f"{rate:.1f}/s",
                flush=True,
            )

        time.sleep(args.delay)

    elapsed = time.monotonic() - started
    print(f"\nDone in {elapsed/60:.1f} min: {downloaded:,} downloaded, "
          f"{skipped:,} already present, {len(failures):,} failed.")

    if failures:
        with open(FAILED_LOG, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["symbol", "reason"])
            writer.writerows(failures)

        share = len(failures) / max(len(pending), 1)
        print(f"Failure detail written to {FAILED_LOG} ({share:.0%} of attempted).")
        print("Symbols listed in nasdaqlisted.txt as of 2017 may since have been "
              "delisted, acquired or renamed. Note that Yahoo also returns an "
              "empty result when rate limiting, so a high failure rate at a low "
              "--delay may not all be genuine: re-run a sample with "
              "--retry-empty --delay 1.0 to check.")

if __name__ == "__main__":
    main()
