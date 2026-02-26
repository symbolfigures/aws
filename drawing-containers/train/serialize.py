import io
import numpy as np
import pickle
import tensorflow as tf
from typing import Callable


def serialize_array(arr: np.ndarray) -> bytes:
    mem_file = io.BytesIO()
    np.save(mem_file, arr)
    mem_file.seek(0)
    return mem_file.read()


def deserialize_array(serialized: bytes) -> np.ndarray:
    mem_file = io.BytesIO()
    mem_file.write(serialized)
    mem_file.seek(0)
    return np.load(mem_file)


def serialize_model(model: tf.keras.Model) -> bytes:
    return pickle.dumps({
        'model_weights': list(map(serialize_array, model.get_weights()))
    })


def deserialize_model(serialized: bytes, create_model: Callable[[], tf.keras.Model]) -> tf.keras.Model:
    serializable = pickle.loads(serialized)
    model = create_model()
    model.set_weights(list(map(deserialize_array, serializable['model_weights'])))
    return model











