from abc import ABC, abstractmethod
import os
import boto3
from botocore.exceptions import NoCredentialsError


class Storage(ABC):
    @abstractmethod
    def save(self, file_name: str, data: bytes):
        pass


class LocalStorage(Storage):
    def __init__(self, base_path: str = "./storage"):
        self.base_path = base_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)

    def save(self, file_name: str, data: bytes):
        file_path = os.path.join(self.base_path, file_name)
        with open(file_path, "wb") as f:
            f.write(data)
        print(f"File saved locally at {file_path}")


class MinIOStorage(Storage):
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str):
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self.bucket_name = bucket_name


        try:
            self.client.head_bucket(Bucket=bucket_name)
        except Exception:
            self.client.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' created.")

    def save(self, file_name: str, data: bytes):
        try:
            self.client.put_object(Bucket=self.bucket_name, Key=file_name, Body=data)
            print(f"File saved in MinIO bucket '{self.bucket_name}' with key '{file_name}'")
        except NoCredentialsError as e:
            print("Credentials error:", e)


def save_file(storage: Storage, file_name: str, data: bytes):
    storage.save(file_name, data)
