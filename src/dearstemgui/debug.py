from typing import Any


def debug_callback(sender: str, data: Any) -> None:
    print(f'sender {sender} sent:')
    print(data)
