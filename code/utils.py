import sys
import logging


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
