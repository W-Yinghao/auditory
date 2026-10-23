"""VLAAI TensorFlow reference outputs for the PyTorch port check (runs in the 'EEG' conda env: Python 3.7, TF 2.4.1, CPU).

Standalone: python -I vlaai_tf_reference.py --repo <pinned vlaai checkout> --out <npz>
Loads the released pretrained_models/vlaai.h5 twice -- (a) tf.keras.models.load_model with the repo's pearson_loss /
pearson_metric, (b) the repo's model.vlaai() + load_weights -- asserts identical outputs, and writes the fixed input
(numpy default_rng(3401), [2, 320, 64] float32), the final output and the per-block taps (extractor / dense /
output_context outputs of each of the 4 blocks) of model (a).  The repo's model.py was read before use; nothing else
from the checkout is imported or executed.
"""
import argparse
import importlib.util
import json
import os

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--repo', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
import tensorflow as tf  # noqa: E402

spec = importlib.util.spec_from_file_location('vlaai_model', os.path.join(a.repo, 'model.py'))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
h5 = os.path.join(a.repo, 'pretrained_models', 'vlaai.h5')
full = tf.keras.models.load_model(h5, custom_objects={'pearson_loss': M.pearson_loss, 'pearson_metric': M.pearson_metric})
fresh = M.vlaai()
fresh.load_weights(h5)
x = np.random.default_rng(3401).standard_normal((2, 320, 64)).astype(np.float32)
y_full = full.predict(x, batch_size=2)
y_fresh = fresh.predict(x, batch_size=2)
assert np.array_equal(y_full, y_fresh), float(np.abs(y_full - y_fresh).max())
names = [l.name for l in full.layers]
ext, ctx = full.get_layer('functional_9'), full.get_layer('functional_7')
dense = ['dense', 'dense_1', 'dense_2', 'dense_3']
outs, keys = [], []
for i in range(4):
    outs += [ext.get_output_at(i), full.get_layer(dense[i]).output, ctx.get_output_at(i)]
    keys += [f'extractor_{i}', f'dense_{i}', f'output_context_{i}']
probe = tf.keras.Model(inputs=full.inputs, outputs=outs)
vals = probe.predict(x, batch_size=2)
meta = {'tf_version': tf.__version__, 'keras_version': tf.keras.__version__, 'layers': names,
        'n_params': int(full.count_params()), 'load_model_equals_load_weights': True}
np.savez(a.out, input=x, output=y_full, meta=json.dumps(meta), **dict(zip(keys, vals)))
print(json.dumps(meta))
