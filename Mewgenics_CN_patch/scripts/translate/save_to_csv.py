import csv
import json
import os

input_dir = 'csv'
output_dir = 'output'

translation_file = 'translations.json'

csv_list = [f for f in os.listdir(input_dir) if f.lower().endswith('.csv')]

translation_file = json.load(open(translation_file, 'r', encoding='utf-8'))

os.makedirs(output_dir, exist_ok=True)

for csv_file in csv_list:
    f = os.path.join(input_dir, csv_file)
    with open(f, mode='r', encoding='utf-8-sig', newline='') as file:
        print(f"正在处理文件: {csv_file}")
        reader = csv.reader(file)
        try:
            headers = next(reader)
        except StopIteration:
            print(f"  警告: {csv_file} 是空文件，跳过。")
            continue
        
        with open(os.path.join(output_dir, csv_file), mode='w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers) 
            
            for row in reader:
                key = row[0]  # 第一列作为 key
                row[-1] = translation_file.get(key, {'zh': row[-1]})['zh']  # 替换最后一列的值
                writer.writerow(row) 

        
    
    
