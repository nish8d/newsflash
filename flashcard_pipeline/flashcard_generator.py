# flashcard_pipeline/flashcard_generator.py

import json
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from flashcard_schema import Flashcard

# Enhanced prompt with clear instructions and examples
ENHANCED_PROMPT = """You are an expert at creating educational flashcards from news articles.

Given the article below, create ONE high-quality flashcard following these guidelines:

GUIDELINES:
1. Question: Ask about the most important fact, event, or development in the article
   - Be specific and clear
   - Focus on "what", "who", "when", or "why" questions
   - Avoid yes/no questions

2. Answer: Provide a concise, factual answer (1-3 sentences)
   - Include key details: names, dates, numbers
   - Be precise and accurate

3. Context: Explain why this matters (2-3 sentences)
   - Connect to broader implications
   - Explain the significance or impact

4. Entity: The main organization, company, or institution featured
   - Use the official name
   - If multiple, choose the primary one

5. Person of Contact: The key person mentioned (CEO, official, spokesperson)
   - Use full name and title if available
   - Leave empty if no specific person is prominently featured

ARTICLE DETAILS:
Title: {title}
Summary: {summary}
Source: {source}
Date: {published_at}

{format_instructions}

OUTPUT (valid JSON only, no other text):"""


class FlashcardGenerator:
    def __init__(self, model="mistral", temperature=0.3, max_retries=2):
        """
        Initialize with configurable parameters.
        
        Args:
            model: Ollama model name
            temperature: Higher = more creative, lower = more focused (0.3 is good balance)
            max_retries: Number of retry attempts on failure
        """
        self.llm = ChatOllama(
            model=model,
            temperature=temperature,
            format="json",  # Force JSON output mode in Ollama
        )
        
        # Use Pydantic schema for structured output
        self.parser = JsonOutputParser(pydantic_object=Flashcard)
        
        self.prompt = PromptTemplate(
            template=ENHANCED_PROMPT,
            input_variables=["title", "summary", "source", "published_at"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.max_retries = max_retries

    def validate_output(self, flashcard_data):
        """Validate flashcard quality."""
        issues = []
        
        # Check for empty critical fields
        if not flashcard_data.get("question", "").strip():
            issues.append("Question is empty")
        if not flashcard_data.get("answer", "").strip():
            issues.append("Answer is empty")
        
        # Check minimum quality thresholds
        question = flashcard_data.get("question", "")
        answer = flashcard_data.get("answer", "")
        
        if len(question) < 10:
            issues.append("Question too short (< 10 chars)")
        if len(answer) < 15:
            issues.append("Answer too short (< 15 chars)")
        
        # Check for placeholder text
        placeholders = ["n/a", "none", "unknown", "not applicable", "no information"]
        if any(ph in answer.lower() for ph in placeholders):
            issues.append("Answer contains placeholder text")
        
        return issues

    def generate_for_article(self, article):
        """
        Generate flashcard with retry logic and validation.
        
        Returns:
            dict: Flashcard data with question, answer, context, entity, person_of_contact
        """
        chain = self.prompt | self.llm | self.parser
        
        for attempt in range(self.max_retries + 1):
            try:
                # Invoke the chain
                result = chain.invoke({
                    "title": article.get("title", ""),
                    "summary": article.get("summary", ""),
                    "source": article.get("source", ""),
                    "published_at": article.get("published_at", "")
                })
                
                # Validate output quality
                issues = self.validate_output(result)
                
                if not issues:
                    # Map the schema field name to the shorter version used in storage
                    return {
                        "question": result.get("question", ""),
                        "answer": result.get("answer", ""),
                        "context": result.get("context", ""),
                        "entity": result.get("the_entity_mainly_concerned_with_the_news_article", ""),
                        "person_of_contact": result.get("person_of_contact", "")
                    }
                
                # If validation failed and we have retries left
                if attempt < self.max_retries:
                    print(f"  ⚠️  Validation issues: {', '.join(issues)}. Retrying...")
                    continue
                else:
                    print(f"  ⚠️  Validation issues after {self.max_retries} retries: {', '.join(issues)}")
                    return result  # Return anyway
                    
            except json.JSONDecodeError as e:
                if attempt < self.max_retries:
                    print(f"  ⚠️  JSON parsing error: {e}. Retrying...")
                    continue
                else:
                    print(f"  ❌ JSON parsing failed after {self.max_retries} retries")
                    raise
                    
            except Exception as e:
                if attempt < self.max_retries:
                    print(f"  ⚠️  Error: {e}. Retrying...")
                    continue
                else:
                    print(f"  ❌ Failed after {self.max_retries} retries: {e}")
                    raise
        
        # Fallback empty result
        return {
            "question": "",
            "answer": "",
            "context": "",
            "entity": "",
            "person_of_contact": ""
        }