import csv
import statistics


lenghts_by_level = dict()


def assign_csv_data(row):
    if row[5] in lenghts_by_level.keys():
        lenghts_by_level[row[5]].append(int(row[3]))
    else:
        lenghts_by_level[row[5]] = list()
        lenghts_by_level[row[5]].append(int(row[3]))


def main():
    with open("example.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                assign_csv_data(row)

                line_count += 1
    for key in lenghts_by_level.keys():
        print(key)
        print(statistics.stdev(lenghts_by_level[key]))


if __name__ == '__main__':
    main()
