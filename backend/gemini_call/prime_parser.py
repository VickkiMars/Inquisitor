import ast
import re
from typing import List

def parse_gemini_question_blocks(blocks: List[str]) -> List[List[dict]]:
    all_questions = []

    for block in blocks:
        try:
            # 1. Remove triple backticks and optional language hint
            cleaned = re.sub(r"^```python\s*|```$", "", block.strip())

            # 2. Remove the `questions = ` prefix
            cleaned = cleaned.strip()
            if cleaned.startswith("questions ="):
                cleaned = cleaned[len("questions ="):].strip()

            # 3. Safely evaluate the list using ast.literal_eval
            cleaned.strip("\n").strip("\\")
            print(cleaned)
            parsed = ast.literal_eval(cleaned)
            for i in parsed: all_questions.append(i)
        except Exception as e:
            print(f"Error parsing block:\n{block[:100]}...\nError: {e}")
            all_questions.append([])  # or raise, depending on strictness

    return all_questions

# out = parse_gemini_question_blocks(list_)
# with open('gem.json', 'w', encoding='utf-8') as f:
#     json.dump(out,f, indent=2)