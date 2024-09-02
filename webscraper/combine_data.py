# Combine both csv files
import pandas as pd

df1 = pd.read_csv('dish_parts.csv')
df2 = pd.read_csv('fridge_parts.csv')

combined_df = pd.concat([df1, df2])
combined_df.to_csv('combined_file.csv', index=False)

# Combine both json files
import json

with open('dish_parts.json', 'r') as f1:
    data1 = json.load(f1)

with open('fridge_parts.json', 'r') as f2:
    data2 = json.load(f2)

combined_data = data1 + data2

with open('combined_file.json', 'w') as f_out:
    json.dump(combined_data, f_out, indent=4)