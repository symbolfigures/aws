import boto3
import os
import shutil


s3 = boto3.client('s3')
bucket = os.environ['BUCKET_APP']
key = 'vectors.zip'
dir = 'data'


def load_vectorstore():
	s3.download_file(bucket, key, key)
	shutil.unpack_archive(key, dir)


if __name__ == '__main__':
	load_vectorstore()
