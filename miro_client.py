import requests
from config import MIRO_API_KEY, MIRO_BOARD_ID

MIRO_API_BASE_URL = "https://api.miro.com/v2"


def get_board_items(board_id=None):
    if board_id is None:
        board_id = MIRO_BOARD_ID

    url = f"{MIRO_API_BASE_URL}/boards/{board_id}/items"
    headers = {
        "Authorization": f"Bearer {MIRO_API_KEY}",
        "Content-Type": "application/json"
    }

    items = []
    cursor = None

    while True:
        params = {}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise RuntimeError(
                f"Miro API request failed with status code {response.status_code}: {response.text}"
            )

        data = response.json()
        raw_items = data.get("data", [])

        for raw_item in raw_items:
            item = {
                "id": raw_item.get("id"),
                "type": raw_item.get("type"),
                "text": None,
                "position": None
            }

            if raw_item.get("type") == "connector":
                item["start_item"] = raw_item.get("startItem", {}).get("id")
                item["end_item"] = raw_item.get("endItem", {}).get("id")
            else:
                if "data" in raw_item:
                    item["text"] = raw_item["data"].get("content") or raw_item["data"].get("text")

                if "position" in raw_item:
                    item["position"] = {
                        "x": raw_item["position"].get("x"),
                        "y": raw_item["position"].get("y")
                    }

            items.append(item)

        cursor = data.get("cursor")
        if not cursor:
            break

    return items


def create_sticky_note(text, x, y, board_id=None):
    if board_id is None:
        board_id = MIRO_BOARD_ID

    url = f"{MIRO_API_BASE_URL}/boards/{board_id}/sticky_notes"
    headers = {
        "Authorization": f"Bearer {MIRO_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "data": {
            "content": text
        },
        "position": {
            "x": x,
            "y": y
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"Miro API request failed with status code {response.status_code}: {response.text}"
        )

    return response.json()


def create_text_item(text, x, y, board_id=None):
    if board_id is None:
        board_id = MIRO_BOARD_ID

    url = f"{MIRO_API_BASE_URL}/boards/{board_id}/texts"
    headers = {
        "Authorization": f"Bearer {MIRO_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "data": {
            "content": text
        },
        "position": {
            "x": x,
            "y": y
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"Miro API request failed with status code {response.status_code}: {response.text}"
        )

    return response.json()
