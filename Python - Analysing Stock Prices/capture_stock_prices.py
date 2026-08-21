import argparse
import csv
import os
import sys
import time
import yfinance as yf

START_DATE = "2007-01-01"
END_DATE = "2026-01-01"
PRICES_DIR = "prices"
SYMBOLS_FILE = "nasdaqlisted.txt"
REQUEST_DELAY = 0.05
MAX_RETRIES = 3

COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]


def load_symbols(path, include_etfs=False):
    """Load ticker symbols from either a plain list or a NASDAQ listing file.

    Accepts both:
      - one ticker per line (blank lines and # comments ignored)
      - NASDAQ's pipe-delimited nasdaqlisted.txt

    For the NASDAQ format, test issues are always dropped and ETFs are
    dropped unless include_etfs is True.
    """
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

def fetch_symbol(symbol, start, end):
    """Fetch one symbol's history. Returns a DataFrame, or None if unavailable."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.Ticker(symbol).history(
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
            )
            if df.empty:
                return None
            return df
        except Exception as exc:
            if attempt == MAX_RETRIES:
                print(f"  {symbol}: failed after {MAX_RETRIES} attempts ({exc})")
                return None
            # Back off progressively rather than hammering a rate limit
            time.sleep(2 ** attempt)
    return None

def write_csv(symbol, df, out_dir):
    """Write the DataFrame to prices/<symbol>.csv in the target schema."""
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
    args = parser.parse_args()

    symbols = args.symbols or load_symbols(args.symbol_file, args.include_etfs)
    symbols = [s.upper() for s in symbols]
    if args.limit:
        symbols = symbols[:args.limit]
    os.makedirs(args.out, exist_ok=True)

    print(f"{len(symbols)} symbols | {args.start} to {args.end} | -> {args.out}/\n")

    downloaded = skipped = failed = 0

    for i, symbol in enumerate(symbols, 1):
        out_path = os.path.join(args.out, f"{symbol}.csv")

        if os.path.exists(out_path) and not args.force:
            skipped += 1
            continue

        print(f"[{i}/{len(symbols)}] {symbol}", end=" ")
        df = fetch_symbol(symbol, args.start, args.end)

        if df is None:
            print("- no data")
            failed += 1
        else:
            write_csv(symbol, df, args.out)
            print(f"- {len(df)} rows")
            downloaded += 1

        time.sleep(REQUEST_DELAY)

    print(
        f"\nDone. {downloaded} downloaded, {skipped} already present, {failed} failed."
    )
    if failed:
        print("Failures are usually delisted tickers or symbols renamed since 2026.")

if __name__ == "__main__":
    main()
