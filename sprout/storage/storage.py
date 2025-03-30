
from minio import Minio
from minio.error import S3Error
import io
from minio import Minio
from typing import Any, Union, BinaryIO
from sprout.config import Config

class MinIOModelStorage:
    def __init__(self):
        self.client = client = Minio(Config.MINIO_URI,
        access_key=Config.MINIO_ACCESS_KEY,
        secret_key=Config.MINIO_SECRET_KEY,
        secure=False,
        )
        self.bucket_name = "sprout"
    
    def upload_model(
        self, 
        model_buffer: Union[io.BytesIO, BinaryIO], 
        bucket_name: str, 
        object_name: str
    ) -> None:
        """
        Uploads the model buffer to MinIO
        
        Parameters:
        - model_buffer: binary buffer of the model
        - bucket_name: target bucket name
        - object_name: object name (file name)
        """
        try:
            # If the buffer pointer is not at the beginning, reset to the beginning
            if hasattr(model_buffer, 'seek'):
                model_buffer.seek(0)
            
            # Ensure the bucket exists
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            # Get the buffer length
            if hasattr(model_buffer, 'getbuffer'):
                length = model_buffer.getbuffer().nbytes
            elif hasattr(model_buffer, 'tell'):
                current_pos = model_buffer.tell()
                model_buffer.seek(0, 2)  # Move to the end
                length = model_buffer.tell()
                model_buffer.seek(current_pos)  # Restore original position
            else:
                raise ValueError("Unable to determine model buffer length")
            
            # Upload the model
            self.client.put_object(
                bucket_name, 
                object_name, 
                model_buffer, 
                length=length
            )
            
            print(f"Model successfully uploaded to {bucket_name}/{object_name}")
        
        except Exception as e:
            print(f"Error occurred while uploading the model: {e}")
            raise

    def download_model(
        self, 
        bucket_name: str, 
        object_name: str
    ) -> io.BytesIO:
        """
        Downloads the model from MinIO
        
        Parameters:
        - bucket_name: bucket name
        - object_name: object name (file name)
        
        Returns:
        - model in binary buffer
        """
        try:
            # Get the object
            model_data = self.client.get_object(bucket_name, object_name)
            
            # Read the data into an in-memory buffer
            model_buffer = io.BytesIO(model_data.read())
            
            # Close the original data stream
            model_data.close()
            
            # Reset the buffer pointer to the beginning
            model_buffer.seek(0)
            
            return model_buffer
        
        except Exception as e:
            print(f"Error occurred while downloading the model: {e}")
            raise

def save_file(storage: MinIOModelStorage, file_name: str):
    storage = MinIOModelStorage
    with open(file_name, "rb") as file:
            file_bytes = file.read()
    storage.upload_model(file_bytes)

