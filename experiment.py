#!/usr/bin/env python3
#   encoding: utf-8
#   experiment.py
# TODO documentation
import numpy as np
import scipy.stats as st

from collections import OrderedDict
from numba import jit, prange
from sklearn import svm, metrics
from sklearn.metrics.pairwise import rbf_kernel
from tqdm import tqdm

from basics import generate_random_weights, get_d0, pad_data, radius
from butterfly import butterfly_params, generate_butterfly_weights
from householder import generate_householder_weights
from kernels import approximate_arccos0_kernel, approximate_arccos1_kernel, \
                    approximate_rbf_kernel, arccos0_kernel, arccos1_kernel
from mapping import fast_batch_approx_arccos0, fast_batch_approx_arccos1, \
                    fast_batch_approx_rbf
from rom import generate_rademacher_weights, generate_gort_weights, \
                generate_rsimplex_weights, generate_but_weights
from qmc import generate_sobol_weights

APPROX = OrderedDict({'exact': None,
          'G': [False, generate_random_weights],
          'Gort': [False, generate_orthogonal_weights],
          'ROM': [False, generate_rademacher_weights],
          'H': [False, generate_householder_weights],
          'B dense': [False, generate_butterfly_weights],
          'B': [True, None]})
KERNEL = OrderedDict({
             'RBF': [rbf_kernel, approximate_rbf_kernel, fast_batch_approx_rbf]
             'Arccos 0': [arccos0_kernel, approximate_arccos0_kernel,
                          fast_batch_approx_arccos0]
             'Arccos 1': [arccos1_kernel, approximate_arccos1_kernel,
                          fast_batch_approx_arccos1]})
N_APPROX = len(APPROX.keys())


def kernel(x, y, k, kernel_type, approx_type):
    assert approx_type in APPROX, 'No such approximation type.'
    assert kernel_type in KERNEL, 'No such kernel type.'

    if approx_type == 'exact':
        kernel = KERNEL(kernel_type)[0]
        K = kernel(x, y)
        return K

    flag, generate_weights = APPROX[approx_type]
    kernel = KERNEL[kernel_type][flag+1]
    if flag:
        M, w = generate_weights(k, n)
    K = kernel(x, y, M, w)
    return K


def error(exact, approx):
    err = np.linalg.norm(exact - approx) / np.linalg.norm(exact)
    return err


def mserror(exact, approx):
    mse = ((exact - approx)**2).mean()
    return mse


def approximation(x, y, k, kernel_type, approx_type, exact):
    K = kernel(x, y, k, kernel_type, approx_type)
    err = error(exact, K)
    mse = mserror(exact, K)
    return K, err, mse


def experiment(x, y, k, kernel_type, start_deg=1, max_deg=3,
               step=1, shift=1, runs=3):
    K_exact = kernel(x, y, k, kernel_type, 'exact')
    steps = int(np.ceil(max_deg/step))
    errs = np.zeros((N_APPROX, steps, runs))
    mses = np.zeros((N_APPROX, steps, runs))
    ranks = np.zeros((N_APPROX, steps, runs))
    i = 0
    for approx_type in tqdm(APPROX.keys()):
        if approx_type == 'exact':
            continue
        for j, deg in enumerate(np.arange(start_deg, max_deg+step, step)):
            k = deg + shift
            for r in range(runs):
                K = kernel(x, y, k, kernel_type, approx_type)
                ranks[i, j, r] = np.linalg.matrix_rank(K)
                errs[i, j, r] = error(K_exact, K)
                mses[i, j, r] = mse(K_exact, K)
        i += 1
    return errs, mses


def get_estimator_score(data, labels, kernel_type, task):
    '''
    Args:
    =====
    task: if 0 - SVM, 1 - SVR
    kernel_type: any of sklearn's allowed kernel types.
    data: a tuple of matrices; if kernel_type = 'precomputed',
        data[0] is a train set kernel, data[1] - test set kernel,
        otherwise, data[0] is just a train set, data[1] - test set.
    labels: a tuple of target values, labels[0] is train targets,
        labels[1] - test targets.
    '''
    if task == 0:
        estimator = svm.SVC(kernel=kernel_type)
    elif task == 1:
        estimator = svm.SVR(kernel=kernel_type)
    else:
        raise Exception('task=0 for SVM, task=1 for SVR, \
                         other models not implemented')
    estimator.fit(data[0], labels[0])
    predicted = estimator.predict(data[1])
    if task == 0:
        return metrics.accuracy_score(labels[1], predicted)
    else:
        return metrics.r2_score(labels[1], predicted)
