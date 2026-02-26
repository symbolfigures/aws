import boto3
import functools
import io
from models import create_discriminator, create_generator
import os
import pickle
from serialize import deserialize_model, serialize_model
import tensorflow as tf
from tensor_ops import lerp
from training_loop import training_loop

s3 = boto3.client('s3')


def decode_record_image(record_bytes):
    schema = {
        'image_shape': tf.io.FixedLenFeature([3], dtype=tf.int64),
        'image_bytes': tf.io.FixedLenFeature([], dtype=tf.string)
        }
    example = tf.io.parse_single_example(record_bytes, schema)
    image = tf.io.decode_image(example['image_bytes'])
    image = tf.reshape(image, tf.cast(example['image_shape'], tf.int32))
    return image


def make_real_image_dataset(
        batch_size: int,
        file_pattern: str,
        ) -> tf.data.Dataset:
    file_names = tf.io.gfile.glob(file_pattern)

    return tf.data.TFRecordDataset(file_names
        ).map(decode_record_image
        ).map(lambda image: tf.image.convert_image_dtype(image, tf.float32, saturate=True)
        ).shuffle(1000
        ).repeat(
        ).batch(batch_size
        ).prefetch(tf.data.AUTOTUNE)


class TrainingOptions:
	def __init__(
			self,
			dataset_file_pattern: str,
			resolution: int,
			replica_batch_size: int,
			epoch_sample_count: int = 1024 * 16,
			total_sample_count: int = 1024 * 16 * 32,
			learning_rate: float = 0.002,
			latent_size = 64,
			beta_1 = None,
			beta_2 = None
			):
		assert epoch_sample_count % replica_batch_size == 0
		assert total_sample_count % epoch_sample_count == 0

		self.dataset_file_pattern = dataset_file_pattern
		self.resolution = resolution
		self.replica_batch_size = replica_batch_size
		self.epoch_sample_count = epoch_sample_count
		self.total_sample_count = total_sample_count
		self.learning_rate = learning_rate
		self.latent_size = latent_size
		self.beta_1 = beta_1
		self.beta_2 = beta_2

	@property
	def epoch_count(self):
		return self.total_sample_count // self.epoch_sample_count


class TrainingState:
	def __init__(
			self,
			options: TrainingOptions,
			epoch_i: int = 0,
			generator: tf.keras.Model = None,
			discriminator: tf.keras.Model = None):
		self.options = options
		self.epoch_i = epoch_i
		self.generator = generator
		self.discriminator = discriminator

	def training_is_done(self) -> bool:
		return self.epoch_i * self.options.epoch_sample_count >= self.options.total_sample_count

	def __getstate__(self):
		state = self.__dict__.copy()
		state['generator'] = serialize_model(self.generator)
		state['discriminator'] = serialize_model(self.discriminator)
		return state

	def __setstate__(self, state):
		self.__dict__ = state.copy()
		self.generator = deserialize_model(
			self.generator,
			functools.partial(create_generator, self.options.resolution, self.options.latent_size))
		self.discriminator = deserialize_model(
			self.discriminator,
			functools.partial(create_discriminator, self.options.resolution))


class CheckpointStateCallback(tf.keras.callbacks.Callback):
	def __init__(
			self,
			state: TrainingState,
			bucket: str,
			key_out_prefix: str):
		self.state = state
		self.bucket = bucket
		self.key_out_prefix = key_out_prefix
		super().__init__()

	def on_epoch_end(self, epoch_i: int, logs=None) -> None:
		self.state.epoch_i = epoch_i + 1
		key_out = f'{self.key_out_prefix}/{self.state.epoch_i}.checkpoint'
		buf = io.BytesIO()
		pickle.dump(self.state, buf)
		buf.seek(0)
		try:
			s3.put_object(Bucket=self.bucket, Key=key_out, Body=buf.getvalue())
		except Exception as e:
			print(e)


def train(
		strategy: tf.distribute.MirroredStrategy,
		bucket: str,
		key_out_prefix: str,
		state: TrainingState
		) -> None:
	options = state.options

	checkpoint_callback = CheckpointStateCallback(state, bucket, key_out_prefix)

	if state.generator is None:
		global_batch_size = options.replica_batch_size * strategy.num_replicas_in_sync
		with strategy.scope():
			state.generator = create_generator(options.resolution, options.latent_size)
			state.discriminator = create_discriminator(options.resolution)

	global_batch_size = options.replica_batch_size * strategy.num_replicas_in_sync

	image_dataset = strategy.experimental_distribute_dataset(
		make_real_image_dataset(
			global_batch_size,
			file_pattern=options.dataset_file_pattern))

	state.epoch_i = training_loop(
		checkpoint_callback,
		strategy,
		state.generator,
		state.discriminator,
		image_dataset,
		state.epoch_i,
		options.epoch_count,
		options.replica_batch_size,
		options.epoch_sample_count,
		learning_rate=options.learning_rate,
		beta_1=options.beta_1,
		beta_2=options.beta_2)













