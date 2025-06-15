from typing import List
from langchain_core.output_parsers import BaseOutputParser
import ast
import re

class PythonListOutputParser(BaseOutputParser[List[str]]):
    """Parse LLM output into a Python list of strings"""

    def parse(self, text: str) -> List[str]:
        # First try to find a Python list pattern in the output
        match = re.search(r'\[.*\]', text)
        if not match:
            raise ValueError(f"Could not parse list from: {text}")
        
        # Safely evaluate the string as Python literal
        try:
            result = ast.literal_eval(match.group(0))
            if not isinstance(result, list):
                raise ValueError(f"Parsed object is not a list: {result}")
            return result
        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Failed to parse list: {e}")