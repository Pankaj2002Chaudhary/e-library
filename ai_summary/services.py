import requests

from django.conf import settings


class AISummaryService:
    """
    Handles communication with
    the Userfacet AI API.
    """

    BASE_URL = "https://ai-api.userfacet.com"

    @classmethod
    def generate_summary(
        cls,
        book,
        summary_type
    ):

        if summary_type == "SHORT":

            instruction = """
            Generate a concise summary.

            Length: 150-200 words.

            Include:
            - Main idea
            - Core concepts
            - Target audience
            """

            max_tokens = 400

        else:

            instruction = """
            Generate a detailed summary.

            Length: 700-800 words.

            Include:
            - Main concepts
            - Important topics
            - Key lessons
            - Practical takeaways
            """

            max_tokens = 1500

        prompt = f"""
        {instruction}

        Title: {book.title}

        Author: {book.author}

        Description:
        {book.description}
        """

        headers = {
            "Authorization":
                f"Bearer {settings.AI_API_TOKEN}",
            "Content-Type":
                "application/json"
        }

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens
        }

        response = requests.post(
            f"{cls.BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]