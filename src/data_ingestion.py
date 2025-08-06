import os
import pandas as pd
from google.cloud import storage
from minio import Minio
from sklearn.model_selection import train_test_split
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *
from utils.common_functions import read_yaml

logger = get_logger(__name__)

class DataIngestion:
    def __init__(self,config):
        self.config = config["data_ingestion"]
        self.bucket_name = self.config["bucket_name"]
        self.file_name = self.config["bucket_file_name"]
        self.train_test_ratio = self.config["train_ratio"]
        self.storage_provider = self.config.get("storage_provider", "gcp").lower()
        self.minio_endpoint = self.config.get("minio_endpoint")
        self.minio_access_key = self.config.get("minio_access_key")
        self.minio_secret_key = self.config.get("minio_secret_key")
        self.minio_secure = self.config.get("minio_secure", False)

        os.makedirs(RAW_DIR , exist_ok=True)

        logger.info(f"Data Ingestion started with {self.bucket_name} and file is  {self.file_name}")

    def download_csv_from_gcp(self):
        try:
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(self.file_name)

            blob.download_to_filename(RAW_FILE_PATH)

            logger.info(f"CSV file is sucesfully downloaded to {RAW_FILE_PATH}")

        except Exception as e:
            logger.error("Error while downloading the csv file from GCP")
            raise CustomException("Failed to downlaod csv file from GCP", e)

    def download_csv_from_minio(self):
        try:
            client = Minio(
                self.minio_endpoint,
                access_key=self.minio_access_key,
                secret_key=self.minio_secret_key,
                secure=self.minio_secure,
            )
            client.fget_object(self.bucket_name, self.file_name, RAW_FILE_PATH)
            logger.info(f"CSV file is sucesfully downloaded to {RAW_FILE_PATH} from Minio")

        except Exception as e:
            logger.error("Error while downloading the csv file from Minio")
            raise CustomException("Failed to downlaod csv file from Minio", e)
        
    def split_data(self):
        try:
            logger.info("Starting the splitting process")
            data = pd.read_csv(RAW_FILE_PATH)
            train_data , test_data = train_test_split(data , test_size=1-self.train_test_ratio , random_state=42)

            train_data.to_csv(TRAIN_FILE_PATH)
            test_data.to_csv(TEST_FILE_PATH)

            logger.info(f"Train data saved to {TRAIN_FILE_PATH}")
            logger.info(f"Test data saved to {TEST_FILE_PATH}")
        
        except Exception as e:
            logger.error("Error while splitting data")
            raise CustomException("Failed to split data into training and test sets ", e)
        
    def run(self):

        try:
            logger.info("Starting data ingestion process")

            if self.storage_provider == "minio":
                self.download_csv_from_minio()
            else:
                self.download_csv_from_gcp()
            self.split_data()

            logger.info("Data ingestion completed sucesfully")
        
        except CustomException as ce:
            logger.error(f"CustomException : {str(ce)}")
        
        finally:
            logger.info("Data ingestion completed")

if __name__ == "__main__":
    data_ingestion = DataIngestion(read_yaml(CONFIG_PATH))
    data_ingestion.run()




        

