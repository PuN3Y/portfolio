# Multi Processing
import os

def mapper(file_chunk):
    line_count = []
    for file in file_chunk:
        with open(os.path.join("wiki", file), encoding="UTF-8") as f:
            line_count.append(len(f.readlines()))
    return sum(line_count), len(file_chunk)

def reducer(a, b):
    return a + b
