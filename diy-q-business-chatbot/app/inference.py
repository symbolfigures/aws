import boto3
import json
from langchain_core.prompts import PromptTemplate
from langchain_aws import BedrockEmbeddings, BedrockLLM
from langchain_community.vectorstores import FAISS
import os
import re

bedrock_runtime_USE1 = boto3.client(
    service_name='bedrock-runtime',
	region_name='us-east-1'
)

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
	region_name='us-west-2' # ec2 instance doesn't default to us-west-2
)

qa_template = '''You answer questions with reference to provided documents. \
Document exerpts are provided below, ordered by relevance. \
Each exerpt ends with a tag beginning with '#'. \
For any exerpt you reference, include the tag with your answer. \
You can put them between sentences or at the end.

Example 1:
- Question: "What is a bitloop?"
- Answer: "A bitloop as a bit string whose ends are connected to form a loop. #0"

Example 2:
- Question: "What is a type?"
- Answer: "A type is a collection of qualities that characterize a thing. #1"

You may use markdown to format your answer.

Document exerpts:

{context}

Question:

{question}

Answer:'''


def call_novapro(payload):
	response = bedrock_runtime_USE1.invoke_model(
		modelId=payload['modelId'],
		contentType=payload['contentType'],
		accept=payload['accept'],
		body=json.dumps(payload['body'])
	)
	return response['body'].read().decode('utf-8')


def novapro_api_format(text: str) -> dict:
    return {
        'modelId': 'amazon.nova-pro-v1:0',
        'contentType': 'application/json',
        'accept': 'application/json',
        'body': {
            'inferenceConfig': {
                'max_new_tokens': 2048,
				'temperature': 0.3,
				'topP': 0.5
            },
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'text': text
                        }
                    ]
                }
            ]
        }
    }


def call_rerank(payload):
	response = bedrock_runtime.invoke_model(
		modelId=payload['modelId'],
		contentType=payload['contentType'],
		accept=payload['accept'],
		body=json.dumps(payload['body'])
	)
	return response['body'].read().decode('utf-8')


def rerank_api_format(query: str, documents: list[str]) -> dict:
    return {
		'modelId': 'amazon.rerank-v1:0',
		'contentType': 'application/json',
		'accept': '*/*',
		'body': {
			'query': query,
			'documents': documents,
			'top_n': 5
		}
	}


def retrieve_context_and_rerank(vectors, question):
	top_k = vectors.similarity_search(question, k=20)
	formatted = []
	for i in top_k:
		content = i.page_content
		guid = i.metadata['guid']
		formatted.append(f'{content} #{guid}')
	payload = rerank_api_format(question, formatted)
	response = json.loads(call_rerank(payload))
	indices = [response['results'][i]['index'] for i in range(len(response['results']))]
	context = ''
	for i in range(len(indices)):
		context = context + f'{formatted[i]}\n\n'
	return context


def format_footnotes(guid_strs):
	footnotes = []
	for i, gs in enumerate(guid_strs):
		guid = str(gs[1:])
		with open(f'data/metadata.json', 'r') as f:
			metadata = json.load(f)
		title = 'Title not found.'
		url = 'URL not found.'
		for entry in metadata:
			if entry['guid'] == guid:
				title = entry['title']
				url = entry['url']
		entry = {'n': i+1, 'title': title, 'url': url}
		footnotes.append(entry)
	return footnotes


def format_answer(s):
	guideq = r'#[A-Z0-9]+'
	# replace surrounding characters with spaces
	s = re.sub(r'\n+('+guideq+')', r' \1', s)
	s = re.sub(r'\W('+guideq+r')\W', r' \1 ', s)
	# get unique guids in the order that they appear
	guid_strs = re.findall(guideq, s)
	gs_unique = []
	for gs in guid_strs:
		if gs not in gs_unique:
			gs_unique.append(gs)
	# format footnotes
	footnotes = format_footnotes(gs_unique)
	# replace markers in the order that they appear
	for i, gs in enumerate(gs_unique):
		s = s.replace(gs, f'<sup>{i+1}</sup>')
	s = s + '  \n'
	# add footnotes at the bottom
	for f in range(len(footnotes)):
		n = footnotes[f]['n']
		title = footnotes[f]['title']
		url = footnotes[f]['url']
		s = s + f'  \n<sup>{n}</sup> [{title}]({url})'
	return s


def load_vectorstore():
	embeddings = BedrockEmbeddings(
		model_id='amazon.titan-embed-text-v2:0',
		client=bedrock_runtime
	)
	vectors = FAISS.load_local(
		f'data/vectors',
		embeddings,
		allow_dangerous_deserialization=True
	)
	return vectors


def infer(question):
	vectors = load_vectorstore()
	context = retrieve_context_and_rerank(vectors, question)

	prompt = qa_template.format(context=context, question=question)
	print(f'\nPrompt:\n{prompt}\n')

	payload = novapro_api_format(prompt)
	response = json.loads(call_novapro(payload))

	answer = response['output']['message']['content'][0]['text']
	print(f'\nAnswer:\n{answer}\n')

	return format_answer(answer)
















