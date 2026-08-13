import requests

from django.conf import settings


class AIReviewService:
    """Generate polished reviews through the Userfacet AI API."""

    BASE_URL = "https://ai-api.userfacet.com"

    @classmethod
    def generate_review(cls, book, rating, user_notes):
        prompt = f"""
        Write a professional book review.

        Book: {book.title}
        Author: {book.author}
        Rating: {rating}/5
        User Notes: {user_notes}

        Requirements:
        - 150 to 250 words
        - Natural tone
        - Mention strengths
        - Mention who should read it
        """
        headers = {
            "Authorization": f"Bearer {settings.AI_API_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {"messages": [{"role": "user", "content": prompt}]}

        response = requests.post(
            f"{cls.BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
