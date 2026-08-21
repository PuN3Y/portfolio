#homemade_grep_word_finder
import os

def find_match_index(line, target_word):
    results_index=[]
    i=line.find(target_word, 0)
    while i != -1:
        results_index.append(i)
        i=line.find(target_word, i+1)
    return results_index

def grep_mapper_word_finder(data):
    target_word = "data"
    results={}
    for file in data:
        with open(os.path.join("wiki", file), encoding="UTF-8") as f:
            lines=[line.lower() for line in f.readlines()]
        for line_index, line in enumerate(lines):
            match_indexes=find_match_index(line, target_word.lower())
            if file not in results:
                results[file]=[]
            results[file].extend([(line_index,match_index) for match_index in match_indexes])
    return results

def grep_reducer_word_finder(lines1, lines2):
    lines1.update(lines2)
    return lines1
