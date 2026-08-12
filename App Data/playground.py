opened_file = open('AppleStore.csv', encoding='utf-8')
from csv import reader
read_file = reader(opened_file)
apps_data = list(read_file)
opened_file.close()
header = apps_data[0]

def extract(data_set, index):
    column = []
    for row in data_set[1:]:
        value = row[index]
        column.append(value)
    return column


def find_sum(a_list):
    a_sum = 0
    for element in a_list:
        a_sum += float(element)
    return a_sum


def find_length(a_list):
    length = 0
    for element in a_list:
        length += 1
    return length


def mean(data_set, index):
    column = extract(data_set, index)
    return find_sum(column) / find_length(column)


avg_price = mean(apps_data, 4)


def open_dataset(file_name):
    opened_file = open(file_name)
    from csv import reader
    read_file = reader(opened_file)
    data = list(read_file)

    return data