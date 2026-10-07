"""
Criterion Extractor using local FLAN-T5 model.
Replaces Gemini API for local offline inference.
"""

import os
import json
import re
import logging
<<<<<<< HEAD
import torch
from transformers import pipeline, T5Tokenizer, T5ForConditionalGeneration
=======
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from pydantic import BaseModel, Field
from typing import List
>>>>>>> 4e831edd2a8d727fe267b4289bffc197d5ecf0a6

logger = logging.getLogger(__name__)

MAX_CHUNK_CHARS = 1000   # FLAN-T5 has a smaller context window than Gemini
OVERLAP_CHARS = 200

class CriterionExtractor:
    def __init__(self):
<<<<<<< HEAD
        """Initialize local FLAN-T5 model."""
        self.model_name = "google/flan-t5-base" # Using base for lower memory footprint in prototype
        logger.info(f"Loading local model {self.model_name}...")
        try:
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
            self.generator = pipeline(
                "text2text-generation", 
                model=self.model, 
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("Local model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            self.generator = None
=======
        """Initialize LangChain Gemini model and chain."""
        if os.getenv("MOCK_LLM", "false").lower() == "true":
            logger.info("🤖 Using MOCK LLM for Criteria Extraction")
            self.llm = FakeListChatModel(responses=[
                '[{"text": "Simulated Mandatory Criterion", "type": "mandatory", "weight": 1.0}, {"text": "Simulated Optional Criterion", "type": "optional", "weight": 0.5}]'
            ])
        else:
            # ✅ LangChain ChatOllama (Local LLM)
            self.llm = ChatOllama(
                model="llama3", # Default ollama model
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=0,
                format="json",
            )
        
        # ✅ LangChain PromptTemplate
        self.prompt = PromptTemplate(
            input_variables=["tender_text"],
            template="""You are an expert procurement officer. Extract all eligibility and evaluation criteria from the following government tender document.

Rules:
1. Identify if a criterion is 'mandatory' (Pass/Fail) or 'optional' (scored/weighted).
2. Assign a weight if mentioned (e.g. "30 marks"), otherwise default to 1.0.
3. Provide a clear, concise text description for each criterion.
4. Do NOT invent criteria that are not explicitly stated.

Output MUST be a valid JSON array of objects with these keys:
- text: string (the criterion description)
- type: string ("mandatory" or "optional")
- weight: float

Tender Document Text:
---
{tender_text}
---

Respond ONLY with the JSON array. No markdown, no explanation."""
        )
        
        # ✅ LangChain JsonOutputParser for structured output
        self.parser = JsonOutputParser()
        
        # ✅ Build the chain: Prompt → LLM → Parser
        self.chain = self.prompt | self.llm | self.parser
>>>>>>> 4e831edd2a8d727fe267b4289bffc197d5ecf0a6

    def extract_criteria(self, tender_text: str) -> list:
        """
        Extracts criteria using FLAN-T5.
        Processes text in small chunks due to T5's sequence length limits.
        """
        if not self.generator or not tender_text.strip():
            return []

        # Split text into chunks
        all_criteria = []
        seen_texts = set()
        
        # Simple chunking for T5
        words = tender_text.split()
        chunk_size = 200 # words
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size - 20)]

        for chunk in chunks[:10]: # Limit chunks for performance in prototype
            prompt = f"Extract procurement eligibility criteria from this text: {chunk}"
            try:
                outputs = self.generator(prompt, max_length=128, num_return_sequences=1)
                extracted_text = outputs[0]['generated_text']
                
                # FLAN-T5 won't return perfect JSON easily, so we parse bullet points or sentences
                # We'll split by common separators
                items = re.split(r'\n|;|\.', extracted_text)
                for item in items:
                    item = item.strip()
                    if len(item) > 20 and item.lower() not in seen_texts:
                        # Heuristic to determine type
                        ctype = "mandatory"
                        if any(word in item.lower() for word in ["prefer", "optional", "desired", "extra"]):
                            ctype = "optional"
                        
                        all_criteria.append({
                            "text": item,
                            "type": ctype,
                            "weight": 1.0
                        })
                        seen_texts.add(item.lower())
            except Exception as e:
                logger.warning(f"Chunk extraction failed: {e}")

        return all_criteria

extractor = CriterionExtractor()
