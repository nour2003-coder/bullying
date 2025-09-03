"""
Unit tests for the NLP pipeline module
"""

import unittest
from unittest.mock import Mock, patch
import sys
sys.path.append('../scripts')

from scripts.nlp_pipeline import NLPPipeline

class TestNLPPipeline(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.nlp_pipeline = NLPPipeline()
    
    def test_detect_language_english(self):
        """Test language detection for English text"""
        english_text = "This is a test message in English language"
        language = self.nlp_pipeline.detect_language(english_text)
        self.assertEqual(language, 'en')
    
    def test_detect_language_empty_text(self):
        """Test language detection with empty text"""
        language = self.nlp_pipeline.detect_language("")
        self.assertEqual(language, 'unknown')
        
        language = self.nlp_pipeline.detect_language("ab")  # Too short
        self.assertEqual(language, 'unknown')
    
    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis for positive text"""
        positive_text = "I love this amazing product! It's wonderful and fantastic!"
        result = self.nlp_pipeline.analyze_sentiment_textblob(positive_text)
        
        self.assertEqual(result['sentiment'], 'positive')
        self.assertGreater(result['polarity'], 0.1)
        self.assertIsInstance(result['subjectivity'], float)
    
    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis for negative text"""
        negative_text = "I hate this terrible product! It's awful and disgusting!"
        result = self.nlp_pipeline.analyze_sentiment_textblob(negative_text)
        
        self.assertEqual(result['sentiment'], 'negative')
        self.assertLess(result['polarity'], -0.1)
    
    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis for neutral text"""
        neutral_text = "This is a product. It exists."
        result = self.nlp_pipeline.analyze_sentiment_textblob(neutral_text)
        
        self.assertEqual(result['sentiment'], 'neutral')
        self.assertGreaterEqual(result['polarity'], -0.1)
        self.assertLessEqual(result['polarity'], 0.1)
    
    def test_analyze_sentiment_empty_text(self):
        """Test sentiment analysis with empty text"""
        result = self.nlp_pipeline.analyze_sentiment_textblob("")
        
        self.assertEqual(result['sentiment'], 'neutral')
        self.assertEqual(result['polarity'], 0.0)
        self.assertEqual(result['subjectivity'], 0.0)
    
    def test_calculate_toxicity_score_bullying(self):
        """Test toxicity score calculation for bullying content"""
        text = "You are stupid and worthless"
        label = "Bullying"
        sentiment_data = {'polarity': -0.8, 'subjectivity': 0.9}
        
        score = self.nlp_pipeline.calculate_toxicity_score(text, label, sentiment_data)
        
        self.assertGreater(score, 0.7)  # Should be high for bullying
        self.assertLessEqual(score, 1.0)  # Should not exceed 1.0
    
    def test_calculate_toxicity_score_normal(self):
        """Test toxicity score calculation for normal content"""
        text = "This is a normal message"
        label = "Normal"
        sentiment_data = {'polarity': 0.1, 'subjectivity': 0.3}
        
        score = self.nlp_pipeline.calculate_toxicity_score(text, label, sentiment_data)
        
        self.assertLess(score, 0.5)  # Should be low for normal content
        self.assertGreaterEqual(score, 0.0)  # Should not be negative
    
    def test_process_document(self):
        """Test complete document processing"""
        sample_doc = {
            'text': 'This is a test message',
            'original_text': 'This is a test message',
            'preprocessed_text': 'test message',
            'label': 'Normal',
            'id_post': 'test123'
        }
        
        result = self.nlp_pipeline.process_document(sample_doc)
        
        # Check if all required fields are present
        required_fields = ['language', 'sentiment', 'polarity', 'subjectivity', 
                          'toxicity_score', 'nlp_processed_at']
        for field in required_fields:
            self.assertIn(field, result)
        
        # Check data types
        self.assertIsInstance(result['language'], str)
        self.assertIsInstance(result['sentiment'], str)
        self.assertIsInstance(result['polarity'], float)
        self.assertIsInstance(result['subjectivity'], float)
        self.assertIsInstance(result['toxicity_score'], float)

if __name__ == '__main__':
    unittest.main()