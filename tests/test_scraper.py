import unittest
import pandas as pd
import tempfile
import os
from unittest.mock import patch, Mock
import sys
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from scraper import Scraper


class TestDataScraper(unittest.TestCase):
    def setUp(self):
        self.sample_df = pd.DataFrame({
            'Text': ['Test message 1', 'Test message 2'],
            'Label': ['Bullying', 'Not-Bullying'],
            'Types': ['Religious', 'Racism']
        })
        self.scraper = Scraper(data_path=None)
        self.scraper.df = self.sample_df.copy()

    # Test loading a CSV file successfully
    def test_load_csv_data_success(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            self.sample_df.to_csv(tmp.name, index=False)
            path = tmp.name

        try:
            scraper = Scraper(data_path=path)
            df = scraper.load_data()
            self.assertIsNotNone(df)
            self.assertEqual(len(df), 2)
            self.assertIn('Text', df.columns)
        finally:
            os.remove(path)
    # Test get_data raises if no data is loaded
    def test_get_data_raises_without_load(self):
        scraper = Scraper(data_path=None)
        with self.assertRaises(ValueError):
            scraper.get_data()
    # Test duplicate removal
    def test_drop_duplicate_rows(self):
        df_dup = pd.concat([self.sample_df, self.sample_df])
        self.scraper.df = df_dup
        self.scraper.drop_duplicate_rows()
        self.assertEqual(len(self.scraper.df), 2)
    # Test normalization of 'Types' column
    def test_normalize_types(self): 
        result = self.scraper.normalize_types('Religon')
        self.assertEqual(result, 'religion')
        result = self.scraper.normalize_types('racism')
        self.assertEqual(result, 'ethnicity')
    # Test normalization of 'Label' column
    def test_normalize_label(self):
        self.assertEqual(self.scraper.normalize_label('Not-Bullying'), 'NB')
        self.assertEqual(self.scraper.normalize_label('Bullying'), 'B')
    
    # Test applying a normalization function
    def test_apply_function(self):
        self.scraper.apply_function('Label', self.scraper.normalize_label)
        self.assertListEqual(self.scraper.df['Label'].tolist(), ['B', 'NB'])
    
    # Test unique value printing does not raise errors
    def test_print_unique_values(self):
        try:
            self.scraper.print_unique_values('Label')
        except Exception:
            self.fail("print_unique_values raised unexpectedly!")
    
    
    #Test MongoDB insertion with mock
    @patch("scraper.MongoClient")
    def test_insert_to_mongo(self, mock_mongo_client):
        
        mock_client_instance = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        mock_mongo_client.return_value = mock_client_instance

        self.scraper.insert_to_mongo()
        mock_collection.insert_many.assert_called_once()


