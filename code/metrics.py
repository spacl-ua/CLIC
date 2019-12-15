import numpy as np
import json
from PIL import Image
from msssim import MultiScaleSSIM


def evaluate(submission_images, target_images, settings={}):
	"""
	Calculates metrics for the given images.
	"""

	if settings is None:
		settings = {}
	if isinstance(settings, str):
		try:
			settings = json.loads(settings)
		except json.JSONDecodeError:
			settings = {}
	metrics = settings.get('metrics', ['PSNR', 'MSSSIM'])
	num_dims = 0
	sqerror_values = []
	msssim_values = []

	for name in target_images:
		image0 = np.asarray(Image.open(target_images[name]).convert('RGB'), dtype=np.float32)
		image1 = np.asarray(Image.open(submission_images[name]).convert('RGB'), dtype=np.float32)

		num_dims += image0.size

		if 'PSNR' in metrics:
			sqerror_values.append(mse(image1, image0))
		if 'MSSSIM' in metrics:
			msssim_values.append(msssim(image0, image1) * image0.size)

	results = {}

	if 'PSNR' in metrics:
		results['PSNR'] = mse2psnr(np.sum(sqerror_values) / num_dims)
	if 'MSSSIM' in metrics:
		results['MSSSIM'] = np.sum(msssim_values) / num_dims

	return results


def mse(image0, image1):
	return np.sum(np.square(image1 - image0))


def mse2psnr(mse):
	return 20. * np.log10(255.) - 10. * np.log10(mse)


def msssim(image0, image1):
	return MultiScaleSSIM(image0[None], image1[None])
