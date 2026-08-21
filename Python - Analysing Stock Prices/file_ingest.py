# Initial read of all stock prices
import os
import pandas as pd

def mapper(file_chunk, directory):
    stock_prices = {}
    for file in file_chunk:
        name = os.path.splitext(file)[0]
        stock_prices[name] = pd.read_csv(os.path.join(directory, file), encoding="UTF-8")
    return stock_prices, len(file_chunk)

def reducer(a, b):
    merged = dict(a)
    merged.update(b)
    return merged
