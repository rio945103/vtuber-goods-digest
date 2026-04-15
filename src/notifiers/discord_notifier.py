import requests

DISCORD_MAX_LENGTH = 1900  # 余裕を持たせて1900


def build_discord_message(new_items: list[tuple[str, tuple[int, int, str], str, str, str]]) -> str:
    grouped: dict[str, list[tuple[tuple[int, int, str], str, str, str]]] = {}

    for member_name, sort_key, label, title, url in new_items:
        grouped.setdefault(member_name, []).append((sort_key, label, title, url))

    lines: list[str] = []
    lines.append("【VTuberグッズ新着ダイジェスト】")
    lines.append("")

    for member_name, items in grouped.items():
        lines.append(f"■ {member_name}")

        sorted_items = sorted(items, key=lambda x: x[0])

        for _, label, title, url in sorted_items:
            lines.append(f"・{label} {title}")
            lines.append(f"  {url}")

        lines.append("")

    return "\n".join(lines).strip()


def split_message(content: str) -> list[str]:
    """2000文字を超える場合は複数のメッセージに分割する"""
    if len(content) <= DISCORD_MAX_LENGTH:
        return [content]

    chunks = []
    lines = content.split("\n")
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > DISCORD_MAX_LENGTH:
            if current:
                chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks


def send_discord_message(webhook_url: str, content: str) -> None:
    if not webhook_url.strip():
        return

    chunks = split_message(content)
    for chunk in chunks:
        response = requests.post(
            webhook_url,
            json={"content": chunk},
            timeout=(10, 30),
        )
        response.raise_for_status()