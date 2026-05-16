import re


def resolve_reference(reference: str, items: list[dict], id_key: str) -> str:
    if not reference:
        return reference

    normalized_reference = reference.lower().strip()
    if normalized_reference.startswith(("slot-", "appt-")):
        return reference

    item_index = reference_index(normalized_reference)
    if item_index is not None and 0 <= item_index < len(items):
        return items[item_index][id_key]

    for item in items:
        searchable_text = item_searchable_text(item)
        if any(token in searchable_text for token in normalized_reference.split()):
            return item[id_key]

    if len(items) == 1:
        return items[0][id_key]
    return reference


def reference_index(reference: str) -> int | None:
    ordinal_indexes = {
        "second": 1,
        "two": 1,
        "third": 2,
        "three": 2,
        "first": 0,
        "one": 0,
        "3": 2,
        "2": 1,
        "1": 0,
    }
    for keyword, index in ordinal_indexes.items():
        if re.search(rf"\b{keyword}\b", reference):
            return index
    return None


def item_searchable_text(item: dict) -> str:
    slot = item.get("slot", item)
    fields = [
        slot.get("provider", ""),
        slot.get("location", ""),
        slot.get("time", ""),
        item.get("appointment_id", ""),
        item.get("id", ""),
    ]
    return " ".join(str(field) for field in fields).lower()
