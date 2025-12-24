# flashcard_pipeline/flashcard_schema.py

from pydantic import BaseModel, ConfigDict, Field
from typing import List

class Flashcard(BaseModel):
    """Schema for a single flashcard generated from a news article."""
    model_config = ConfigDict(extra='forbid')

    summary: str = Field(
        description="A comprehensive 3-5 sentence summary of the entire article covering main points and key developments"
    )
    question: str = Field(
        description="A clear, specific question about the most important aspect of the article (20+ characters)"
    )
    answer: str = Field(
        description="A detailed, factual answer with key details, names, dates, and statistics (2-4 sentences, 50+ characters)"
    )
    context: str = Field(
        description="Why this matters - broader implications, significance, and future impact (2-4 sentences, 50+ characters)"
    )
    the_entity_mainly_concerned_with_the_news_article: str = Field(
        description="Main organization, company, institution, or team featured in the article (use official full name)",
        default=""
    )
    person_of_contact: str = Field(
        description="Key person mentioned with full name and title/role (empty if no specific person is central)",
        default=""
    )

class FlashcardOutput(BaseModel):
    """Schema for multiple flashcards output."""
    model_config = ConfigDict(extra='forbid')

    flashcards: List[Flashcard]