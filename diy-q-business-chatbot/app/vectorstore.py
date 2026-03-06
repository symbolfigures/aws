import boto3
from concurrent.futures import ProcessPoolExecutor
import faiss
import json
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
import os
import sys

# inference client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime'
)

# embedding model
embeddings = BedrockEmbeddings(
    model_id='amazon.titan-embed-text-v2:0',
    client=bedrock_runtime
)


def initialize_vectorstore():
	sample = embeddings.embed_query('this is a text')
	index = faiss.IndexFlatL2(len(sample))
	vecs = FAISS(
		embedding_function=embeddings,
		index=index,
		docstore=InMemoryDocstore(),
		index_to_docstore_id={}
	)
	return vecs


def build_vectorstore(
	vectors,
    chunk_size=512,
    chunk_overlap=64):

	dir_pdf = f'data/pdf'
	metadata_path = f'data/metadata.json'
	with open(metadata_path, 'r') as f:
		metadata = json.load(f)

	splitter = RecursiveCharacterTextSplitter(
	    chunk_size=chunk_size,
	    chunk_overlap=chunk_overlap
	)
	for entry in metadata:
		pdf_path = f'{dir_pdf}/{entry['filename']}'
		loader = PyPDFLoader(pdf_path)
		pdf_data = loader.load()
		chunks = splitter.split_documents(pdf_data)

		for chunk in chunks:
			chunk.metadata = {
				'guid': entry['guid'],
				'filename': entry['filename'],
				'title': entry['title'],
				'url': entry['url'],				
			}
		vectors.add_documents(chunks)


def save_vectorstore(vectors):
	dir_out = f'data/vectors'
	os.makedirs(dir_out, exist_ok=True)
	vectors.save_local(dir_out)


def main():
	vectors = initialize_vectorstore()
	build_vectorstore(vectors)
	save_vectorstore(vectors)


if __name__ == '__main__':
	main()


















