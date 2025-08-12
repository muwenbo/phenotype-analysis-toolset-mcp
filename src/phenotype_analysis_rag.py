import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_voyageai import VoyageAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClinicalTerm:
    """Represents a clinical term with its various forms"""
    chinese: str
    english: str
    category: str
    confidence: float
    context: str = ""
    severity: str = ""
    temporal: str = ""

@dataclass
class HPOCandidate:
    """Represents an HPO term candidate"""
    hpo_id: str
    hpo_name: str
    description: str
    score: float

@dataclass
class HPOMapping:
    """Final mapping result"""
    original_chinese: str
    english_translation: str
    hpo_id: str
    hpo_name: str
    confidence: float
    context: str = ""
    reasoning: str = ""

# Pydantic models for structured output
class ExtractedSymptom(BaseModel):
    original_chinese: str = Field(description="Original Chinese symptom phrase")
    standardized_chinese: str = Field(description="Standardized Chinese medical term")
    english_translation: str = Field(description="Precise English medical term")
    category: str = Field(description="Clinical category")
    severity: str = Field(description="mild/moderate/severe/unknown")
    temporal: str = Field(description="acute/chronic/recurrent/unknown")
    context: str = Field(description="Additional context")
    confidence: float = Field(description="Confidence score 0.0-1.0")

class ClinicalSummary(BaseModel):
    constitutional: List[str] = Field(default_factory=list)
    respiratory: List[str] = Field(default_factory=list)
    cardiovascular: List[str] = Field(default_factory=list)
    neurological: List[str] = Field(default_factory=list)
    digestive: List[str] = Field(default_factory=list)
    musculoskeletal: List[str] = Field(default_factory=list)
    dermatological: List[str] = Field(default_factory=list)
    other: List[str] = Field(default_factory=list)

class DiagnosticInformation(BaseModel):
    lab_values: List[str] = Field(default_factory=list)
    imaging_findings: List[str] = Field(default_factory=list)
    physical_examination: List[str] = Field(default_factory=list)
    temporal_information: List[str] = Field(default_factory=list)
    severity_indicators: List[str] = Field(default_factory=list)

class SymptomExtractionResult(BaseModel):
    extracted_symptoms: List[ExtractedSymptom]
    clinical_summary: ClinicalSummary
    diagnostic_information: DiagnosticInformation
    processing_notes: str

class HPOSelection(BaseModel):
    selected_hpo_id: str = Field(description="Selected HPO ID")
    selected_hpo_name: str = Field(description="Selected HPO name")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    reasoning: str = Field(description="Detailed reasoning for selection")
    mapping_quality: str = Field(description="excellent/good/fair/poor")

class OpenAIProcessor:
    """Uses OpenAI LLM for medical text processing"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # Setup parsers
        self.symptom_parser = PydanticOutputParser(pydantic_object=SymptomExtractionResult)
        self.selection_parser = PydanticOutputParser(pydantic_object=HPOSelection)
        
        # Setup prompts
        self.symptom_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical expert specializing in Chinese clinical descriptions. 
            You will analyze Chinese clinical text and extract symptoms with high accuracy.
            
            {format_instructions}"""),
            ("user", """Analyze the following Chinese clinical text and perform these tasks:

1. **症状识别**: Extract ALL symptom descriptions, clinical signs, and phenotypic observations
2. **标准化**: Convert to standard medical terminology in Chinese
3. **分类整理**: Group symptoms into clinical categories
4. **重要信息保留**: Preserve diagnostic information (lab values, imaging, temporal info)
5. **英文翻译**: Translate each symptom to precise English medical terminology

Chinese Clinical Text:
{chinese_text}

Focus on medical accuracy and completeness. If uncertain about a translation, indicate lower confidence.""")
        ])
        
        self.selection_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical expert making final decisions on HPO term mapping.
            You will select the BEST HPO term from candidates based on clinical accuracy.
            
            {format_instructions}"""),
            ("user", """Select the BEST HPO term for the clinical description:

**Clinical Term:**
- Chinese: {chinese}
- English: {english}
- Category: {category}
- Severity: {severity}
- Temporal: {temporal}
- Context: {context}

**HPO Candidates:**
{candidates}

**Selection Criteria:**
1. Semantic and clinical accuracy
2. Appropriate level of specificity
3. Medical appropriateness
4. Confidence threshold: {confidence_threshold}

If no term meets the confidence threshold, set confidence to 0.0 and explain why.""")
        ])
    
    def extract_and_process_symptoms(self, chinese_text: str) -> Dict[str, Any]:
        """Extract, standardize, and translate symptoms using OpenAI"""
        
        try:
            # Format the prompt
            formatted_prompt = self.symptom_prompt.format_prompt(
                chinese_text=chinese_text,
                format_instructions=self.symptom_parser.get_format_instructions()
            )
            
            # Get response from LLM
            response = self.llm.invoke(formatted_prompt.to_messages())
            
            # Parse the response
            result = self.symptom_parser.parse(response.content)
            
            # Convert to ClinicalTerm objects
            clinical_terms = []
            for symptom in result.extracted_symptoms:
                term = ClinicalTerm(
                    chinese=symptom.original_chinese,
                    english=symptom.english_translation,
                    category=symptom.category,
                    confidence=symptom.confidence,
                    context=symptom.context,
                    severity=symptom.severity,
                    temporal=symptom.temporal
                )
                clinical_terms.append(term)
            
            return {
                'clinical_terms': clinical_terms,
                'clinical_summary': result.clinical_summary.dict(),
                'diagnostic_information': result.diagnostic_information.dict(),
                'processing_notes': result.processing_notes
            }
            
        except Exception as e:
            logger.error(f"OpenAI processing error: {e}")
            raise

class RAGBasedSelector:
    """Uses RAG (Retrieval-Augmented Generation) for HPO term selection"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=HPOSelection)
        
        self.selection_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical expert making final decisions on HPO term mapping.
            You will select the BEST HPO term from retrieved candidates based on clinical accuracy.
            
            {format_instructions}"""),
            ("user", """Select the BEST HPO term for the clinical description:

**Clinical Term:**
- Chinese: {chinese}
- English: {english}
- Category: {category}
- Severity: {severity}
- Temporal: {temporal}
- Context: {context}

**Retrieved HPO Candidates (from vector search):**
{candidates}

**Selection Criteria:**
1. Semantic and clinical accuracy
2. Appropriate level of specificity  
3. Medical appropriateness
4. Confidence threshold: {confidence_threshold}

Select the most appropriate HPO term. If no term meets the confidence threshold, set confidence to 0.0 and explain why.""")
        ])
    
    def select_best_term(self, query_term: ClinicalTerm, candidates: List[HPOCandidate], 
                        confidence_threshold: float = 0.7) -> Optional[HPOMapping]:
        """Select the best HPO term using RAG approach"""
        
        if not candidates:
            return None
        
        # Prepare candidate information for LLM
        candidate_info = []
        for candidate in candidates:
            candidate_info.append({
                'hpo_id': candidate.hpo_id,
                'hpo_name': candidate.hpo_name,
                'description': candidate.description,
                'similarity_score': candidate.score
            })
        
        candidates_text = json.dumps(candidate_info, indent=2, ensure_ascii=False)
        
        try:
            # Format the prompt
            formatted_prompt = self.selection_prompt.format_prompt(
                chinese=query_term.chinese,
                english=query_term.english,
                category=query_term.category,
                severity=query_term.severity,
                temporal=query_term.temporal,
                context=query_term.context,
                candidates=candidates_text,
                confidence_threshold=confidence_threshold,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # Get response from LLM
            response = self.llm.invoke(formatted_prompt.to_messages())
            
            # Parse the response
            result = self.parser.parse(response.content)
            
            # Check if selection meets threshold
            if result.confidence >= confidence_threshold:
                mapping = HPOMapping(
                    original_chinese=query_term.chinese,
                    english_translation=query_term.english,
                    hpo_id=result.selected_hpo_id,
                    hpo_name=result.selected_hpo_name,
                    confidence=result.confidence,
                    context=query_term.context,
                    reasoning=result.reasoning
                )
                return mapping
            else:
                logger.warning(f"No suitable HPO term found for: {query_term.chinese} (confidence: {result.confidence:.3f})")
                return None
                
        except Exception as e:
            logger.error(f"RAG selection error: {e}")
            return None

class HPOVectorStore:
    """Handles HPO vector store operations"""
    
    def __init__(self, folder_path: str = './embeddings/voyage_3/'):
        self.folder_path = folder_path
        self.embeddings = VoyageAIEmbeddings(model="voyage-3")
        self.vectorstore = None
        
    def load_vectorstore(self):
        """Load the pre-built HPO vector store"""
        try:
            self.vectorstore = FAISS.load_local(
                folder_path=self.folder_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("HPO vector store loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            raise
    
    def search_hpo_terms(self, query: str, k: int = 10) -> List[HPOCandidate]:
        """Search for HPO terms using vector similarity"""
        if not self.vectorstore:
            raise ValueError("Vector store not loaded")
        
        try:
            # Perform similarity search
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            candidates = []
            for doc, score in results:
                # Extract HPO ID and name from document
                hpo_id = doc.metadata.get('id', 'Unknown')
                hpo_name = doc.metadata.get('label', 'Unknown')
                description = doc.page_content
                
                # Convert distance to similarity score (FAISS returns distances)
                similarity_score = 1.0 / (1.0 + score)
                
                candidate = HPOCandidate(
                    hpo_id=hpo_id,
                    hpo_name=hpo_name,
                    description=description,
                    score=similarity_score
                )
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}")
            return []

class RAGChineseToHPOTransformer:
    """Main class using RAG approach for Chinese to HPO transformation"""
    
    def __init__(self, llm: ChatOpenAI, vectorstore_path: str = './embeddings/voyage_3/'):
        self.llm = llm
        self.openai_processor = OpenAIProcessor(llm)
        self.vectorstore = HPOVectorStore(vectorstore_path)
        self.selector = RAGBasedSelector(llm)
        
        # Load vector store
        self.vectorstore.load_vectorstore()
    
    def transform(self, chinese_text: str) -> Dict[str, Any]:
        """Transform Chinese clinical description to HPO terms using RAG"""
        logger.info("Starting RAG-based transformation process...")
        start_time = datetime.now()
        
        # Step 1: Process Chinese text using OpenAI
        logger.info("Step 1: Processing Chinese text with OpenAI...")
        step1_results = self.openai_processor.extract_and_process_symptoms(chinese_text)
        
        # Step 2: RAG-based mapping to HPO terms
        logger.info("Step 2: RAG-based mapping to HPO terms...")
        step2_results = self._rag_map_to_hpo_terms(step1_results['clinical_terms'])
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Combine results
        result = {
            'original_text': chinese_text,
            'clinical_terms': step1_results['clinical_terms'],
            'clinical_summary': step1_results['clinical_summary'],
            'diagnostic_information': step1_results['diagnostic_information'],
            'processing_notes': step1_results['processing_notes'],
            'hpo_mappings': step2_results['mappings'],
            'mapping_summary': step2_results['summary'],
            'total_processing_time': total_time,
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def _rag_map_to_hpo_terms(self, clinical_terms: List[ClinicalTerm]) -> Dict[str, Any]:
        """Map clinical terms to HPO terms using RAG approach"""
        
        mappings = []
        successful_mappings = 0
        high_confidence_mappings = 0
        total_confidence = 0
        
        for term in clinical_terms:
            logger.info(f"Processing term: {term.chinese} -> {term.english}")
            
            try:
                # Step 1: Retrieve candidates from vector store
                candidates = self.vectorstore.search_hpo_terms(term.english, k=10)
                
                if not candidates:
                    logger.warning(f"No candidates found for term: {term.english}")
                    continue
                
                # Step 2: Use LLM to select best term (RAG approach)
                mapping = self.selector.select_best_term(term, candidates)
                
                if mapping:
                    mappings.append(mapping)
                    successful_mappings += 1
                    total_confidence += mapping.confidence
                    
                    if mapping.confidence >= 0.8:
                        high_confidence_mappings += 1
                    
                    logger.info(f"Mapped to HPO: {mapping.hpo_id} - {mapping.hpo_name} (confidence: {mapping.confidence:.3f})")
                else:
                    logger.warning(f"No suitable HPO term found for: {term.english}")
                    
            except Exception as e:
                logger.error(f"Error processing term {term.chinese}: {e}")
                continue
        
        # Create summary
        summary = {
            'total_terms': len(clinical_terms),
            'successfully_mapped': successful_mappings,
            'high_confidence_mappings': high_confidence_mappings,
            'average_confidence': total_confidence / successful_mappings if successful_mappings > 0 else 0,
            'mapping_success_rate': successful_mappings / len(clinical_terms) if clinical_terms else 0
        }
        
        return {
            'mappings': mappings,
            'summary': summary
        }
    
    def batch_transform(self, chinese_texts: List[str]) -> List[Dict[str, Any]]:
        """Transform multiple Chinese clinical descriptions"""
        results = []
        
        for i, text in enumerate(chinese_texts):
            logger.info(f"Processing text {i+1}/{len(chinese_texts)}")
            try:
                result = self.transform(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing text {i+1}: {e}")
                results.append({
                    'original_text': text,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def save_results(self, results: Dict[str, Any], filename: str):
        """Save results to JSON file"""
        serializable_results = self._make_serializable(results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results saved to {filename}")
    
    def _make_serializable(self, obj):
        """Convert dataclasses and other objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (ClinicalTerm, HPOMapping)):
            return obj.__dict__
        else:
            return obj

# Example usage and test functions
def test_rag_transformer():
    """Test the RAG-based transformer with sample Chinese clinical text"""
    
    # Import your LLM (assuming it's already configured)
    from llm import llm  # Your ChatOpenAI instance
    
    # Sample Chinese clinical texts
    test_texts = [
        """
        发育迟缓/身材矮小。右耳前赘生物，性发育迟缓待排。骶1椎板未闭合。无惊厥、抽搐。肾脏病理：光镜FSGS。
        行走呈痉挛步态，容易摔跤，不会跳绳、骑自行车。
        食纳增加，平素一碗面/餐，1月前增加至两碗面/餐，吃零食，小便频率增加，1-2h/次，夜尿情况不详 。
        父母非近亲结婚。无家族遗传史。
        """
    ]
    
    # Initialize transformer
    transformer = RAGChineseToHPOTransformer(llm)
    
    # Transform each text
    for i, text in enumerate(test_texts):
        print(f"\n=== Processing Text {i+1} ===")
        print(f"Original: {text.strip()}")
        
        try:
            results = transformer.transform(text)
            
            print(f"\nClinical Terms Extracted:")
            for term in results['clinical_terms']:
                print(f"  {term.chinese} -> {term.english} ({term.category})")
            
            print(f"\nHPO Mappings:")
            for mapping in results['hpo_mappings']:
                print(f"  {mapping.original_chinese} -> {mapping.english_translation}")
                print(f"    HPO: {mapping.hpo_id} - {mapping.hpo_name}")
                print(f"    Confidence: {mapping.confidence:.3f}")
                print(f"    Reasoning: {mapping.reasoning}")
                print()
            
            print(f"Summary: {results['mapping_summary']}")
            
            # Save individual results
            transformer.save_results(results, f'rag_results_{i+1}.json')
            
        except Exception as e:
            print(f"Error processing text {i+1}: {e}")
    
    # Test batch processing
    print("\n=== Batch Processing Test ===")
    try:
        batch_results = transformer.batch_transform(test_texts)
        print(f"Processed {len(batch_results)} texts successfully")
        
        # Save batch results
        with open('batch_rag_results.json', 'w', encoding='utf-8') as f:
            json.dump(transformer._make_serializable(batch_results), f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"Batch processing error: {e}")

if __name__ == "__main__":
    # Run the test
    from dotenv import load_dotenv
    load_dotenv()
    test_rag_transformer()