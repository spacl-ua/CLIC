#!/usr/bin/env python3

import os
import sys
import traceback
import numpy as np
from argparse import ArgumentParser
from glob import glob
from subprocess import run, PIPE
from tempfile import mkdtemp
from utils import get_logger, get_submission, sql_setup
from PIL import Image
from metrics import evaluate


def main(args):
	log_file = os.path.join(mkdtemp(), '.log_evaluate')
	logger = get_logger(debug=args.debug, filename=log_file)

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
		submission = get_submission(id=args.id)
		submission.status = Submission.STATUS_EVALUATING
		submission.save()
	except ObjectDoesNotExist:
		logger.error('Could not find submission')
		return 1
	except:
		logger.error('Some unexpected error occured')
		logger.debug(traceback.format_exc())
		return 1

	# ativate service account (needed for gsutil)
	run('gcloud auth activate-service-account --quiet --key-file={key_file}'.format(
			key_file=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')),
		stdout=PIPE,
		stderr=PIPE,
		check=False,
		shell=True)

	# obtain submission
	logger.info('Obtaining decoded images')
	submission_dir = '/submission'
	run('mkdir -p {dir}'.format(dir=submission_dir), shell=True)
	run('gsutil -m rsync -e -R gs://{bucket}/{path}/ {submission_dir}'.format(
			bucket=os.environ['BUCKET_SUBMISSIONS'],
			path=submission.fs_path(),
			submission_dir=submission_dir),
		stdout=PIPE,
		stderr=PIPE,
		check=True,
		shell=True)

	# obtain target images
	logger.info('Obtaining target images')
	target_dir = '/target'
	run('mkdir -p {dir}'.format(dir=target_dir), shell=True)
	run('gsutil -m rsync -e -R gs://{bucket}/{path}/ {target_dir}'.format(
			bucket=os.environ['BUCKET_TARGETS'],
			path=os.path.join(submission.task.name, submission.phase.name),
			target_dir=target_dir),
		stdout=PIPE,
		stderr=PIPE,
		check=True,
		shell=True)

	try:
		# check images
		target_images = glob(os.path.join(target_dir, '*.png'))
		any_images = len(target_images) > 0
		target_images += glob(os.path.join(target_dir, '*.csv'))
		target_images = {os.path.basename(path): path for path in target_images}
		submission_images = glob(os.path.join(submission_dir, '**/*.png'), recursive=True)
		submission_images += glob(os.path.join(submission_dir, '**/*.csv'), recursive=True)
		submission_images = {os.path.basename(path): path for path in submission_images}

		if any_images:
			logger.info('Checking image dimensions')

		if not target_images:
			logger.error('Failed to locate target files')
			submission.status = Submission.STATUS_ERROR
			submission.save()
			return 1

		for name in target_images:
			# check if image is present
			if name not in submission_images:
				if name.endswith('.csv') and \
						len(submission_images) == 1 and \
						len(target_images) == 1:
					# hack so that CSV file can be named anything in perceptual track
					path = list(submission_images.values())[0]
					if path.lower().endswith('.csv'):
						submission_images[name] = path
						continue

				logger.error('Submission is missing file: {}'.format(name))
				submission.status = Submission.STATUS_EVALUATION_FAILED
				submission.save()
				return 1

			if name.endswith('.csv'):
				continue

			# check if image has correct size
			image_size = Image.open(submission_images[name]).size
			target_size = Image.open(target_images[name]).size

			if image_size != target_size:
				logger.error(
					'Image {name} has incorrect size ({image_size} instead of {target_size})'.format(
						name=name,
						image_size='x'.join(map(str, image_size)),
						target_size='x'.join(map(str, target_size))))
				submission.status = Submission.STATUS_EVALUATION_FAILED
				submission.save()
				return 1

		# start actual evaluation
		logger.info('Running evaluation')
		results = evaluate(
			submission_images,
			target_images,
			settings=submission.phase.settings,
			logger=logger)

		with transaction.atomic():
			for metric, value in results.items():
				logger.info(f'{metric}: {value}')

				if np.isnan(value):
					logger.warning(f'Evaluation of {metric} failed')
					continue

				measurement = Measurement(
					metric=metric,
					value=value,
					submission=submission)
				measurement.save()

		submission.status = Submission.STATUS_SUCCESS
		submission.save()

		logger.info('Evaluation complete')

	except:
		logger.error('Some unexpected error occured')
		logger.debug(traceback.format_exc())
		submission.status = Submission.STATUS_ERROR
		submission.save()
		return 1

	finally:
		# store logs
		run('gsutil cp {log_file} gs://{bucket}/{path}/'.format(
				log_file=log_file,
				bucket=os.environ['BUCKET_SUBMISSIONS'],
				path=submission.fs_path()),
			stdout=PIPE,
			stderr=PIPE,
			check=False,
			shell=True)
		run('rm {log_file}'.format(log_file=log_file), check=False, shell=True)

		# unmount buckets
		run('rm -rf {}'.format(submission_dir), shell=True)
		run('rm -rf {}'.format(target_dir), shell=True)

	return 0


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('--id', type=int, required=True,
		help='Used to identify the submission')
	parser.add_argument('--debug', action='store_true')

	args = parser.parse_args()

	sys.exit(main(args))
