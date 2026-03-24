import requests


def build_discord_message(new_items: list[tuple[str, tuple[int, int, str], str, str, str]]) -> str:
    grouped: dict[str, list[tuple[tuple[int, int, str], str, str, str]]] = {}

    for member_name, sort_key, label, title, url in new_items:
        grouped.setdefault(member_name, []).append((sort_key, label, title, url))

    lines: list[str] = []
    lines.append("【にじさんじ新着ダイジェスト】")
    lines.append("")

    for member_name, items in grouped.items():
        lines.append(f"■ {member_name}")

        sorted_items = sorted(items, key=lambda x: x[0])

        for _, label, title, url in sorted_items:
            lines.append(f"・{label} {title}")
            lines.append(f"  {url}")

        lines.append("")

    return "\n".join(lines).strip()


def send_discord_message(webhook_url: str, content: str) -> None:
    if not webhook_url.strip():
        return

    response = requests.post(
        webhook_url,
        json={"content": content},
        timeout=(10, 30),
    )
    response.raise_for_status()