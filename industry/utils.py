import csv
import os


def load_countries():
    DATA_PATH_FILE = os.path.join(os.getcwd(), "all_countries.csv")
    with open(DATA_PATH_FILE, mode='r', newline='', encoding='utf-8') as file_reader:
        csv_reader = csv.reader(file_reader)
        countries = []
        for row in csv_reader:
            countries.append(row[0])
    return countries[1:]