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

FILES_TO_PROCESS = [
    "additions.json",
]

# Chunk size (number of items per request)
CHUNK_SIZE = 100

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_existing_terms_dict(terms_list):
    return {(item['original'], item['type']): (item['translation'], item['notes']) for item in terms_list}

def form_json_dict(terms_list):
    return { item['original'] + ":" + item['type']: item['translation'] + ':' + item['source_key'] for item in terms_list }
def call_llm(chunk, existing_terms_dict):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/KiloCode/Mewgenics-Translation", # Optional
        "X-Title": "Mewgenics Translation Script" # Optional
    }


    system_prompt = """
你是一位专业的游戏本地化专家，正在负责《Mewgenics》（猫咪养成Roguelike战棋游戏）的中文翻译术语提取工作。
你的任务是阅读给定的游戏文本片段（JSON格式），从中提取出需要统一翻译的“术语”（Terminology）。

**术语包括但不限于：**
1. 专有名词：角色名、地名、组织名。
2. 游戏系统词汇：属性（如 Strength, Luck）、状态效果（如 Bleed, Poison, Confusion）、货币名称。
3. 物品名称、技能名称、被动技能名称。
4. 特殊的动词或关键词（如 Cast, Downed, Revive）。

**注意事项：**
1. **保留标签**：文本中的 `[m:happy]`, `[s:1.5]`, `[b]`, `{catname}` 等标签必须完全保留，不要作为术语提取，除非它们是术语的一部分。
2. **保留英文**：中文玩家习惯使用的词汇（如 Boss, HP, EXP, NPC, DPS, Buff, Debuff）请保留英文原文，或者提供“中文(英文)”的格式，或者如果非常通用则直接保留英文。
3. **一致性**：参考提供的“已翻译术语表”，确保相同的同类型术语翻译保持一致。如果遇到已翻译的术语，可以再次输出以确认，或者忽略。
4. **上下文**：利用 `KEY` 字段来判断文本的类型（例如 `ABILITY_` 开头的是技能）。

**输出格式：**
请仅输出一个合法的 JSON 列表，不包含 markdown 格式标记（如 ```json）。列表中的每个元素是一个对象，包含以下字段：
- `original`: 英文原文（去除标签后的纯文本，或者保留必要的变量占位符）。
- `translation`: 建议的中文翻译。
- `type`: 术语类型（例如：Keyword 关键词，Skill 技能名称, Item 物品名称, Status 状态, Tile 地块，Character 角色名称, Event 事件名称，Location 地名, Misc 杂项等等）。
- `source_key`: 来源的 KEY（方便回溯）。
- `notes`: 备注（可选，解释为什么这样翻译，或者上下文信息）。

**示例输入：**
[
    {"KEY": "ABILITY_FIREBALL_DESC", "en": "Shoot a fireball that inflicts Burn 2."},
    {"KEY": "ITEM_SWORD_NAME", "en": "Iron Sword"}
]

**示例输出：**
[
    {"original": "Fireball", "translation": "火球术", "type": "Skill", "source_key": "ABILITY_FIREBALL_DESC", "notes": ""},
    {"original": "Burn", "translation": "燃烧", "type": "Status", "source_key": "ABILITY_FIREBALL_DESC", "notes": "状态效果"},
    {"original": "Iron Sword", "translation": "铁剑", "type": "Item", "source_key": "ITEM_SWORD_NAME", "notes": ""}
]
"""

    user_prompt = f"""
**已翻译术语表（参考用）：**
本部分目的是为了提供上下文和保持翻译一致性，不需要完全覆盖所有术语。请优先参考这个表格中的翻译，如果有新的术语或更好的翻译建议，可以输出新的术语对象。
条目格式由 original : type 映射到 translation:source_key ，其中 type 是术语类型， translation是翻译结果，source_key是来源KEY。

{json.dumps(existing_terms_dict, ensure_ascii=False)}

**待处理文本片段：**
本部分文件是`additions.json` 的一部分，包含了游戏中的追加文本（含语言元数据）

{json.dumps(chunk, ensure_ascii=False)}

请提取并翻译术语：
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
            # Sometimes models wrap the list in a key like "terms"
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
    if not isinstance(all_terms, list):
        all_terms = []
    
    existing_terms_dict = get_existing_terms_dict(all_terms)
    
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
        valid_data = [item for item in valid_data if not item['KEY'].startswith("QEVENT_")]
        total_chunks = (len(valid_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        for i in range(0, len(valid_data), CHUNK_SIZE):
            chunk = valid_data[i:i + CHUNK_SIZE + 10]  # Add a few extra items to help with context
            print(f"  Processing chunk {i // CHUNK_SIZE + 1}/{total_chunks} ({len(chunk)} items)...")
            
            llm_existing_terms_dict = form_json_dict(all_terms)
            new_terms = call_llm(chunk, llm_existing_terms_dict)
            
            # Merge new terms
            added_count = 0
            for term in new_terms:
                # Simple deduplication based on original text
                # In a real scenario, we might want to handle conflicts better
                if term.get('original') and term.get('type') and (term.get('original'), term.get('type')) not in existing_terms_dict:
                    all_terms.append(term)
                    existing_terms_dict[(term['original'], term['type'])] = (term['translation'], term.get('notes', ''))
                    added_count += 1
                elif term.get('original') and term.get('type'):
                    # replace existing term if translation is different (optional, based on confidence)
                    existing_terms_dict[(term['original'], term['type'])] = (term['translation'], term.get('notes', ''))
                    for idx, existing_term in enumerate(all_terms):
                        if existing_term['original'] == term['original'] and existing_term['type'] == term['type']:
                            all_terms[idx] = term  # Update with new translation/notes
                            break
                

            print(f"  Extracted {len(new_terms)} terms, {added_count} new.")
            print(f"  Total unique terms so far: {len(all_terms)}")
            # Save progress after each chunk
            save_json(TERMINOLOGY_FILE, all_terms)
            
            # Rate limiting / politeness
            time.sleep(1)

    print("Done! Terminology extraction complete.")

if __name__ == "__main__":
    main()
