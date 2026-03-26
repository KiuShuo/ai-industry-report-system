import markdown


def render_markdown_to_html(md_text: str) -> str:
    """Render markdown text to HTML for report display."""
    return markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
