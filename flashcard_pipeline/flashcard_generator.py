# flashcard_pipeline/flashcard_generator.py

import json
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from flashcard_schema import Flashcard

# Enhanced prompt that uses the full article body
# Enhanced prompt that uses the full article body
ENHANCED_PROMPT = """You are an expert at creating educational flashcards from business news articles across various industries and sectors.

Read the FULL ARTICLE BODY below and create ONE comprehensive flashcard.

GUIDELINES:
1. **Question**: Ask about the most important fact, event, or development
   - Be specific and reference concrete details from the article
   - Focus on "what", "who", "when", "where", or "why" questions
   - Avoid yes/no questions
   - Example: "What strategic partnership did Company X announce in the technology sector?"

2. **Answer**: Provide a detailed, factual answer (2-4 sentences)
   - Include specific names, dates, numbers, and statistics from the article
   - Be precise and comprehensive
   - Example: "Company X announced a strategic partnership with Company Y to expand their market presence in the Asia-Pacific region, with an expected investment of $500 million over the next three years..."

3. **Context**: Explain the broader significance (2-4 sentences)
   - Why does this matter to the industry/sector?
   - What are the business implications or future impact?
   - Connect to larger market trends, competitive landscape, or regulatory changes

4. **Summary**: Create a concise summary of the entire article (3-5 sentences)
   - Cover the main business developments and key points
   - Include important financial figures, statistics, or quotes from executives
   - Maintain chronological or logical flow

5. **Entity**: The main organization, company, or institution
   - Use the official full name
   - If multiple entities, choose the primary subject of the article

6. **Person of Contact**: The key person mentioned
   - Use full name and title/role (CEO, CFO, Managing Director, etc.)
   - Choose the most prominently featured business leader or executive
   - Leave empty if no specific person is central to the story

ARTICLE DETAILS:
Title: {title}
Source: {source}
Date: {published_at}

FULL ARTICLE BODY:
{body}

Read the entire article carefully before generating the flashcard.

{format_instructions}

OUTPUT (valid JSON only, no other text):"""


class FlashcardGenerator:
    def __init__(self, model="mistral", temperature=0.2, max_retries=3):
        """
        Initialize with configurable parameters.
        
        Args:
            model: Ollama model name (mistral, llama2, etc.)
            temperature: Lower = more focused (0.2 recommended for factual content)
            max_retries: Number of retry attempts on failure
        """
        self.llm = ChatOllama(
            model=model,
            temperature=temperature,
            format="json",
            num_predict=2048,  # Increased token limit for longer responses
        )
        
        self.parser = JsonOutputParser(pydantic_object=Flashcard)
        
        self.prompt = PromptTemplate(
            template=ENHANCED_PROMPT,
            input_variables=["title", "body", "source", "published_at"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.max_retries = max_retries

    def validate_output(self, flashcard_data):
        """Validate flashcard quality with stricter requirements."""
        issues = []
        
        # Check for empty critical fields
        required_fields = ["question", "answer", "context", "summary"]
        for field in required_fields:
            if not flashcard_data.get(field, "").strip():
                issues.append(f"{field.capitalize()} is empty")
        
        # Check minimum quality thresholds (increased for body-based generation)
        question = flashcard_data.get("question", "")
        answer = flashcard_data.get("answer", "")
        context = flashcard_data.get("context", "")
        summary = flashcard_data.get("summary", "")
        
        if len(question) < 20:
            issues.append("Question too short (< 20 chars)")
        if len(answer) < 50:
            issues.append("Answer too short (< 50 chars)")
        if len(context) < 50:
            issues.append("Context too short (< 50 chars)")
        if len(summary) < 100:
            issues.append("Summary too short (< 100 chars)")
        
        # Check for placeholder text
        placeholders = ["n/a", "none", "unknown", "not applicable", "no information", "not mentioned"]
        for field_name, field_value in [("answer", answer), ("context", context), ("summary", summary)]:
            if any(ph in field_value.lower() for ph in placeholders):
                issues.append(f"{field_name.capitalize()} contains placeholder text")
        
        # Check that answer contains specific details (numbers, names, etc.)
        if not any(char.isdigit() for char in answer) and len(answer) < 100:
            issues.append("Answer lacks specific details (numbers, statistics)")
        
        return issues

    def generate_for_article(self, article):
        """
        Generate flashcard with retry logic and validation.
        
        Args:
            article: Dict containing title, body, source, published_at
            
        Returns:
            dict: Flashcard data with all required fields
        """
        chain = self.prompt | self.llm | self.parser
        
        # Truncate body if too long (keep first 4000 chars to stay within context limits)
        body = article.get("body", "")
        if len(body) > 4000:
            body = body[:4000] + "..."
        
        for attempt in range(self.max_retries + 1):
            try:
                # Invoke the chain
                result = chain.invoke({
                    "title": article.get("title", ""),
                    "body": body,
                    "source": article.get("source", ""),
                    "published_at": article.get("published_at", "")
                })
                
                # Validate output quality
                issues = self.validate_output(result)
                
                if not issues:
                    # Map schema fields correctly
                    return {
                        "summary": result.get("summary", ""),
                        "question": result.get("question", ""),
                        "answer": result.get("answer", ""),
                        "context": result.get("context", ""),
                        "entity": result.get("the_entity_mainly_concerned_with_the_news_article", ""),
                        "person_of_contact": result.get("person_of_contact", "")
                    }
                
                # If validation failed and we have retries left
                if attempt < self.max_retries:
                    continue
                else:
                    # Return partial result rather than failing completely
                    return {
                        "summary": result.get("summary", ""),
                        "question": result.get("question", ""),
                        "answer": result.get("answer", ""),
                        "context": result.get("context", ""),
                        "entity": result.get("the_entity_mainly_concerned_with_the_news_article", ""),
                        "person_of_contact": result.get("person_of_contact", "")
                    }
                    
            except json.JSONDecodeError as e:
                if attempt < self.max_retries:
                    continue
                else:
                    raise
                    
            except Exception as e:
                if attempt < self.max_retries:
                    continue
                else:
                    raise
        
        # Fallback empty result
        return {
            "summary": "",
            "question": "",
            "answer": "",
            "context": "",
            "entity": "",
            "person_of_contact": ""
        }