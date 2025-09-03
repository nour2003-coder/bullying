import pandas as pd
import re
import string
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
from pymongo import MongoClient
import nltk
import warnings
from bs4 import MarkupResemblesLocatorWarning
from pymongo import MongoClient, UpdateOne 
from nltk.corpus import wordnet
from nltk import pos_tag 
# Ignore BeautifulSoup's warning
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)



class TextPreprocessor:
    # Initialize preprocessing tools
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

    # Remove HTML tags
    def clean_html(self, text):
        if pd.isna(text):
            return ""
        if re.match(r'^[a-zA-Z]:[\\/].*', text):
            return text
        soup = BeautifulSoup(str(text), "html.parser")
        return soup.get_text()
    
    # Remove URLs
    def clean_urls(self, text):
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$$\$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        return url_pattern.sub('', text)
    
    # Remove special characters and extra whitespace
    def clean_special_chars(self, text):
        text = re.sub(r'[^\w\s\.\!\?\,\;\:]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    # Remove punctuation and digits
    def remove_punctuation_and_digits(self, text):
        text = re.sub(r'\d+', '', text)
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text
    
    # Remove stopwords from token list
    def remove_stopwords(self, tokens):
        if not isinstance(tokens, list):
            raise ValueError("Input should be a list of tokens")
        return [token for token in tokens if token.lower() not in self.stop_words]
    
    def get_wordnet_pos(self,treebank_tag):
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN 
    

    # Apply lemmatization to tokens
    def lemmatize_tokens(self, tokens):
        if not isinstance(tokens, list):
            raise ValueError("Input should be a list of tokens")

        try:
            pos_tags = pos_tag(tokens)  # List of (token, POS) tuples
            return [
                self.lemmatizer.lemmatize(token, self.get_wordnet_pos(tag))
                for token, tag in pos_tags
            ]
        except LookupError:
            # Fallback to simple lemmatization if POS tagging fails
            return [self.lemmatizer.lemmatize(token) for token in tokens]
        
    # Complete preprocessing pipeline
    def preprocess_text(self, text):
        if pd.isna(text) or text == "":
            return ""
        

        text = str(text).lower()
        
        # Remove HTML tags
        text = self.clean_html(text)

        # Remove URLs
        text = self.clean_urls(text)
        
        # Remove special characters
        text = self.clean_special_chars(text)
        
        # Remove punctuation and digits
        text = self.remove_punctuation_and_digits(text)
        
        # Tokenize
        tokens = word_tokenize(text, preserve_line=True)
        
        # Remove stopwords
        tokens = self.remove_stopwords(tokens)
        
        # Lemmatization
        tokens = self.lemmatize_tokens(tokens)
        
        # Filter out empty tokens
        tokens = [token for token in tokens if len(token) > 1]
        
        return ' '.join(tokens)


class MongoPreprocessor:
    # Initialize MongoDB connection and preprocessor
    def __init__(self, mongo_uri="mongodb://localhost:27017/"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client.harcelement
        self.collection = self.db.posts
        self.preprocessor = TextPreprocessor()
        
    # Preprocess documents in the MongoDB collection
    def preprocess_collection(self, batch_size=100):
        total_docs = self.collection.count_documents({})
        processed_count = 0

        for skip in range(0, total_docs, batch_size):
            documents = list(self.collection.find().skip(skip).limit(batch_size))
            bulk_updates = []

            for doc in documents:
                original_text = doc.get('Text', '')
                preprocessed_text = self.preprocessor.preprocess_text(original_text)

                bulk_updates.append(
                    UpdateOne(
                        {'_id': doc['_id']},
                        {'$set': {
                            'original_text': original_text,
                            'preprocessed_text': preprocessed_text
                        }}
                    )
                )
                processed_count += 1

            if bulk_updates:
                self.collection.bulk_write(bulk_updates)  # bulk update here

            print(f"Processed {processed_count}/{total_docs} documents")

        print("Preprocessing completed!")
        return processed_count


        
def main():
    mongo_preprocessor = MongoPreprocessor()
    
    # Preprocess all documents
    processed_count = mongo_preprocessor.preprocess_collection()
    
    # Show sample of preprocessed data
    sample_docs = list(mongo_preprocessor.collection.find().limit(3))
    print("\nSample preprocessed documents:")
    for doc in sample_docs:
        print(f"Original: {doc.get('original_text', '')[:100]}...")
        print(f"Preprocessed: {doc.get('preprocessed_text', '')[:100]}...")
        print("-" * 50)

if __name__ == "__main__":
    main()
