from base64 import b64encode
import boto3
from datetime import datetime
from dotenv import load_dotenv
import json
import os

load_dotenv()

s3 = boto3.client(
	service_name='s3',
	region_name='us-west-2'
)

def log_interaction(id, prompt, answer, feedback):
	entry = {
		'id': id,
		'prompt': prompt,
		'answer': answer,
		'feedback': feedback
	}
	now = datetime.now()
	log_group = 'chatbot/interactions'
	bucketname = os.getenv('BUCKET_LOG')
	s3_key = (
		f'logs/{log_group}/'
		f'year={now.year:04d}/month={now.month:02d}/day={now.day:02d}/'
		f'{id}.json'
	)
	s3.put_object(
		Bucket=bucketname,
		Key=s3_key,
		Body=json.dumps(entry),
		ContentType='application/json'
	)


def encode_font(path):
	with open(path, 'rb') as f:
		data = f.read()
	return b64encode(data).decode('utf-8')


def font_css():
	fonts = {
		'normal': 'static/cmunrm.woff',
		'italic': 'static/cmunti.woff',
		'bold': 'static/cmunbx.woff',
		'bold_italic': 'static/cmunbi.woff'
	}
	encoded_fonts = {key: encode_font(path) for key, path in fonts.items()}
	font_css_style = f'''
		<style>
			@font-face {{
				font-family: 'ComputerModern';
				src: url('data:font/woff;base64,{encoded_fonts['normal']}') format('woff');
				font-weight: normal;
				font-style: normal;
			}}
			@font-face {{
				font-family: 'ComputerModern';
				src: url('data:font/woff;base64,{encoded_fonts['italic']}') format('woff');
				font-weight: normal;
				font-style: italic;
			}}
			@font-face {{
				font-family: 'ComputerModern';
				src: url('data:font/woff;base64,{encoded_fonts['bold']}') format('woff');
				font-weight: bold;
				font-style: normal;
			}}
			@font-face {{
				font-family: 'ComputerModern';
				src: url('data:font/woff;base64,{encoded_fonts['bold_italic']}') format('woff');
				font-weight: bold;
				font-style: italic;
			}}
		</style>
	'''
	return font_css_style







