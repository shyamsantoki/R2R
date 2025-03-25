import http.client
import json
import logging
import os
import urllib.parse
import requests

logger = logging.getLogger(__name__)


def process_json(json_object, indent=0):
    """Recursively traverses the JSON object (dicts and lists) to create an
    unstructured text blob."""
    text_blob = ""
    if isinstance(json_object, dict):
        for key, value in json_object.items():
            padding = "  " * indent
            if isinstance(value, (dict, list)):
                text_blob += (
                    f"{padding}{key}:\n{process_json(value, indent + 1)}"
                )
            else:
                text_blob += f"{padding}{key}: {value}\n"
    elif isinstance(json_object, list):
        for index, item in enumerate(json_object):
            padding = "  " * indent
            if isinstance(item, (dict, list)):
                text_blob += f"{padding}Item {index + 1}:\n{process_json(item, indent + 1)}"
            else:
                text_blob += f"{padding}Item {index + 1}: {item}\n"
    return text_blob


class BraveClient:
    def __init__(self, api_base: str = "api.search.brave.com") -> None:
        api_key = os.getenv("BRAVE_API_KEY")
        if not api_key:
            raise ValueError(
                "Please set the `BRAVE_API_KEY` environment variable to use `BraveClient`."
            )

        self.api_base = api_base
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }

    def search(self, query: str, limit: int = 10) -> list:
        if not isinstance(query, str):  # Ensure query is a string
            raise ValueError("Query must be a string")

        encoded_query = urllib.parse.quote_plus(query.strip())  # Strip spaces and encode properly
        url = f"https://{self.api_base}/res/v1/web/search?q={encoded_query}&count={limit}"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        json_data = response.json()

        return BraveClient._extract_results(json_data)

    @staticmethod
    def _extract_results(result_data: dict) -> list:
        formatted_results = []
        
        for key, value in result_data.items():
            if key == "searchParameters":
                continue
            
            if key == "answerBox":
                value["type"] = key
                formatted_results.append(value)
            elif isinstance(value, list):
                for item in value:
                    item["type"] = key
                    formatted_results.append(item)
            elif isinstance(value, dict):
                value["type"] = key
                formatted_results.append(value)
        
        return formatted_results

    @staticmethod
    def construct_context(results: list) -> str:
        organized_results = {}
        for result in results:
            result_type = result.get("type", "Unknown")
            if result_type not in organized_results:
                organized_results[result_type] = [result]
            else:
                organized_results[result_type].append(result)

        context = ""
        for result_type, items in organized_results.items():
            context += f"# {result_type} Results:\n"
            for index, item in enumerate(items, start=1):
                context += f"Item {index}:\n"
                context += process_json(item) + "\n"

        return context
