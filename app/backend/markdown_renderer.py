from html import escape

try:
    import markdown
except ImportError:  # pragma: no cover - exercised in environments without markdown installed
    markdown = None


def render_markdown_to_html(md_text: str) -> str:
    """Render markdown text to HTML for report display."""
    if not md_text:
        return ""
    if markdown is not None:
        return markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    return _render_basic_markdown(md_text)


def _render_basic_markdown(md_text: str) -> str:
    blocks = []
    for raw_line in md_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("### "):
            blocks.append(f"<h3>{escape(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            blocks.append(f"<h2>{escape(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            blocks.append(f"<h1>{escape(line[2:])}</h1>")
            continue
        blocks.append(f"<p>{escape(line)}</p>")
    return "\n".join(blocks)
