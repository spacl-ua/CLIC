#!/usr/bin/env python3

import os
import numpy as np
import tensorflow as tf
from glob import glob
import time

tf.get_logger().setLevel('ERROR')

# load image
image_path_in = tf.placeholder(tf.string)
image = tf.io.read_file(image_path_in)
image = tf.image.decode_image(image)

filters = tf.zeros([1, 1, 3, 3])

image = tf.cast(image, 'float32')
image = tf.expand_dims(image, axis=0)
image = tf.nn.conv2d(image, filters, 1, padding='SAME')
image = tf.cast(image[0], 'uint8')

# save image
image_path_out = tf.placeholder(tf.string)
image = tf.image.encode_png(image)
write_op = tf.write_file(image_path_out, image)

with tf.Session() as sess:
	# initialize kernel
	sess.run(tf.global_variables_initializer())

	# simply load and save images
	for file_path_in in glob('**/*.jpg', recursive=True):
		print('Decoding {0}'.format(file_path_in))
		file_path_out = os.path.splitext(file_path_in)[0] + '.png'
		image = sess.run(write_op, feed_dict={
			image_path_in: file_path_in,
			image_path_out: file_path_out})
