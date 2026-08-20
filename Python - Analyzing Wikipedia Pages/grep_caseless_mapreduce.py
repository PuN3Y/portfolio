#homemade_grep_caseless
import os

def grep_mapper_caseless(data):
    target_word = "data"
    line_index={}
    for file in data:
        with open(os.path.join("wiki", file), encoding="UTF-8") as f:
            lines = [line for line in f.readlines()]
            for i in range(len(lines)):
                if target_word in lines[i].lower():
                    if file not in line_index:
                        line_index[file]=[]
                    line_index[file].append(i)

    return line_index

def grep_reducer_caseless(lines1, lines2):
    lines1.update(lines2)
    return lines1
