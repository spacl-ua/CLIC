import sys
import logging
import urllib.request
import urllib.error
import json


def get_logger(debug=False, warn=True, stdout=sys.stdout, stderr=sys.stderr):
	"""
	Creates a logger which sends some messages to stdout and some messagese to stderr.

	Parameters
	----------
	debug : bool
		If True, print debug messages.

	warn : bool
		If False, ignore warning messages.

	Returns
	-------
	logging.Logger
		AnGinstance of a logger
	"""

	logger = logging.Logger(__name__ + '.get_logger.{0}_{1}'.format(debug, warn))
	logger.setLevel(logging.DEBUG if debug else logging.INFO)

	# clear handlers
	logger.handlers = []

	formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

	# debug and info messages
	handler = logging.StreamHandler(stdout)
	handler.setFormatter(formatter)
	handler.setLevel(logging.DEBUG)
	handler.addFilter(lambda record: record.levelno <= logging.INFO)
	logger.addHandler(handler)

	# error and warning messages
	handler = logging.StreamHandler(stderr)
	handler.setFormatter(formatter)
	handler.setLevel(logging.WARNING if warn else logging.ERROR)
	logger.addHandler(handler)

	return logger


class APIClient(object):
	"""
	Communicates with the webserver to update 
	"""

	def __init__(self, host, token, pk):
		self.host = host
		self.token = token
		self.pk = pk


	@staticmethod
	def _urljoin(*args):
		return '/'.join(str(s).strip('/') for s in args) + '/'


	def _post(self, kind, data):
		data = json.dumps({kind: data})
		data = data.encode('utf-8')

		url = self._urljoin(self.host, 'api', self.pk, kind)

		request = urllib.request.Request(url)
		request.add_header('Auth-Token', self.token)
		request.add_header('Content-Type', 'application/json')
		request.add_header('Content-Length', len(data))

		try:
			response = urllib.request.urlopen(request, data)
		except urllib.error.HTTPError as error:
			return error.code
		except ConnectionError:
			return 503

		return response.status


	def post_status(self, status):
		return self._post('status', status)


	def post_metrics(self, metrics):
		return self._post('metrics', metrics)


	def post_decoding_time(self, decoding_time):
		return self._post('decoding_time', decoding_time)
