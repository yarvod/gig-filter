import os

import numpy as np


def linear(x, a, b):
    return a * x + b


def linear_fit(x, y):
    x = np.array(x)
    y = np.array(y)
    # number of observations/points
    n = np.size(x)

    # mean of x and y vector
    m_x = np.mean(x)
    m_y = np.mean(y)

    # calculating cross-deviation and deviation about x
    SS_xy = np.sum(y * x) - n * m_y * m_x
    SS_xx = np.sum(x * x) - n * m_x * m_x

    # calculating regression coefficients
    b_1 = SS_xy / SS_xx
    b_0 = m_y - b_1 * m_x

    return b_1, b_0


def truncate_path(path: str):
    try:
        return os.path.split(path)[-1]
    except IndexError:
        return "Undefined path"
