"""
Bidder Evaluator using local FLAN-T5 and Scikit-learn.
Replaces Gemini API for local offline inference.
"""

import os
import json
import logging
<<<<<<< HEAD
=======
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from sentence_transformers import SentenceTransformer, util
>>>>>>> 4e831edd2a8d727fe267b4289bffc197d5ecf0a6
import torch
import numpy as np
from transformers import pipeline, T5Tokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer, util
from sklearn.ensemble import RandomForestRegressor, IsolationForest

logger = logging.getLogger(__name__)

class BidderEvaluator:
    def __init__(self):
<<<<<<< HEAD
        """Initialize local models."""
        self.model_name = "google/flan-t5-base"
        try:
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
            self.generator = pipeline(
                "text2text-generation", 
                model=self.model, 
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Phase 7: Initialize Random Forest for confidence scoring
            # We'll use a pre-set forest as a placeholder for a trained one
            self.rf_model = RandomForestRegressor(n_estimators=10, random_state=42)
            # Dummy training to "initialize" the model for the prototype
            X_dummy = np.random.rand(10, 3) # features: semantic_score, chunk_len, match_ratio
            y_dummy = np.random.rand(10)
            self.rf_model.fit(X_dummy, y_dummy)
            
            # Isolation Forest for anomaly detection (flagging weird evaluations)
            self.iso_forest = IsolationForest(contamination=0.1, random_state=42)
            self.iso_forest.fit(X_dummy)
            
            logger.info("Local evaluator models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load local evaluator: {e}")
            self.generator = None
=======
        """Initialize LangChain Gemini model and evaluation chain."""
        if os.getenv("MOCK_LLM", "false").lower() == "true":
            logger.info("🤖 Using MOCK LLM for Bidder Evaluation")
            self.llm = FakeListChatModel(responses=[
                '{"status": "pass", "excerpt": "Simulated evidence excerpt found in document.", "reasoning": "This is a simulated passing evaluation.", "completeness": 1.0, "page": 1, "source_doc": "simulated.pdf"}'
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
            input_variables=["criterion", "criterion_type", "context"],
            template="""You are a government procurement auditor evaluating a bidder's submission.
>>>>>>> 4e831edd2a8d727fe267b4289bffc197d5ecf0a6

    def find_relevant_excerpts(self, criterion_text, bidder_chunks, top_k=3):
        """Uses semantic similarity (local) to find relevant chunks."""
        criterion_embedding = self.semantic_model.encode(criterion_text, convert_to_tensor=True)
        chunk_texts = [c.get("normalized_text", c.get("text", "")) for c in bidder_chunks]
        
        if not chunk_texts:
            return []
            
        chunk_embeddings = self.semantic_model.encode(chunk_texts, convert_to_tensor=True)
        cosine_scores = util.cos_sim(criterion_embedding, chunk_embeddings)[0]
        top_results = torch.topk(cosine_scores, k=min(top_k, len(chunk_texts)))
        
        relevant_chunks = []
        for score, idx in zip(top_results[0], top_results[1]):
            chunk = bidder_chunks[idx.item()]
            chunk["semantic_score"] = score.item()
            relevant_chunks.append(chunk)
            
        return relevant_chunks

    def compute_confidence_ml(self, features):
        """
        Uses RandomForest to compute confidence based on features.
        Features: [semantic_match, text_length_ratio, ocr_quality]
        """
        if not hasattr(self, 'rf_model'):
            return 0.5
        
        features_array = np.array([features])
        confidence = self.rf_model.predict(features_array)[0]
        
        # Check for anomalies using Isolation Forest
        is_anomaly = self.iso_forest.predict(features_array)[0] == -1
        if is_anomaly:
            confidence *= 0.5 # Penalize anomalous/untrustworthy predictions
            
        return float(np.clip(confidence, 0.0, 1.0))

    def evaluate_bidder_criterion(self, criterion, bidder_chunks):
        """Evaluates a single criterion using local T5 and ML models."""
        relevant_chunks = self.find_relevant_excerpts(criterion["text"], bidder_chunks)
        
        if not relevant_chunks:
            return {
                "status": "review_needed",
                "reasoning": "No relevant evidence found.",
                "confidence": 0.0
            }

        context = relevant_chunks[0].get("text", "") # Take top match for T5 context limits
        prompt = f"Does this text satisfy the requirement '{criterion['text']}'? Context: {context}. Answer Yes/No and give reason."
        
        try:
            outputs = self.generator(prompt, max_length=128)
            t5_output = outputs[0]['generated_text'].lower()
            
            status = "review_needed"
            if "yes" in t5_output:
                status = "pass"
            elif "no" in t5_output:
                status = "fail"
                
            # ML Confidence Scoring
            semantic_match = relevant_chunks[0].get("semantic_score", 0.0)
            text_length_ratio = min(len(context) / (len(criterion['text']) + 1), 2.0) / 2.0
            ocr_quality = 0.9 # Hardcoded for prototype
            
            confidence = self.compute_confidence_ml([semantic_match, text_length_ratio, ocr_quality])
            
            return {
                "status": status,
                "reasoning": t5_output,
                "excerpt": context[:200],
                "confidence": confidence,
                "completeness": semantic_match,
                "page": relevant_chunks[0].get("page"),
                "source_doc": relevant_chunks[0].get("source_file")
            }
            
        except Exception as e:
            logger.error(f"T5 Evaluation failed: {e}")
            return {
                "status": "review_needed",
                "reasoning": f"Local evaluation error: {e}",
                "confidence": 0.0
            }

evaluator = BidderEvaluator()
