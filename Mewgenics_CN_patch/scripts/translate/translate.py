import json
import os
import requests
import time
import sys

# Configuration
API_URL = "<YOUR_API_ENDPOINT>"
API_KEY = "<YOUR_API_KEY>"
MODEL = "gemini-3-pro-preview" 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSONS_DIR = os.path.join(BASE_DIR, "jsons")
TERMINOLOGY_FILE = os.path.join(BASE_DIR, "terms.json")
TRANSLATE_FILE = os.path.join(BASE_DIR, "translations.json")

FILES_TO_PROCESS = [
    "teamnames.json",
]

# Chunk size (number of items per request)
CHUNK_SIZE = 150

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_json_dict(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_existing_terms_dict(terms_list):
    return {(item['original'], item['type']): (item['translation'], item['notes']) for item in terms_list}

def form_json_dict(terms_list):
    return { item['original'] + ":" + item['type']: item['translation']  for item in terms_list }
def call_llm(chunk, existing_terms_dict):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/KiloCode/Mewgenics-Translation", # Optional
        "X-Title": "Mewgenics Translation Script" # Optional
    }


    system_prompt = """
你是一位专业的游戏本地化专家，正在负责《Mewgenics》（猫咪养成Roguelike战棋游戏）的中文翻译工作。
你的任务是阅读给定的游戏文本片段（JSON格式），将其翻译为中文文本。

**注意事项：**
1. **保留标签**：文本中的 `[m:happy]`, `[s:1.5]`, `[b]`, `{catname}` 等标签必须完全保留。此外不要在原文没有的地方添加任何标签。
    标签的含义如下：
    - `[m:happy]`：表示对话中角色表情（例如 happy, sad, angry 等）
    - `[s:1.5]`：表示文字缩放倍数
    - `[b]...[/b]`：表示粗体文本
    - `{Catname}`：表示会被替换为猫咪名字的占位符
    - `[w:500]`：表示等待500毫秒
    - `[c:color]`：表示文本颜色（例如 red, blue, green 等）
    - `[img:icon]`：表示插入图标（例如 heart, star 等）
    - `&nbsp;`：表示不换行空格

2. **翻译质量**：请确保翻译准确、自然，符合中文玩家的习惯。
3. **一致性**：参考提供的“已翻译术语表”，确保相同的同类型术语翻译保持一致。
4. **上下文**：利用 `KEY` 字段来判断文本的类型（例如 `ABILITY_` 开头的是技能）。

**输出格式：**
请仅输出一个合法的 JSON 列表，不包含 markdown 格式标记（如 ```json）。列表中的每个元素是一个对象，包含以下字段：
- `source_key`: 来源的 KEY（方便回溯）。
- `zh`: 英文文本的中文翻译。

**示例输入：**
[
    {"KEY": "ABILITY_FIREBALL_DESC", "en": "Shoot a fireball that inflicts Burn 2."},
    {"KEY": "ITEM_SWORD_NAME", "en": "Iron Sword"}
]

注意，输入中可能包含 notes 字段，表示对该文本的额外说明，不需要翻译，但可以帮助理解该字段含义。

**示例输出：**
[
    {"source_key": "ABILITY_FIREBALL_DESC", "zh": "发射一颗火球，造成 2 层灼烧效果。"},
    {"source_key": "ITEM_SWORD_NAME", "zh": "铁剑"}
]
"""

    user_prompt = f"""
**术语列表**
条目格式由 original : type 映射到 translation ，其中 type 是术语类型， translation是翻译结果
请尽可能按照术语表翻译，以保持翻译质量和一致性。**你应该在翻译时直接翻译成对应的结果，而不是采用引用的方式**（如：“使用近战攻击” 而不应该出现 “使用 [melee attack]”）。

{json.dumps(existing_terms_dict, ensure_ascii=False)}

**待处理文本片段：**
本部分文件是`teamnames.json`，是游戏中的队伍名称系统

{json.dumps(chunk, ensure_ascii=False)}

请提取并翻译术语，翻译前深度思考：
"""
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": { "type": "json_object" } 
    }

    response = None
    try:
        print(f"Sending request to {MODEL} with {len(chunk)} items...")
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        print(result['usage'])

        
        content = result['choices'][0]['message']['content']
        # Clean up potential markdown code blocks if the model ignores instructions
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        parsed_json = json.loads(content)
        if isinstance(parsed_json, dict):
            # Sometimes models wrap the list in a key like "terms" or "terms"
            for key in parsed_json:
                if isinstance(parsed_json[key], list):
                    return parsed_json[key]
            # If no list found, return empty or try to force it?
            print("Warning: LLM returned a dict but no list found inside.")
            return []
        elif isinstance(parsed_json, list):
            return parsed_json
        else:
            print("Warning: LLM returned unexpected JSON structure.")
            return []

    except Exception as e:
        print(f"Error calling LLM: {e}")
        if response:
            try:
                print(f"Response content: {response.text}")
            except:
                pass
        return []

def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        return

    all_terms = load_json(TERMINOLOGY_FILE)
    translated_parts = load_json_dict(TRANSLATE_FILE)

    if not isinstance(all_terms, list):
        all_terms = []
    
    
    print(f"Loaded {len(all_terms)} existing terms.")

    for filename in FILES_TO_PROCESS:
        filepath = os.path.join(JSONS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Skipping {filename} (not found)")
            continue
            
        print(f"Processing {filename}...")
        file_data = load_json(filepath)
        
        # Filter out items that don't have 'en' or 'KEY'
        valid_data = [item for item in file_data if 'en' in item and 'KEY' in item and item['en'].strip()]
        print(f"  Found {len(valid_data)} valid items with 'en' and 'KEY' fields.")
        valid_data = [ item for item in valid_data if item['KEY'] not in translated_parts ]  # Skip already translated items
        print(f"  {len(valid_data)} items left after filtering out already translated ones.")
        total_chunks = (len(valid_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
        chunk_count = 0
        start = 0
        end = CHUNK_SIZE
        def is_same_key_group(key1, key2):
            key1_prefix = key1.split('_')[:-1] # Remove last part
            key2_prefix = key2.split('_')[:-1]
            key1_prefix = '_'.join(key1_prefix)
            key2_prefix = '_'.join(key2_prefix)
            
            # for ability，ABILITY_SNACK and ABILITY_SNACK2C should be in the same group, so we need to remove the last part of the key
            key2_prefix = key2_prefix.rstrip('0123456789') # Remove trailing numbers for grouping


            return key1_prefix == key2_prefix

        while start < len(valid_data):
            while(end > len(valid_data)):
                end -= 1
            while end < len(valid_data) and is_same_key_group(valid_data[end-1]['KEY'], valid_data[end]['KEY']):
                end += 1
                if end >= len(valid_data):
                    break
        
            chunk = valid_data[start:end]  # Add a few extra items to help with context
            print(f"  Processing chunk {chunk_count} ({len(chunk)} items)...[{start},{end}) of {len(valid_data)}")
            
            llm_existing_terms_dict = form_json_dict(all_terms)
            translated = call_llm(chunk, llm_existing_terms_dict)
            
            # Merge new terms
            added_count = 0
            for item in translated:
                source_key = item['source_key']
                en = ''
                for original_item in chunk:
                    if original_item['KEY'] == source_key:
                        en = original_item['en']
                        break
                zh = item['zh']
                if source_key not in translated_parts:
                    translated_parts[source_key] = {
                        "en": en,
                        "zh": zh
                    }
                    added_count += 1

            print(f"  Extracted {len(translated_parts)} terms, {added_count} new.")
            if added_count == 0:
                print("No new terms extracted, stopping to avoid infinite loop.")
                break
            # Save progress after each chunk
            save_json(TRANSLATE_FILE, translated_parts)
            
            # Rate limiting / politeness
            time.sleep(3)
            start = end
            end = start + CHUNK_SIZE

    print("Done! Translation complete.")

if __name__ == "__main__":
    main()
