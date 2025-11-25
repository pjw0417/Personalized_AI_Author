# questionnaire.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserProfile:
    age: int
    preferred_theme: str
    purpose_of_reading: str
    mood_today: str
    length_in_pages: int
    education_level: Optional[str] = ""
    favorite_author: Optional[str] = ""
    special_request: Optional[str] = ""
