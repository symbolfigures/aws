'''
AWS version
S3 file handling
- tfrecords
- checkpoints
- options.json
option dataset_file_pattern is replaced with the constant ./tfrecord/*.tfrecord
instead the S3 location is the environment variable KEY_IN_PREFIX
and the dataset is invariably downloaded to ./tfrecord/*.tfrecord

Initiate or resume training.
Output folder must contain an options.json file that has all the hyperparameters
as seen in TrainingOptions.
Automatically resumes from latest checkpoint in the output folder.
'''
import boto3
import io
import json
import os
import pickle
import tensorflow as tf
import time
from train import TrainingOptions, TrainingState, train
from typing import List, Optional

bucket = os.environ['BUCKET']
key_in_prefix = os.environ['KEY_IN_PREFIX']
key_out_prefix = os.environ['KEY_OUT_PREFIX']
s3 = boto3.client('s3')


def init_training():
	print('initializaing...')

	# download options.json from S3
	key = f'{key_out_prefix}/options.json'
	response = s3.get_object(Bucket=bucket, Key=key)
	bytes = io.BytesIO(response['Body'].read())
	opt = json.load(bytes)
	print('options loaded...')

	options = TrainingOptions(
		'tfrecord/*.tfrecord',
		opt['resolution'],
		opt['replica_batch_size'],
		opt['epoch_sample_count'],
		opt['total_sample_count'],
		opt['learning_rate'],
		opt['latent_size'],
		opt['beta_1'],
		opt['beta_2'])

	strategy = tf.distribute.MirroredStrategy()

	training_state = TrainingState(options)

	train(
		strategy,
		bucket,
		key_out_prefix,
		training_state)


def resume_training(checkpoint_i):
	strategy = tf.distribute.MirroredStrategy()

	with strategy.scope():
		key = f'{key_out_prefix}/{checkpoint_i}.checkpoint'
		response = s3.get_object(Bucket=bucket, Key=key)
		buf = io.BytesIO(response['Body'].read())
		buf.seek(0)
		state = pickle.load(buf)
		print(f'resuming from epoch {state.epoch_i}...')

		training_state = TrainingState(
			state.options,
			state.epoch_i,
			state.generator,
			state.discriminator)

	train(
		strategy,
		bucket,
		key_out_prefix,
		training_state)


def main():
	# save dataset to disk
	keys = []
	metadata = s3.list_objects_v2(Bucket=bucket, Prefix=key_in_prefix)['Contents']
	for k in range(len(metadata)):
		keys.append(metadata[k]['Key'])
	os.makedirs('tfrecord', exist_ok=True)
	for key in keys:
		filename = key.split('/')[-1]
		s3.download_file(bucket, key, f'tfrecord/{filename}')
	print('saved dataset to disk...')

	# look for checkpoints
	metadata = s3.list_objects_v2(Bucket=bucket, Prefix=key_out_prefix)['Contents']
	checkpoints = []
	for k in range(len(metadata)):
		key = metadata[k]['Key']
		if key.endswith('checkpoint'):
			key = key.split('/')[-1]
			checkpoints.append(key)

	# init or resume
	if not checkpoints:
		print('no checkpoint found...')
		init_training()
	else:
		print('checkpoint found...')
		checkpoint_i = max([int(c.split('.')[0]) for c in checkpoints])
		resume_training(checkpoint_i)


if __name__ == '__main__':
	main()













