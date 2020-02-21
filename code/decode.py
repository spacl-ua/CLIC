#!/usr/bin/env python3

"""
This script executes a submission by doing the following:

	1. Mount storage bucket containing the submission
	2. Copy submission to an executable directory on the host (/var/lib/docker)
	3. Run the decoder
	4. Copy files generated by decoder back to the storage bucket
"""

import os
import sys
import time
import traceback
from argparse import ArgumentParser
from subprocess import run, CalledProcessError, TimeoutExpired, PIPE, DEVNULL
from tempfile import mkdtemp
from utils import get_logger, get_submission, sql_setup
from zipfile import ZipFile

EXECUTABLE_NAME = 'decode'
ZIP_FILE_NAME = 'decoder.zip'

DECODE_CMD_CPU = [
	'docker', 'run',
	'--network', 'none',
	'--memory', '{memory_limit}m',
	'--memory-swap', '{memory_limit}m',
	'--cpus', '{num_cpus}',
	'--name', '{identifier}',
	'-v', '{work_dir}:/home/{identifier}',
	'-w', '/home/{identifier}',
	'-e', 'TF_CPP_MIN_LOG_LEVEL=3',
	'--entrypoint', './' + EXECUTABLE_NAME,
	'{image}']

DECODE_CMD_GPU = [
	'docker', 'run',
	'--network', 'none',
	'--memory', '{memory_limit}m',
	'--memory-swap', '{memory_limit}m',
	'--cpus', '{num_cpus}',
	'--name', '{identifier}',
	'-v', '{work_dir}:/home/{identifier}',
	'-v', '/home/kubernetes/bin/nvidia:/usr/local/nvidia:ro',
	'-v', '/home/kubernetes/bin/nvidia/vulkan/icd.d:/etc/vulkan/icd.d:ro',
	'--device', '/dev/nvidia0:/dev/nvidia0:mrw',
	'--device', '/dev/nvidiactl:/dev/nvidiactl:mrw',
	'--device', '/dev/nvidia-uvm:/dev/nvidia-uvm:mrw',
	'--device', '/dev/nvidia-uvm-tools:/dev/nvidia-uvm-tools:mrw',
	'-w', '/home/{identifier}',
	'-e', 'TF_CPP_MIN_LOG_LEVEL=3',
	'--entrypoint', './' + EXECUTABLE_NAME,
	'{image}']

DECODE_CMD = {True: DECODE_CMD_GPU, False: DECODE_CMD_CPU}


def main(args):
	log_file = os.path.join(mkdtemp(), '.log_decode')
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
		from models import Submission
		from django.core.exceptions import ObjectDoesNotExist

		logger.info('Obtaining submission')
		submission = get_submission(id=args.id)
		submission.status = Submission.STATUS_DECODING
		submission.save()
	except ObjectDoesNotExist:
		logger.error('Could not find submission')
		return 1
	except:
		logger.error('Some unexpected error occured')
		logger.debug(traceback.format_exc())
		return 1

	# directory on host in which decoder will be run
	identifier = submission.task.name + '_' + submission.phase.name + '_' + submission.team.username

	# create working directory
	work_dir = os.path.join(args.exec_dir, identifier)
	run('mkdir -p {dir}'.format(dir=work_dir), check=True, shell=True)

	# ativate service account (needed for gsutil)
	run('gcloud auth activate-service-account --quiet --key-file={key_file}'.format(
			key_file=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')),
		stdout=PIPE,
		stderr=PIPE,
		check=False,
		shell=True)

	# copy submission files
	try:
		logger.debug('Copying submission files')
		run('gsutil -m rsync -e -R gs://{bucket}/{path}/ {work_dir}'.format(
				bucket=os.environ['BUCKET_SUBMISSIONS'],
				path=submission.fs_path(),
				work_dir=work_dir),
			stdout=PIPE,
			stderr=PIPE,
			check=True,
			shell=True)
	except CalledProcessError as error:
		logger.error('Failed to copy submission files')
		logger.debug(error.stderr)
		submission.status = Submission.STATUS_ERROR
		submission.save()
		return 1

	# copy environment files
	try:
		logger.debug('Copying environment files')
		run('gsutil -m rsync -e -R gs://{bucket}/{path}/ {work_dir}'.format(
				bucket=os.environ['BUCKET_ENVIRONMENTS'],
				path=os.path.join(submission.task.name, submission.phase.name),
				work_dir=work_dir),
			stderr=PIPE,
			stdout=PIPE,
			check=True,
			shell=True)
	except CalledProcessError as error:
		logger.error('Failed to copy environment files')
		logger.debug(error.stderr)
		run('fusermount -u {}'.format(submission_dir), shell=True)
		submission.status = Submission.STATUS_ERROR
		submission.save()
		return 1

	try:
		# unzip decoder if zipped
		zip_path = os.path.join(work_dir, ZIP_FILE_NAME)
		if os.path.exists(zip_path):
			logger.info('Unzipping decoder')
			ZipFile(zip_path).extractall(work_dir)

		# check if decoder executable is present
		executable_path = os.path.join(work_dir, EXECUTABLE_NAME)
		if not os.path.exists(executable_path):
			logger.error('Missing executable \'{}\''.format(EXECUTABLE_NAME))
			return 1

		run('chmod +x {}'.format(executable_path), check=True, shell=True)

		# make sure latest Docker image is present before decoder starts
		try:
			logger.info('Pulling Docker image')
			run('docker pull {} > /dev/null'.format(submission.docker_image.name),
				stdout=PIPE, stderr=PIPE, check=True, shell=True)
		except CalledProcessError as error:
			logger.warn('Failed to pull Docker image')
			logger.debug(error.stdout)
			logger.debug(error.stderr)

		# delete container if for some reason it already exists
		containers = run('docker ps -a --format {{.Names}}',
			stdout=PIPE, stderr=DEVNULL, check=True, shell=True).stdout
		if identifier in containers.decode().split():
			logger.debug('Removing existing container')
			run('docker stop {}'.format(identifier),
				stdout=PIPE, stderr=PIPE, check=True, shell=True)
			run('docker rm {}'.format(identifier),
				stdout=PIPE, stderr=PIPE, check=True, shell=True)

		try:
			decode_cmd = [
				s.format(
					work_dir=work_dir,
					identifier=identifier,
					image=submission.docker_image.name,
					memory_limit=submission.phase.memory,
					num_cpus=submission.phase.cpu)
				for s in DECODE_CMD[submission.docker_image.gpu]]

			# run decoder
			logger.info('Running decoder')
			start = time.time()
			run(decode_cmd, timeout=submission.phase.timeout, check=True, shell=False)
			logger.info('Decoding complete')

			submission.decoding_time = time.time() - start
			submission.status = Submission.STATUS_DECODED
			submission.save()

		except CalledProcessError as error:
			submission.status = Submission.STATUS_DECODING_FAILED
			submission.save()

			if error.returncode == 125:
				logger.error('Unable to start Docker container')
				logger.debug(error)
				return 1

			elif error.returncode == 137:
				# check if process was killed by OOMKiller
				process = run('docker inspect {}'.format(identifier),
					stdout=PIPE, stderr=PIPE, check=True, shell=True)

				if '"OOMKilled": true' in process.stdout.decode():
					logger.error('The decoder exceeded the memory limit ({})'.format(
						submission.phase.memory))
					return 1

			logger.error('The decoder has failed ({})'.format(error.returncode))
			logger.debug(error)
			return 1

		except TimeoutExpired:
			logger.error('Decoding exceeded the time limit ({} seconds)'.format(submission.phase.timeout))
			return 1

		finally:
			# remove docker container
			run('docker rm {}'.format(identifier),
				stderr=PIPE, stdout=PIPE, check=False, shell=True)

	except:
		logger.error('Some unexpected error occured')
		logger.debug(traceback.format_exc())
		submission.status = Submission.STATUS_ERROR
		submission.save()
		return 1

	finally:
		# copy (intermediate) results back to submission directory
		run('mv {log_file} {work_dir}'.format(log_file=log_file, work_dir=work_dir),
			check=False,
			shell=True)
		run('gsutil -m rsync -e -C -R {work_dir} gs://{bucket}/{path}/'.format(
				bucket=os.environ['BUCKET_SUBMISSIONS'],
				path=submission.fs_path(),
				work_dir=work_dir),
			stdout=PIPE,
			stderr=PIPE,
			check=False,
			shell=True)

		# remove working directory
		run('rm -rf {}'.format(work_dir), shell=True)

	return 0


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('--id', type=int, required=True,
		help='Used to identify the submission')
	parser.add_argument('--exec_dir', type=str, default='/var/lib/docker/submissions',
		help='Location of executable directory which exists both on host and inside container')
	parser.add_argument('--debug', action='store_true')

	args = parser.parse_args()

	sys.exit(main(args))
