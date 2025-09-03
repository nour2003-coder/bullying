"""
Elasticsearch ingestion script
Transfers enriched data from MongoDB to Elasticsearch
"""

from elasticsearch import Elasticsearch, helpers
import pymongo
from pymongo import MongoClient
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElasticsearchIngestor:
    def __init__(self, 
                 es_host="http://localhost:9200",
                 mongo_uri="mongodb://localhost:27017/",
                 index_name="harcelement_posts"):
        """Initialize Elasticsearch and MongoDB connections"""
        self.es = Elasticsearch([es_host])
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client.harcelement
        self.collection = self.db.posts
        self.index_name = index_name
        
    def create_index_mapping(self):
        """Create Elasticsearch index with proper mapping"""
        mapping = {
            "mappings": {
                "properties": {
                    "id_post": {"type": "keyword"},
                    "titre": {"type": "text", "analyzer": "standard"},
                    "contenu": {"type": "text", "analyzer": "standard"},
                    "original_text": {"type": "text", "analyzer": "standard","fields": {"keyword": {"type": "keyword","ignore_above": 256
    }}},
                    "preprocessed_text": {"type": "text", "analyzer": "standard"},
                    "auteur": {"type": "keyword"},
                    "date": {"type": "date"},
                    "url": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "sentiment": {"type": "keyword"},
                    "polarity": {"type": "float"},
                    "subjectivity": {"type": "float"},
                    "vader_compound": {"type": "float"},
                    "toxicity_score": {"type": "float"},
                    "label": {"type": "keyword"},
                    "type": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "nlp_processed_at": {"type": "date"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }
        
        # Delete index if it exists
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
            logger.info(f"Deleted existing index: {self.index_name}")
        
        # Create new index
        self.es.indices.create(index=self.index_name, body=mapping)
        logger.info(f"Created index: {self.index_name}")
    
    def transform_document(self, mongo_doc):
        """Transform MongoDB document for Elasticsearch"""
        # Remove MongoDB ObjectId to avoid issues
        if '_id' in mongo_doc:
            del mongo_doc['_id']
        
        # Extract dates safely (MongoDB datetime to ISO string or pass as is)
        def safe_date(val):
            if val is None:
                return datetime.now()
            return val
        
        es_doc = {
            "id_post": str(mongo_doc.get('Id_post', '')),
            "titre": f"Post {str(mongo_doc.get('Id_post', ''))[:8]}",  # Generate title
            "contenu": mongo_doc.get('original_text', mongo_doc.get('Text', '')),
            "original_text": mongo_doc.get('original_text', mongo_doc.get('Text', '')),
            "preprocessed_text": mongo_doc.get('preprocessed_text', ''),
            "auteur": f"user_{hash(mongo_doc.get('Id_post', '')) % 1000}",  # Anonymous author
            "date": safe_date(mongo_doc.get('created_at')),
            "url": f"https://example.com/post/{mongo_doc.get('Id_post', '')}",
            "language": mongo_doc.get('language', 'unknown'),
            "sentiment": mongo_doc.get('sentiment', 'neutral'),
            "polarity": float(mongo_doc.get('polarity', 0.0)),
            "subjectivity": float(mongo_doc.get('subjectivity', 0.0)),
            "vader_compound": float(mongo_doc.get('vader_compound', 0.0)),
            "toxicity_score": float(mongo_doc.get('toxicity_score', 0.0)),
            "label": mongo_doc.get('Label', ''),
            "type": mongo_doc.get('Types', ''),
            "created_at": safe_date(mongo_doc.get('created_at')),
            "nlp_processed_at": safe_date(mongo_doc.get('nlp_processed_at'))
        }
        
        return es_doc
    
    def bulk_index_documents(self, batch_size=100):
        """Bulk index documents from MongoDB to Elasticsearch"""
        total_docs = self.collection.count_documents({})
        logger.info(f"Starting bulk indexing of {total_docs} documents")
        
        def doc_generator():
            """Generator for bulk indexing"""
            for doc in self.collection.find():
                es_doc = self.transform_document(doc)
                yield {
                    "_index": self.index_name,
                    "_source": es_doc
                }
        
        # Perform bulk indexing
        success_count = 0
        error_count = 0
        
        for success, info in helpers.parallel_bulk(
            self.es,
            doc_generator(),
            chunk_size=batch_size,
            thread_count=4
        ):
            if success:
                success_count += 1
            else:
                error_count += 1
                logger.error(f"Indexing error: {info}")
            
            if (success_count + error_count) % 100 == 0:
                logger.info(f"Indexed {success_count} documents, {error_count} errors")
        
        logger.info(f"Bulk indexing completed: {success_count} successful, {error_count} errors")
        return success_count, error_count
    
    def verify_indexing(self):
        """Verify that documents were indexed correctly"""
        self.es.indices.refresh(index=self.index_name)
        
        stats = self.es.indices.stats(index=self.index_name)
        doc_count = stats['indices'][self.index_name]['total']['docs']['count']
        
        search_result = self.es.search(
            index=self.index_name,
            body={"query": {"match_all": {}}, "size": 3}
        )
        
        return {
            'document_count': doc_count,
            'sample_documents': search_result['hits']['hits']
        }
    
    def create_sample_queries(self):
        """Create sample queries to test the index"""
        queries = [
            {
                "name": "High toxicity posts",
                "query": {
                    "range": {
                        "toxicity_score": {"gte": 0.7}
                    }
                }
            },
            {
                "name": "Negative sentiment posts",
                "query": {
                    "term": {
                        "sentiment": "negative"
                    }
                }
            },
            {
                "name": "Bullying posts",
                "query": {
                    "term": {
                        "label": "B"  # Assuming label 'B' means Bullying in your dataset
                    }
                }
            }
        ]
        
        results = {}
        for query_info in queries:
            result = self.es.search(
                index=self.index_name,
                body={"query": query_info["query"], "size": 5}
            )
            results[query_info["name"]] = {
                "total_hits": result['hits']['total']['value'],
                "sample_docs": result['hits']['hits']
            }
        
        return results

def main():
    """Main execution function"""
    ingestor = ElasticsearchIngestor()
    
    try:
        ingestor.create_index_mapping()
        success_count, error_count = ingestor.bulk_index_documents()
        verification = ingestor.verify_indexing()
        
        print(f"\nElasticsearch Ingestion Results:")
        print(f"Successfully indexed: {success_count} documents")
        print(f"Errors: {error_count}")
        print(f"Total documents in index: {verification['document_count']}")
        
        print(f"\nSample indexed documents:")
        for hit in verification['sample_documents']:
            doc = hit['_source']
            print(f"ID: {doc['id_post'][:8]}...")
            print(f"Content: {doc['contenu'][:80]}...")
            print(f"Sentiment: {doc['sentiment']}, Toxicity: {doc['toxicity_score']:.2f}")
            print("-" * 50)
        
        query_results = ingestor.create_sample_queries()
        print(f"\nSample Query Results:")
        for query_name, result in query_results.items():
            print(f"{query_name}: {result['total_hits']} matches")
        
    except Exception as e:
        logger.error(f"Error during Elasticsearch ingestion: {e}")

if __name__ == "__main__":
    main()
