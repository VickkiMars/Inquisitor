def get_content_between_curly_braces(text, sym1, sym2):
    """
    Returns the substring from the first '{' to the last '}' (inclusive).

    Args:
        text: The input string.

    Returns:
        The substring contained within the first and last curly braces,
        or an empty string if braces are not found or are misplaced.
    """
    first_brace_index = text.find(sym1)
    last_brace_index = text.rfind(sym2)

    if first_brace_index == -1 or last_brace_index == -1:
        return text  # No braces found

    if first_brace_index >= last_brace_index:
        return text  # Mismatched or inverted braces

    return text[first_brace_index : last_brace_index + 1]



