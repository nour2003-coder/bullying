DATA_PATH = "C:/Users/user/Documents/smart_conseil/data/raw/Approach to Social Media Cyberbullying and Harassment Detection Using Advanced Machine Learning.csv"
types_mapping = {
    'religious': 'religion',
    'religon': 'religion',
    'ethnically': 'ethnicity',
    'racism': 'ethnicity',
    'threat': 'threats',
    'vocation': 'vocational',
    'saxual': 'sexual',
}
import pandas as pd
import numpy as np
from pymongo import MongoClient
from datetime import datetime
from datetime import datetime, timedelta
import random
class Scraper:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
    #Load data from CSV file
    def load_data(self):
        try:
            df = pd.read_csv(self.data_path)
            print(f"Loaded {len(df)} records from {self.data_path}")
            self.df = df
            return self.df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None
    #Return the loaded DataFrame
    def get_data(self):
        if self.df is not None:
            return self.df
        else:
            raise ValueError("Data not loaded. Please call load_data() first.")
    
    #Print unique values in a specified column
    def print_unique_values(self, column_name):   
        if self.df is not None and column_name in self.df.columns:
            unique_values = self.df[column_name].unique().tolist()
            print(column_name)
            print(unique_values)
        else:
            raise ValueError(f"Column '{column_name}' does not exist in the DataFrame.") 
    
    # Drop duplicate rows from the Df
    def drop_duplicate_rows(self):
        initial = len(self.df)
        self.df.drop_duplicates(inplace=True)
        final = len(self.df)
        print(f"Dropped {initial - final} duplicate rows. Remaining records: {final}")
    
    def normalize_types(self,val):
        if pd.isna(val):
            return np.nan
        val = val.strip().lower()
        return types_mapping.get(val, val)
    def normalize_label(self,val):
        if pd.isna(val):
            return np.nan
        val = val.strip().lower()
        if val[0] == 'n':
            return 'NB'
        else :
            return 'B'
    #apply a function to a column in the DataFrame
    def apply_function(self, column_name, func):
        if self.df is not None and column_name in self.df.columns:
            self.df[column_name] = self.df[column_name].apply(func)
            print(f"Applied function to column '{column_name}'.")
        else:
            raise ValueError(f"Column '{column_name}' does not exist in the DataFrame.")
    
    # Print the number of null values in a specified column
    def print_null_values(self, column_name):
        if self.df is not None and column_name in self.df.columns:
            null_count = self.df[column_name].isnull().sum()
            null_values=self.df[df[column_name].isnull()]
            print(f"Column '{column_name}' has {null_count} null values.")
            if null_count > 0:
                print("Null values in the column:")
                print(null_values)
        else:
            raise ValueError(f"Column '{column_name}' does not exist in the DataFrame.")
    def visualize_data(self):
        if self.df is not None:
            print("DataFrame head:")
            print(self.df.head())
            print("\nDataFrame info:")
            print(self.df.info())
            print("\nDataFrame description:")
            print(self.df.describe())
        else:
            raise ValueError("Data not loaded. Please call load_data() first.")
    def visualization(self,column_name):
        if self.df is not None:
            self.df[column_name].value_counts().plot(kind='bar')
        else:
            raise ValueError("Data not loaded. Please call load_data() first.")
    def generate_post_time(self,start_date, end_date):
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = end - start
        rand_days = random.randint(0, delta.days)
        rand_seconds = random.randint(0, 24 * 3600 - 1)
        post_time = start + timedelta(days=rand_days, seconds=rand_seconds)

        # Optional: Peak hours (simulate more posts in evening)
        if random.random() < 0.6:
            post_time = post_time.replace(hour=random.randint(18, 22),
                                        minute=random.randint(0, 59),
                                        second=random.randint(0, 59))
        return post_time
    def insert_to_mongo(self):
        try:
            client = MongoClient("mongodb://localhost:27017/")
            db = client['harcelement']
            collection = db['posts']
            collection.insert_many(self.df.to_dict(orient='records'))
            print("Data loaded into MongoDB successfully.")
        except Exception as e:
            print(f"Error loading data into MongoDB: {e}")
        finally:
            client.close()
  
        






if __name__ == "__main__":
    scraper = Scraper(DATA_PATH)
    df = scraper.load_data()
    if df is None:
        raise ValueError("Failed to load data. Exiting.")
    scraper.visualize_data()
    scraper.print_unique_values('Label')
    scraper.print_unique_values('Types')
    scraper.drop_duplicate_rows()
    scraper.apply_function('Types', scraper.normalize_types)
    scraper.apply_function('Label', scraper.normalize_label)
    scraper.print_null_values('Types')
    scraper.print_null_values('Label')
    df.loc[df['Label'].isna(), 'Label'] = 'NB'
    df[df['Types'].isna()]['Label'].value_counts()
    df.loc[df['Types'].isna() & (df['Label'] == 'NB'), 'Types'] = 'none'
    df.loc[df['Types'].isna() & (df['Label'] == 'B'), 'Types'] = 'unknown'
    df['Id_post'] = range(1, len(df) + 1)
    df['created_at'] = [scraper.generate_post_time("2024-01-01", "2024-12-31") for _ in range(len(df))]
    scraper.visualization('Label')
    scraper.visualization('Types')
    scraper.insert_to_mongo()
