# utils.py
def extract_text(response) -> str:
    """Safely extract text from LangChain response regardless of version."""
    content = response.content
    if isinstance(content, list):
        return content[0]["text"]
    return content