# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from google.cloud import vision
from google.cloud.vision import types

import os.path
import re
import sys
import tarfile
import io
import urllib
import socket
import cv2
import numpy
import tensorflow as tf
import time

HOST = ""
PORT = 1107

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string(
	'model_dir', '/tmp/imagenet',
	"""Path to classify_image_graph_def.pb, """
	"""imagenet_synset_to_human_label_map.txt, and """
	"""imagenet_2012_challenge_label_map_proto.pbtxt.""")
tf.app.flags.DEFINE_string(
	'image_file', '',
	"""Absolute path to image file.""")
tf.app.flags.DEFINE_integer(
	'num_top_predictions', 5,
	"""Display this many predictions.""")
DATA_URL = "http://download.tensorflow.org/models/image/imagenet/inception-2015-12-05.tgz"

class NodeLookup(object):
	def __init__(self, label_lookup_path=None, uid_lookup_path=None):
		if not label_lookup_path:
			label_lookup_path = os.path.join(FLAGS.model_dir,
				'imagenet_2012_challenge_label_map_proto.pbtxt')
		if not uid_lookup_path:
			uid_lookup_path = os.path.join(FLAGS.model_dir,
				'imagenet_synset_to_human_label_map.txt')
		self.node_lookup = self.load(label_lookup_path, uid_lookup_path)
	
	def load(self, label_lookup_path, uid_lookup_path):
		if not tf.gfile.Exists(uid_lookup_path):
			tf.logging.fatal('File does not exist %s', uid_lookup_path)
		if not tf.gfile.Exists(label_lookup_path):
			tf.logging.fatal('File does not exist %s', label_lookup_path)
		proto_as_ascii_lines = tf.gfile.GFile(uid_lookup_path).readlines()
		uid_to_human = {}
		p = re.compile(r'[n\d]*[ \S,]*')
		for line in proto_as_ascii_lines:
			parsed_items = p.findall(line)
			uid = parsed_items[0]
			human_string = parsed_items[2]
			uid_to_human[uid] = human_string
		node_id_to_uid = {}
		proto_as_ascii = tf.gfile.GFile(label_lookup_path).readlines()
		for line in proto_as_ascii:
			if line.startswith('  target_class:'):
				target_class = int(line.split(': ')[1])
			if line.startswith('  target_class_string:'):
				target_class_string = line.split(': ')[1]
				node_id_to_uid[target_class] = target_class_string[1:-2]
		node_id_to_name = {}
		for key, val in node_id_to_uid.items():
			if val not in uid_to_human:
				tf.logging.fatal('Failed to locate: %s', val)
			name = uid_to_human[val]
			node_id_to_name[key] = name
		return node_id_to_name
	
	def id_to_string(self, node_id):
		if node_id not in self.node_lookup:
			return ''
		return self.node_lookup[node_id]

def create_graph():
	with tf.gfile.FastGFile(os.path.join(FLAGS.model_dir, 'classify_image_graph_def.pb'), 'rb') as f:
		graph_def = tf.GraphDef()
		graph_def.ParseFromString(f.read())
		_ = tf.import_graph_def(graph_def, name='')

def run_inference_on_image(image):
	if not tf.gfile.Exists(image):
		tf.logging.fatal('File does not exist %s', image)
	image_data = tf.gfile.FastGFile(image, 'rb').read()
	create_graph()
	with tf.Session() as sess:
		softmax_tensor = sess.graph.get_tensor_by_name('softmax:0')
		predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
		predictions = numpy.squeeze(predictions)
		node_lookup = NodeLookup()
		top_k = predictions.argsort()[-FLAGS.num_top_predictions:][::-1]
		for node_id in top_k:
			human_string = node_lookup.id_to_string(node_id)
			score = predictions[node_id]
			return human_string, score

def maybe_download_and_extract():
	dest_directory = FLAGS.model_dir
	if not os.path.exists(dest_directory):
		os.makedirs(dest_directory)
	filename = DATA_URL.split('/')[-1]
	filepath = os.path.join(dest_directory, filename)
	if not os.path.exists(filepath):
		def _progress(count, block_size, total_size):
			sys.stdout.write('\r>> Downloading %s %.1f%%' % (filename, float(count * block_size) / float(total_size) * 100.0))
			sys.stdout.flush()
		filepath, _ = urllib.request.urlretrieve(DATA_URL, filepath, _progress)
		print()
		statinfo = os.stat(filepath)
		print('Succesfully downloaded', filename, statinfo.st_size)
	tarfile.open(filepath, 'r:gz').extractall(dest_directory)



def rec_val(socket, count):
	buf = b''
	while count:
		newbuf = socket.recv(count)
		if not newbuf: return None
		buf += newbuf
		count -= len(newbuf)
	return buf

def rec_image(socket):
	length = rec_val(socket, 16)
	string_data = rec_val(socket, int(length))
	data = numpy.fromstring(string_data, dtype='uint8')

	img_decode = cv2.imdecode(data, 1)
	cv2.imwrite('/tmp/imagenet/input.jpg', img_decode)

def to_one_word(words):
	length = len(words)
	word = ""
	for i in range(length):
		if words[i] == ',':
			word = words[:i]
			return word
	return words

def main(argv=None):
	maybe_download_and_extract()

	client = vision.ImageAnnotatorClient()

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((HOST, PORT))
	s.listen(1)
	conn, addr = s.accept()

	while True:
		flag = conn.recv(10).decode()
		rec_image(conn)
		if (str(flag) == 'object'):
			print("--------------object detection-------------------")
			image = (FLAGS.image_file if FLAGS.image_file else os.path.join(FLAGS.model_dir, "input.jpg"))
			result_string, result_score = run_inference_on_image(image)
			print(result_string, result_score)
			result = to_one_word(result_string)
			conn.send(result.encode())
		elif (str(flag) == 'text'):
			print("--------------text detection---------------------")
			file_name = os.path.join(os.path.dirname(__file__), '/tmp/imagenet/input.jpg')
			with io.open(file_name, 'rb') as image_file:
				content = image_file.read()
			image = types.Image(content=content)
			response = client.text_detection(image=image)
			texts = response.text_annotations
			try:
				text = str(texts[0].description)
			except:
				text = "글이 없습니다."
			conn.send(text.encode())
	
	conn.close()
	s.close()


if __name__ == '__main__':
	tf.app.run()
