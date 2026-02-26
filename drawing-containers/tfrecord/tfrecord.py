# TODO: Convert original version to S3, which splits datasets into multiple tfrecords.
'''
AWS version
- downloads and uploads to S3
'''
import boto3
import io
import numpy as np
import os
from PIL import Image
import tensorflow as tf


def sample(image_string, image_shape):
	feature = {
		'image_bytes': tf.train.Feature(bytes_list=tf.train.BytesList(value=[image_string])),
		'image_shape': tf.train.Feature(int64_list=tf.train.Int64List(value=image_shape)),
	}
	return tf.train.Example(features=tf.train.Features(feature=feature))


def make_record(bucket, keys, filepath, s3):
	# save tfrecord locally before upload
	writer = tf.io.TFRecordWriter(filepath)

	# images are added to the tfrecord one at a time
	for key in keys:
		response = s3.get_object(Bucket=bucket, Key=key)
		img = Image.open(io.BytesIO(response['Body'].read()))
		mode = img.mode
		img = np.array(img)
		# for pixels with 3-4 channels (RGB or RGBA) the array has shape (3-4, X)
		img_shape = img.shape
		img_tensor = tf.convert_to_tensor(img, dtype=tf.uint8)
		img_string = tf.io.encode_png(img_tensor).numpy()

		tf_example = sample(img_string, img_shape)
		writer.write(tf_example.SerializeToString())

	writer.close()


def main():
	# list the s3 objects
	s3 = boto3.client('s3')
	bucket = os.environ['BUCKET']
	key_in_prefix = os.environ['KEY_IN_PREFIX']
	keys = []
	# use a paginator for 1000+ objects
	pager = s3.get_paginator('list_objects_v2')
	for page in pager.paginate(Bucket=bucket, Prefix=key_in_prefix):
		contents = page.get('Contents', [])
		for obj in contents:
			key = obj['Key']
			if 'grid' not in key:
				keys.append(key)
	# make record, save to disk
	filepath = 'shard_0.tfrecord'
	make_record(bucket, keys, filepath, s3)
	# upload
	key_out_prefix = os.environ['KEY_OUT_PREFIX']
	key_out = f'{key_out_prefix}/{filepath}'
	try:
		s3.upload_file(filepath, bucket, key_out)
	except Exception as e:
		print(e)
	print('tfrecord created and uploaded')


if __name__ == '__main__':
	main()














