from dataclasses import dataclass


@dataclass
class StoreItem:
    member_name: str
    title: str
    url: str
    raw_text: str
    source_type: str  # goods