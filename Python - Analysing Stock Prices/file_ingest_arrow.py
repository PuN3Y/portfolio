# Initial read of all stock prices
import os
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pv

_ARROW_SCHEMA = {
    "date": pa.date32(), "open": pa.float32(), "high": pa.float32(),
    "low": pa.float32(), "close": pa.float32(), "adj_close": pa.float32(),
    "volume": pa.int64(),
}

def arrow_mapper(file_chunk, directory, columns):
    """Arrow equivalent of mapper(). Returns (data, files_read)."""
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
