import csv
import json
import os

def convert_csv_to_json(input_dir):
    """
    将指定目录下的所有CSV文件转换为JSON格式，仅保留前3列。
    生成的JSON文件将保存在同一目录下。
    """
    if not os.path.exists(input_dir):
        print(f"错误：目录 '{input_dir}' 不存在。")
        return

    # 遍历目录下的所有文件
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.csv'):
            csv_path = os.path.join(input_dir, filename)
            json_path = os.path.join(input_dir, os.path.splitext(filename)[0] + '.json')
            
            print(f"正在处理: {filename}...")
            
            data = []
            try:
                # 使用 utf-8-sig 编码以处理可能存在的 BOM
                with open(csv_path, mode='r', encoding='utf-8-sig', newline='') as csv_file:
                    reader = csv.reader(csv_file)
                    
                    try:
                        headers = next(reader)
                    except StopIteration:
                        print(f"  警告: {filename} 是空文件，跳过。")
                        continue
                    
                    # 仅保留前3列的表头
                    target_headers = headers[:3]
                    
                    for row in reader:
                        # 仅保留前3列的数据
                        row_data = row[:3]
                        
                        # 确保行数据长度与表头一致（处理列数不足的情况）
                        if len(row_data) < len(target_headers):
                            row_data += [''] * (len(target_headers) - len(row_data))
                        
                        # 构建字典
                        item = dict(zip(target_headers, row_data))
                        data.append(item)
                
                # 写入 JSON 文件
                with open(json_path, mode='w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, indent=4, ensure_ascii=False)
                
                print(f"  已生成: {os.path.basename(json_path)}")
                
            except Exception as e:
                print(f"  转换 {filename} 时出错: {e}")

if __name__ == "__main__":
    # 设置输入目录为当前脚本所在目录下的 file 文件夹
    # 使用相对路径，确保在不同环境下都能找到
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_directory = os.path.join(base_dir, 'file')
    
    convert_csv_to_json(input_directory)
