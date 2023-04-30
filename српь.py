import csv
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--number", type=int, default=2, help="minimum number of members")
parser.add_argument("--place", type=str, help="place")
args = parser.parse_args()

memories = []
with open('infinity.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter='_')
    for row in reader:
        if row['members'].count(", ") + 1 >= args.number and row['place'] == args.place:
            memory = {'date': int(row['date']), 'name': row['name'], 'tag': row['tag']}
            memories.append(memory)

with open('memories.json', 'w') as jsonfile:
    json.dump(memories, jsonfile)
