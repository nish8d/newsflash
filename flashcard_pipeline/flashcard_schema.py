from pydantic import BaseModel, ConfigDict, Field
from typing import List

class Flashcard(BaseModel):
    model_config = ConfigDict(extra='forbid')

    question: str = Field(description="A clear, specific question about the article")
    answer: str = Field(description="A concise, factual answer with key details")
    context: str = Field(description="Why this matters and broader implications")
    the_entity_mainly_concerned_with_the_news_article: str = Field(
        description="Main organization, company, or institution",
        default=""
    )
    person_of_contact: str = Field(
        description="Key person mentioned (full name and title)",
        default=""
    )

class FlashcardOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    flashcards: List[Flashcard]