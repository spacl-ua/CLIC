#!/usr/bin/env python3

import os
import sys
import traceback
import numpy as np
from argparse import ArgumentParser
from glob import glob
from subprocess import run
from utils import get_logger, sql_setup
from PIL import Image
from metrics import evaluate


def main(args):
	logger = get_logger(debug=args.debug)

	try:
		logger.debug('Connecting to SQL database')
		sql_setup()
	except:
		logger.error('Unable to connect to SQL database')
		logger.debug(traceback.format_exc())
		sys.exit(1)

	try:
		# sql_setup needs to be called before importing anything from Django
		from models import Submission, Measurement
		from django.core.exceptions import ObjectDoesNotExist
		from django.db import transaction

		logger.info('Obtaining submission')
		submission = Submission.objects.get(id=args.id)
		submission.status = Submission.STATUS_EVALUATING
		submission.save()
	except ObjectDoesNotExist:
		logger.error('Could not find submission')
		return 1
	except:
		logger.error('Some unexpected error occured')
		logger.debug(traceback.format_exc())
		return 1

	# mount submission
	logger.info('Obtaining decoded images')
	submission_dir = '/submission'
	run('mkdir -p {dir}'.format(dir=submission_dir), shell=True)
	run('gcsfuse --implicit-dirs --file-mode 777 --only-dir {subdir} {bucket} {dir} > /dev/null'.format(
			subdir=submission.fs_path(),
			bucket=os.environ['BUCKET_SUBMISSIONS'],
			dir=submission_dir),
		shell=True)

	# mount target images
	logger.info('Obtaining target images')
	target_dir = '/target'
	run('mkdir -p {dir}'.format(dir=target_dir), shell=True)
	run('gcsfuse --implicit-dirs --file-mode 777 --only-dir {subdir} {bucket} {dir} > /dev/null'.format(
			subdir=os.path.join(submission.task.name, submission.phase.name),
			bucket=os.environ['BUCKET_TARGETS'],
			dir=target_dir),
		shell=True)

	try:
		target_images = glob(os.path.join(target_dir, '*.png'))
		target_images = {os.path.basename(path): path for path in target_images}
		submission_images = glob(os.path.join(submission_dir, '**/*.png'), recursive=True)
		submission_images = {os.path.basename(path): path for path in submission_images}

		if not target_images:
			logger.error('Failed to locate target images')
			submission.status = Submission.STATUS_ERROR
			submission.save()
			return 1

		for name in target_images:
			# check if image is present
			if name not in submission_images:
				logger.error('Submission is missing image: {}'.format(name))
				submission.status = Submission.STATUS_EVALUATION_FAILED
				submission.save()
				return 1

			# check if image has correct size
			image_size = Image.open(submission_images[name]).size
			target_size = Image.open(target_images[name]).size

			if image_size != target_size:
				logger.error(
					'Image {name} has incorrect size ({image_size} instead of {target_size}).'.format(
						name=name,
						image_size='x'.join(image_size),
						target_size='x'.join(target_size)))
				submission.status = Submission.STATUS_EVALUATION_FAILED
				submission.save()
				return 1

		logger.info('Running evaluation')
		results = evaluate(submission_images, target_images, metrics=args.metrics)

		with transaction.atomic():
			for metric, value in results.items():
				logger.info(f'{metric}: {value}')

				measurement = Measurement(
					metric=metric,
					value=value,
					submission=submission)
				measurement.save()

		submission.status = Submission.STATUS_SUCCESS
		submission.save()

	except:
		logger.error('Some unexpected error occured')
		logger.debug(traceback.format_exc())
		submission.status = Submission.STATUS_ERROR
		submission.save()
		return 1

	finally:
		# unmount buckets
		run('fusermount -u {dir}'.format(dir=submission_dir), shell=True)
		run('fusermount -u {dir}'.format(dir=target_dir), shell=True)

	return 0


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('--id', type=int, required=True,
		help='Used to identify the submission')
	parser.add_argument('--debug', action='store_true')
	parser.add_argument('--metrics', type=str, nargs='+', default=['PSNR', 'MSSSIM'],
		choices=['PSNR', 'MSSSIM'])

	args = parser.parse_args()

	sys.exit(main(args))
