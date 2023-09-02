import os
import csv
import numpy as np
import json
import mmd
import scipy
from PIL import Image
from msssim import MultiScaleSSIM

def evaluate(submission_files, target_files, settings={}, logger=None):
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
    patch_size = settings.get('patch_size', 256)

    num_dims = 0
    sqerror_values = []
    msssim_values = []
    accuracy_values = []

    # Full dataset values
    kendall_tau_b_value = -2
    pcc_value = -2
    srcc_value = -2
    

    # used by FID
    target_patches = []
    submission_patches = []
    rs = np.random.RandomState(0)

    for file_idx, name in enumerate(target_files):
        if name.endswith('.csv'):
            file0 = read_csv(target_files[name], logger)
            file1 = read_csv(submission_files[name], logger)

            if file0 is None:
                logger.error('Failed to load targets')
            if file1 is None:
                logger.error('Could not read CSV file')

            if file0 and file1:
                if 'accuracy' in metrics:
                    value = accuracy(file0, file1, logger)
                    if value is None or np.isnan(value):
                        logger.error('Evaluation of accuracy failed, assuming accuracy of 0%')
                        accuracy_values.append(0.0)
                    else:
                        accuracy_values.append(value)

                if 'pcc' in metrics:
                    value = pcc(file0, file1, logger)
                    if value is None or np.isnan(value):
                        logger.error('Evaluation of pcc failed, setting to -2')
                        pcc_value = -2
                    else:
                        pcc_value = value

                if 'srcc' in metrics:
                    value = srcc(file0, file1, logger)
                    if value is None or np.isnan(value):
                        logger.error('Evaluation of srcc failed, setting to -2')
                        srcc_value = -2
                    else:
                        srcc_value = value

                if 'kendall_tau_b' in metrics:
                    value = kendall_tau_b(file0, file1, logger)
                    if value is None or np.isnan(value):
                        logger.error('Evaluation of kendall\'s tau-b failed, setting to -2')
                        kendall_tau_b_value = -2
                    else:
                        kendall_tau_b_value = value
                    

        else:
            logger.debug(f'Metrics for image number `{file_idx}` of `{len(target_files)}`: `{name}`')
            image0 = np.asarray(Image.open(target_files[name]).convert('RGB'), dtype=np.float32)
            image1 = np.asarray(Image.open(submission_files[name]).convert('RGB'), dtype=np.float32)

            num_dims += image0.size

            if 'PSNR' in metrics:
                sqerror_values.append(mse(image1, image0))
            if 'MSSSIM' in metrics:
                value = msssim(image0, image1) * image0.size
                if np.isnan(value):
                    value = 0.0
                    if logger:
                        logger.warning(
                                f'Evaluation of MSSSIM for `{name}` returned NaN. Assuming MSSSIM is zero.')
                msssim_values.append(value)
            if 'KID' in metrics or 'FID' in metrics:
                if image0.shape[0] >= patch_size and image0.shape[1] >= patch_size:
                    # extract random patches for later use
                    i = rs.randint(image0.shape[0] - patch_size + 1)
                    j = rs.randint(image0.shape[1] - patch_size + 1)
                    target_patches.append(image0[i:i + patch_size, j:j + patch_size])
                    submission_patches.append(image1[i:i + patch_size, j:j + patch_size])

    results = {}

    if 'PSNR' in metrics:
        results['PSNR'] = mse2psnr(np.sum(sqerror_values) / num_dims)
    if 'MSSSIM' in metrics:
        results['MSSSIM'] = np.sum(msssim_values) / num_dims
    if 'FID' in metrics:
        results['FID'] = fid(target_patches, submission_patches)
    if 'accuracy' in metrics:
        results['accuracy'] = np.mean(accuracy_values)
    if 'kendall_tau_b' in metrics:
        results['kendall_tau_b'] = kendall_tau_b_value
    if 'srcc' in metrics:
        results['srcc'] = srcc_value
    if 'pcc' in metrics:
        results['pcc'] = pcc_value

    return results


def _missing_keys(file0, file1):
    for k in file0.keys():
        if k not in file1:
            return k
    return None


def pcc(file0, file1, logger=None):
    # First check that we have no 
    missing_key_question_mark = _missing_keys(file0, file1)
    if missing_key_question_mark != None:
        if logger:
            logger.error(f'Missing key {k}')
        return None

    # Get all the values of each mapped up. Don't assume they are in same order.
    x_list = []
    y_list = []
    for k in file0.keys():
        x_list.append(float(file0[k]))
        y_list.append(float(file1[k]))
    value = scipy.stats.pearsonr(x_list, y_list).statistic
    return value


def srcc(file0, file1, logger=None):
    # First check that we have no 
    missing_key_question_mark = _missing_keys(file0, file1)
    if missing_key_question_mark != None:
        if logger:
            logger.error(f'Missing key {k}')
        return None

    # Get all the values of each mapped up. Don't assume they are in same order.
    x_list = []
    y_list = []
    for k in file0.keys():
        x_list.append(float(file0[k]))
        y_list.append(float(file1[k]))
    value = scipy.stats.spearmanr(x_list, y_list).statistic
    return value

def kendall_tau_b(file0, file1, logger=None):
    # First check that we have no 
    missing_key_question_mark = _missing_keys(file0, file1)
    if missing_key_question_mark != None:
        if logger:
            logger.error(f'Missing key {k}')
        return None

    # Get all the values of each mapped up. Don't assume they are in same order.
    x_list = []
    y_list = []
    for k in file0.keys():
        x_list.append(float(file0[k]))
        y_list.append(float(file1[k]))
    value = scipy.stats.kendalltau(x_list, y_list).statistic
    return value


def fid(images0, images1):
    with open(os.devnull, 'w') as devnull:
        kwargs = {
                'get_codes': True,
                'get_preds': False,
                'batch_size': 100,
                'output': devnull}
        model = mmd.Inception()
        features0 = mmd.featurize(images0, model, **kwargs)[-1]
        features1 = mmd.featurize(images1, model, **kwargs)[-1]
        # average across splits
        score = np.mean(
                mmd.fid_score(
                        features0,
                        features1,
                        splits=10,
                        split_method='bootstrap',
                        output=devnull))
    return score


def mse(image0, image1):
    return np.sum(np.square(image1.astype(np.float64) - image0.astype(np.float64)))


def mse2psnr(mse):
    mse = mse.astype(np.float64)
    return 20. * np.log10(255.) - 10. * np.log10(mse)


def msssim(image0, image1):
    return MultiScaleSSIM(image0[None], image1[None])


def accuracy(file0, file1, logger=None):
    matches = 0.
    nonmatches = 0.
    for k in file0.keys():
        if k not in file1:
            if logger:
                logger.error(f'Missing key {k}')
            return None
        if file0[k] == file1[k]:
            matches += 1
        else:
            nonmatches += 1
    return matches / float(matches + nonmatches)


def read_csv(file_name, logger=None):
    """Read CSV file.

    The CSV file contains 4 columns:
    FileA,FileB,OriginalFile,BinaryScore

    or

    FileA,MOS.

    FileA/FileB: paths to images generated by the two methods will be compared.
    OriginalFile: path to the original (uncompressed) image filed.
    BinaryScore: 0/1. This should be 0 if FileA is closer to the original than
    FileB.

    Args:
            file_name: file name to read.

    Returns:
            dict({a/b/c} -> score).
    """
    contents = {}
    with open(file_name) as csvfile:
        reader = csv.reader(csvfile)

        # We actually allow CSVs of either length 4 (image track) or length 2 (video track)
        for row in reader:
            if len(row) != 4 and len(row) != 2:
                if logger:
                    logger.error('Expected CSV file to contain 4 columns. Found %d.', len(row))
                return None

            contents[','.join(row[:-1])] = row[-1]
    return contents
