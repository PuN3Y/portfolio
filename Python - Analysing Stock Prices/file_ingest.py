# Initial read of all stock prices
import os
import pandas as pd

def mapper(file_chunk, directory, columns):
    prices = {}
    for file in file_chunk:
        name = os.path.splitext(file)[0]
        prices[name] = pd.read_csv(
            os.path.join(directory, file),
            usecols=columns,
            parse_dates=["date"],
            index_col="date",
            encoding="utf-8",
        )
    return prices, len(file_chunk)

def reducer(accumulated, chunk):
    accumulated.update(chunk)
    return accumulated
