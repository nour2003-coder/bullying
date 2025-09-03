import pymongo
from pymongo import MongoClient
from textblob import TextBlob
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import numpy as np
from tqdm import tqdm  # for progress bar
import langid
class NLPPipeline:
    def __init__(self, mongo_uri="mongodb://localhost:27017/"):
        """Initialize MongoDB connection and NLP tools"""
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.client = MongoClient(mongo_uri)
        self.db = self.client.harcelement
        self.collection = self.db.posts
    

    def detect_language(self, text):
        """Robust language detection using langdetect and langid"""
        if not text or len(text.strip()) < 3:
            return 'unknown'
        
        try:
            lang1 = detect(text)
            lang2, _ = langid.classify(text)
            
            # Use consensus or default to langid (more stable)
            if lang1 == lang2:
                return lang1
            else:
                return lang2
        except Exception:
            return 'unknown'


    
    def analyze_sentiment(self, text):
        """Use hybrid sentiment analysis: VADER + TextBlob"""
        if not text:
            return {'sentiment': 'neutral', 'polarity': 0.0, 'subjectivity': 0.0}
        
        # TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # VADER
        vader_scores = self.vader_analyzer.polarity_scores(text)
        vader_compound = vader_scores['compound']
        
        # Combine logic (you can adjust thresholds as needed)
        if vader_compound >= 0.3:
            sentiment = 'positive'
        elif vader_compound <= -0.3:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'vader_compound': vader_compound
        }

    
    def calculate_toxicity_score(self, text, label, sentiment_data):
        base_score = 0.0

        # Labels précis pour ton dataset
        if label.upper() == 'B':  # Bullying
            base_score += 0.7
        elif label.upper() == 'NB':  # Not Bullying
            base_score += 0.1
        else:
            # Cas imprévu, on reste faible
            base_score += 0.1
        
        # Score VADER compound (valeurs entre -1 et 1)
        vader_compound = sentiment_data.get('vader_compound', 0)
        if vader_compound < -0.5:
            base_score += 0.2
        elif vader_compound < -0.2:
            base_score += 0.1

        # Bonus si le texte est long (>10 mots)
        if text and len(text.split()) > 10:
            base_score += 0.1

        return min(1.0, base_score)


    def process_document(self, doc):
        """Process a single document with NLP analysis"""
        text = doc.get('preprocessed_text', doc.get('text', ''))
        original_text = doc.get('original_text', doc.get('text', ''))
        label = doc.get('label', '')
        
        # Language detection
        language = self.detect_language(original_text)
        
        # Sentiment analysis
        sentiment_data = self.analyze_sentiment(original_text)

        
        # Toxicity score calculation
        toxicity_score = self.calculate_toxicity_score(
            original_text, label, sentiment_data
        )
        
        # Prepare update data
        update_data = {
            'language': language,
            'sentiment': sentiment_data['sentiment'],
            'polarity': sentiment_data['polarity'],
            'subjectivity': sentiment_data['subjectivity'],
            'vader_compound': sentiment_data['vader_compound'],
            'toxicity_score': toxicity_score,
            'nlp_processed_at': datetime.now()
        }

        
        return update_data
    
    def process_collection(self, batch_size=50):
        """Process all documents in the collection"""
        total_docs = self.collection.count_documents({})
        print(f"Total documents to process: {total_docs}")
        
        processed_count = 0

        for skip in tqdm(range(0, total_docs, batch_size), desc="Processing Batches"):
            documents = list(self.collection.find().skip(skip).limit(batch_size))
            
            for doc in documents:
                try:
                    update_data = self.process_document(doc)
                    
                    self.collection.update_one(
                        {'_id': doc['_id']},
                        {'$set': update_data}
                    )
                    processed_count += 1
                    
                except Exception as e:
                    print(f"Failed to process document {doc.get('_id')}: {e}")
                    continue
        
        print(f"✅ Finished processing {processed_count} documents.")
        return processed_count

    
    def get_analysis_summary(self):
        """Get summary statistics of the NLP analysis"""
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_docs': {'$sum': 1},
                    'avg_toxicity': {'$avg': '$toxicity_score'},
                    'sentiment_distribution': {
                        '$push': '$sentiment'
                    },
                    'language_distribution': {
                        '$push': '$language'
                    }
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        if result:
            data = result[0]
            
            # Count sentiment distribution
            sentiments = data['sentiment_distribution']
            sentiment_counts = {
                'positive': sentiments.count('positive'),
                'negative': sentiments.count('negative'),
                'neutral': sentiments.count('neutral')
            }
            
            # Count language distribution
            languages = data['language_distribution']
            language_counts = {}
            for lang in set(languages):
                language_counts[lang] = languages.count(lang)
            
            return {
                'total_documents': data['total_docs'],
                'average_toxicity_score': round(data['avg_toxicity'], 3),
                'sentiment_distribution': sentiment_counts,
                'language_distribution': language_counts
            }
        
        return None

def main():
    """Main execution function"""
    nlp_pipeline = NLPPipeline()
    
    # Process all documents
    processed_count = nlp_pipeline.process_collection()
    
    # Get analysis summary
    summary = nlp_pipeline.get_analysis_summary()
    
    print(f"\nNLP Processing completed!")
    print(f"Processed documents: {processed_count}")
    
    if summary:
        print(f"\nAnalysis Summary:")
        print(f"Total documents: {summary['total_documents']}")
        print(f"Average toxicity score: {summary['average_toxicity_score']}")
        print(f"Sentiment distribution: {summary['sentiment_distribution']}")
        print(f"Language distribution: {summary['language_distribution']}")
    
    # Show sample processed documents
    sample_docs = list(nlp_pipeline.collection.find().limit(3))
    print("\nSample processed documents:")
    for doc in sample_docs:
        print(f"Text: {doc.get('original_text', '')[:80]}...")
        print(f"Language: {doc.get('language', 'N/A')}")
        print(f"Sentiment: {doc.get('sentiment', 'N/A')} (polarity: {doc.get('polarity', 0):.2f})")
        print(f"Toxicity Score: {doc.get('toxicity_score', 0):.2f}")
        print("-" * 50)

if __name__ == "__main__":
    main()
