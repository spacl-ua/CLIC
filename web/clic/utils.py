import logging


def log_message(level, message, *args):
	"""
	Produces a string formatted like a log message.

	Parameters
	----------
	level : int
		Logging level

	message : str
		Message to be formatted

	Returns
	-------
	str
	"""

	formatter = logging.Formatter(
		'[%(asctime)s] %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	return formatter.format(logging.LogRecord("", level, "", 0, message + '\r\n', args, None))
