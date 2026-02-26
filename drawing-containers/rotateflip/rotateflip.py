'''
AWS version
- downloads and uploads to S3

Input a folder of subfolders.
Each subfolder has all the tiles for one page.
Tiles are rotated and flipped to multiply tile count by 8.
'''
import boto3
import io
import os
from PIL import Image


def main(index):
	# file manage
	s3 = boto3.client('s3')
	bucket = os.environ['BUCKET']
	key_prefix = os.environ['KEY_PREFIX']
	key_prefix = f'{key_prefix}/p{index}'
	tile_metadata = s3.list_objects_v2(Bucket=bucket, Prefix=key_prefix)['Contents']

	# source tile
	for i in range(len(tile_metadata)):
		key_in = tile_metadata[i]['Key']
		response = s3.get_object(Bucket=bucket, Key=key_in)
		img = Image.open(io.BytesIO(response['Body'].read()))

		# rotate and flip
		for f in range(2):
			for r in range(4):
				img = img.rotate(90)
				key_out = key_in.replace('rf00', f'rf{f}{r}')
				buf = io.BytesIO()
				img.save(buf, format='png')
				buf.seek(0)
				try:
					s3.put_object(Bucket=bucket, Key=key_out, Body=buf)
				except Exception as e:
					print(e)
			img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)

	print(f'{index}: tiles rotated, flipped, and uploaded.')


if __name__ == '__main__':
	#index = '00' # local test
	index = os.environ['AWS_BATCH_JOB_ARRAY_INDEX'].zfill(2)
	main(index)















