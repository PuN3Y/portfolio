# Initial read of all stock prices
import os
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pv

_ARROW_SCHEMA = {
    "date": pa.timestamp("s"),
    "open": pa.float64(),
    "high": pa.float64(),
    "low": pa.float64(),
    "close": pa.float64(),
    "adj_close": pa.float64(),
    "volume": pa.int64(),
}

def arrow_mapper(file_chunk, directory, columns):
    convert = pv.ConvertOptions(column_types=_ARROW_SCHEMA, include_columns=columns)
    read = pv.ReadOptions(use_threads=False)   # one thread per worker process

    prices = {}
    for file in file_chunk:
        table = pv.read_csv(
            os.path.join(directory, file), read_options=read, convert_options=convert
        )
        prices[os.path.splitext(file)[0]] = table.to_pandas().set_index("date")
    return prices, len(file_chunk)

def arrow_reducer(accumulated, chunk):
    accumulated.update(chunk)
    return accumulated
