#!/usr/bin/env python3

import os
import sys
import traceback
from argparse import ArgumentParser
from glob import glob
from subprocess import run
from utils import get_logger
from PIL import Image
from metrics import evaluate


def main(args):
	logger = get_logger(debug=args.debug)

	# mount submission
	logger.info('Obtaining decoded images')
	submission_dir = '/submission'
	run('mkdir -p {dir}'.format(dir=submission_dir), shell=True)
	run('gcsfuse --implicit-dirs --file-mode 777 --only-dir {subdir} {bucket} {dir} > /dev/null'.format(
			subdir=args.submission_path,
			bucket=args.submission_bucket,
			dir=submission_dir),
		shell=True)

	# mount target images
	logger.info('Obtaining target images')
	target_dir = '/target'
	run('mkdir -p {dir}'.format(dir=target_dir), shell=True)
	run('gcsfuse --implicit-dirs --file-mode 777 --only-dir {subdir} {bucket} {dir} > /dev/null'.format(
			subdir=os.path.join(args.task, args.phase),
			bucket=args.target_bucket,
			dir=target_dir),
		shell=True)

	try:
		target_images = glob(os.path.join(target_dir, '*.png'))
		target_images = {os.path.basename(path): path for path in target_images}
		submission_images = glob(os.path.join(submission_dir, '**/*.png'), recursive=True)
		submission_images = {os.path.basename(path): path for path in submission_images}

		for name in target_images:
			# check if image is present
			if name not in submission_images:
				logger.error('submission is missing image: {}'.format(name))
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
				return 1

		logger.info('Running evaluation')
		results = evaluate(submission_images, target_images, metrics=args.metrics)

		print(results)

	except:
		logger.error('Some unexpected error occured')
		logger.debug(traceback.format_exc())

	finally:
		# unmount buckets
		run('fusermount -u {dir}'.format(dir=submission_dir), shell=True)
		run('fusermount -u {dir}'.format(dir=target_dir), shell=True)

	return 0


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('--submission_bucket', type=str, required=True,
		help='Name of the bucket which contains submissions')
	parser.add_argument('--submission_path', type=str, required=True,
		help='Path to where submission is stored')
	parser.add_argument('--target_bucket', type=str, required=True,
		help='Name of the bucket which contains target files')
	parser.add_argument('--task', type=str, required=True)
	parser.add_argument('--phase', type=str, required=True)
	parser.add_argument('--team', type=str, required=True)
	parser.add_argument('--debug', action='store_true')
	parser.add_argument('--metrics', type=str, nargs='+', default=['PSNR', 'MSSSIM'],
		choices=['PSNR', 'MSSSIM'])

	args = parser.parse_args()

	sys.exit(main(args))
