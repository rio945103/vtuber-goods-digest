from dataclasses import dataclass
from typing import Optional


@dataclass
class StoreItem:
    member_name: str
    title: str
    url: str
    raw_text: str
    source_type: str  # goods
    available: Optional[bool] = None  # Shopify系はTrue/False、にじさんじはNone