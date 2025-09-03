import unittest
from unittest.mock import Mock, patch
import sys
sys.path.append('../scripts')

from scripts.preprocessing import TextPreprocessor

class TestTextPreprocessor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.preprocessor = TextPreprocessor()
    
    def test_clean_html(self):
        """Test HTML tag removal"""
        html_text = "<p>This is a <strong>test</strong> message.</p>"
        cleaned = self.preprocessor.clean_html(html_text)
        self.assertEqual(cleaned, "This is a test message.")
    
    def test_clean_urls(self):
        """Test URL removal"""
        text_with_url = "Check this out https://example.com/test and this http://test.com"
        cleaned = self.preprocessor.clean_urls(text_with_url)
        self.assertEqual(cleaned, "Check this out  and this ")
    
    def test_clean_special_chars(self):
        """Test special character removal"""
        text_with_special = "Hello @user! This is #awesome & cool!!!"
        cleaned = self.preprocessor.clean_special_chars(text_with_special)
        # Should keep basic punctuation but remove special chars
        self.assertNotIn('@', cleaned)
        self.assertNotIn('#', cleaned)
        self.assertNotIn('&', cleaned)
    
    def test_remove_punctuation_and_digits(self):
        """Test punctuation and digit removal"""
        text_with_punct = "Hello! This is test123 message."
        cleaned = self.preprocessor.remove_punctuation_and_digits(text_with_punct)
        self.assertNotIn('!', cleaned)
        self.assertNotIn('.', cleaned)
        self.assertNotIn('123', cleaned)
    
    def test_remove_stopwords(self):
        """Test stopword removal"""
        tokens = ['this', 'is', 'a', 'test', 'message', 'with', 'stopwords']
        filtered = self.preprocessor.remove_stopwords(tokens)
        
        # Common stopwords should be removed
        self.assertNotIn('this', filtered)
        self.assertNotIn('is', filtered)
        self.assertNotIn('a', filtered)
        self.assertIn('test', filtered)
        self.assertIn('message', filtered)
    
    def test_lemmatize_tokens(self):
        """Test lemmatization"""
        tokens = ['cats',  'flies']
        lemmatized = self.preprocessor.lemmatize_tokens(tokens)
        
        # Check if words are lemmatized (basic check)
        self.assertIn('cat', lemmatized)  # cats -> cat
        self.assertIn('fly', lemmatized)
    def test_preprocess_text_complete(self):
        """Test complete preprocessing pipeline"""
        complex_text = "<p>Hello @user! This is a TEST123 message with https://example.com URL.</p>"
        processed = self.preprocessor.preprocess_text(complex_text)
        
        # Should be cleaned, lowercased, and processed
        self.assertIsInstance(processed, str)
        self.assertNotIn('<p>', processed)
        self.assertNotIn('@user', processed)
        self.assertNotIn('https://example.com', processed)
        self.assertNotIn('123', processed)
    
    def test_preprocess_empty_text(self):
        """Test preprocessing with empty or None text"""
        self.assertEqual(self.preprocessor.preprocess_text(""), "")
        self.assertEqual(self.preprocessor.preprocess_text(None), "")
    
    def test_preprocess_text_with_only_stopwords(self):
        """Test preprocessing text with only stopwords"""
        stopword_text = "the a an is are was were"
        processed = self.preprocessor.preprocess_text(stopword_text)
        # Should result in empty or very short string after removing stopwords
        self.assertTrue(len(processed) < len(stopword_text))

if __name__ == '__main__':
    unittest.main()
