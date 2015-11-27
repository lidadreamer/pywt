#!/usr/bin/env python

from __future__ import division, print_function, absolute_import

import numpy as np
from itertools import combinations
from numpy.testing import (run_module_suite, assert_allclose, assert_,
                           assert_raises, assert_equal)

import pywt

# Check that float32 and complex64 are preserved.  Other real types get
# converted to float64.
dtypes_in = [np.int8, np.float32, np.float64, np.complex64, np.complex128]
dtypes_out = [np.float64, np.float32, np.float64, np.complex64, np.complex128]


def test_dwtn_input():
    # Array-like must be accepted
    pywt.dwtn([1, 2, 3, 4], 'haar')
    # Others must not
    data = dict()
    assert_raises(TypeError, pywt.dwtn, data, 'haar')
    # Must be at least 1D
    assert_raises(ValueError, pywt.dwtn, 2, 'haar')


def test_3D_reconstruct():
    data = np.array([
        [[0, 4, 1, 5, 1, 4],
         [0, 5, 26, 3, 2, 1],
         [5, 8, 2, 33, 4, 9],
         [2, 5, 19, 4, 19, 1]],
        [[1, 5, 1, 2, 3, 4],
         [7, 12, 6, 52, 7, 8],
         [2, 12, 3, 52, 6, 8],
         [5, 2, 6, 78, 12, 2]]])

    wavelet = pywt.Wavelet('haar')
    for mode in pywt.Modes.modes:
        d = pywt.dwtn(data, wavelet, mode=mode)
        assert_allclose(data, pywt.idwtn(d, wavelet, mode=mode),
                        rtol=1e-13, atol=1e-13)


def test_dwdtn_idwtn_allwavelets():
    rstate = np.random.RandomState(1234)
    r = rstate.randn(16, 16)
    # test 2D case only for all wavelet types
    wavelist = pywt.wavelist()
    if 'dmey' in wavelist:
        wavelist.remove('dmey')
    for wavelet in wavelist:
        for mode in pywt.Modes.modes:
            coeffs = pywt.dwtn(r, wavelet, mode=mode)
            assert_allclose(pywt.idwtn(coeffs, wavelet, mode=mode),
                            r, rtol=1e-7, atol=1e-7)


def test_stride():
    wavelet = pywt.Wavelet('haar')

    for dtype in ('float32', 'float64'):
        data = np.array([[0, 4, 1, 5, 1, 4],
                         [0, 5, 6, 3, 2, 1],
                         [2, 5, 19, 4, 19, 1]],
                        dtype=dtype)

        for mode in pywt.Modes.modes:
            expected = pywt.dwtn(data, wavelet)
            strided = np.ones((3, 12), dtype=data.dtype)
            strided[::-1, ::2] = data
            strided_dwtn = pywt.dwtn(strided[::-1, ::2], wavelet)
            for key in expected.keys():
                assert_allclose(strided_dwtn[key], expected[key])


def test_byte_offset():
    wavelet = pywt.Wavelet('haar')
    for dtype in ('float32', 'float64'):
        data = np.array([[0, 4, 1, 5, 1, 4],
                         [0, 5, 6, 3, 2, 1],
                         [2, 5, 19, 4, 19, 1]],
                        dtype=dtype)

        for mode in pywt.Modes.modes:
            expected = pywt.dwtn(data, wavelet)
            padded = np.ones((3, 6), dtype=np.dtype([('data', data.dtype),
                                                     ('pad', 'byte')]))
            padded[:] = data
            padded_dwtn = pywt.dwtn(padded['data'], wavelet)
            for key in expected.keys():
                assert_allclose(padded_dwtn[key], expected[key])


def test_3D_reconstruct_complex():
    # All dimensions even length so `take` does not need to be specified
    data = np.array([
        [[0, 4, 1, 5, 1, 4],
         [0, 5, 26, 3, 2, 1],
         [5, 8, 2, 33, 4, 9],
         [2, 5, 19, 4, 19, 1]],
        [[1, 5, 1, 2, 3, 4],
         [7, 12, 6, 52, 7, 8],
         [2, 12, 3, 52, 6, 8],
         [5, 2, 6, 78, 12, 2]]])
    data = data + 1j

    wavelet = pywt.Wavelet('haar')
    d = pywt.dwtn(data, wavelet)
    # idwtn creates even-length shapes (2x dwtn size)
    original_shape = [slice(None, s) for s in data.shape]
    assert_allclose(data, pywt.idwtn(d, wavelet)[original_shape],
                    rtol=1e-13, atol=1e-13)


def test_idwtn_idwt2():
    data = np.array([
        [0, 4, 1, 5, 1, 4],
        [0, 5, 6, 3, 2, 1],
        [2, 5, 19, 4, 19, 1]])

    wavelet = pywt.Wavelet('haar')

    LL, (HL, LH, HH) = pywt.dwt2(data, wavelet)
    d = {'aa': LL, 'da': HL, 'ad': LH, 'dd': HH}

    for mode in pywt.Modes.modes:
        assert_allclose(pywt.idwt2((LL, (HL, LH, HH)), wavelet, mode=mode),
                        pywt.idwtn(d, wavelet, mode=mode),
                        rtol=1e-14, atol=1e-14)


def test_idwtn_idwt2_complex():
    data = np.array([
        [0, 4, 1, 5, 1, 4],
        [0, 5, 6, 3, 2, 1],
        [2, 5, 19, 4, 19, 1]])
    data = data + 1j
    wavelet = pywt.Wavelet('haar')

    LL, (HL, LH, HH) = pywt.dwt2(data, wavelet)
    d = {'aa': LL, 'da': HL, 'ad': LH, 'dd': HH}

    for mode in pywt.Modes.modes:
        assert_allclose(pywt.idwt2((LL, (HL, LH, HH)), wavelet, mode=mode),
                        pywt.idwtn(d, wavelet, mode=mode),
                        rtol=1e-14, atol=1e-14)


def test_idwtn_missing():
    # Test to confirm missing data behave as zeroes
    data = np.array([
        [0, 4, 1, 5, 1, 4],
        [0, 5, 6, 3, 2, 1],
        [2, 5, 19, 4, 19, 1]])

    wavelet = pywt.Wavelet('haar')

    coefs = pywt.dwtn(data, wavelet)

    # No point removing zero, or all
    for num_missing in range(1, len(coefs)):
        for missing in combinations(coefs.keys(), num_missing):
            missing_coefs = coefs.copy()
            for key in missing:
                del missing_coefs[key]
            LL = missing_coefs.get('aa', None)
            HL = missing_coefs.get('da', None)
            LH = missing_coefs.get('ad', None)
            HH = missing_coefs.get('dd', None)

            assert_allclose(pywt.idwt2((LL, (HL, LH, HH)), wavelet),
                            pywt.idwtn(missing_coefs, 'haar'), atol=1e-15)


def test_error_on_invalid_keys():
    data = np.array([
        [0, 4, 1, 5, 1, 4],
        [0, 5, 6, 3, 2, 1],
        [2, 5, 19, 4, 19, 1]])

    wavelet = pywt.Wavelet('haar')

    LL, (HL, LH, HH) = pywt.dwt2(data, wavelet)

    # unexpected key
    d = {'aa': LL, 'da': HL, 'ad': LH, 'dd': HH, 'ff': LH}
    assert_raises(ValueError, pywt.idwtn, d, wavelet)

    # a key whose value is None
    d = {'aa': LL, 'da': HL, 'ad': LH, 'dd': None}
    assert_raises(ValueError, pywt.idwtn, d, wavelet)

    # mismatched key lengths
    d = {'a': LL, 'da': HL, 'ad': LH, 'dd': HH}
    assert_raises(ValueError, pywt.idwtn, d, wavelet)


def test_error_mismatched_size():
    data = np.array([
        [0, 4, 1, 5, 1, 4],
        [0, 5, 6, 3, 2, 1],
        [2, 5, 19, 4, 19, 1]])

    wavelet = pywt.Wavelet('haar')

    LL, (HL, LH, HH) = pywt.dwt2(data, wavelet)

    # Pass/fail depends on first element being shorter than remaining ones so
    # set 3/4 to an incorrect size to maximize chances. Order of dict items
    # is random so may not trigger on every test run. Dict is constructed
    # inside idwtn function so no use using an OrderedDict here.
    LL = LL[:, :-1]
    LH = LH[:, :-1]
    HH = HH[:, :-1]
    d = {'aa': LL, 'da': HL, 'ad': LH, 'dd': HH}

    assert_raises(ValueError, pywt.idwtn, d, wavelet)


def test_dwt2_idwt2_dtypes():
    wavelet = pywt.Wavelet('haar')
    for dt_in, dt_out in zip(dtypes_in, dtypes_out):
        x = np.ones((4, 4), dtype=dt_in)
        errmsg = "wrong dtype returned for {0} input".format(dt_in)

        cA, (cH, cV, cD) = pywt.dwt2(x, wavelet)
        assert_(cA.dtype == cH.dtype == cV.dtype == cD.dtype,
                "dwt2: " + errmsg)

        x_roundtrip = pywt.idwt2((cA, (cH, cV, cD)), wavelet)
        assert_(x_roundtrip.dtype == dt_out, "idwt2: " + errmsg)


def test_dwtn_axes():
    data = np.array([[0, 1, 2, 3],
                     [1, 1, 1, 1],
                     [1, 4, 2, 8]])

    coefs = pywt.dwtn(data, 'haar', axes=(1,))
    expected_a = list(map(lambda x: pywt.dwt(x, 'haar')[0], data))
    assert_equal(coefs['a'], expected_a)
    expected_d = list(map(lambda x: pywt.dwt(x, 'haar')[1], data))
    assert_equal(coefs['d'], expected_d)

    coefs = pywt.dwtn(data, 'haar', axes=(1, 1))
    expected_aa = list(map(lambda x: pywt.dwt(x, 'haar')[0], expected_a))
    assert_equal(coefs['aa'], expected_aa)
    expected_ad = list(map(lambda x: pywt.dwt(x, 'haar')[1], expected_a))
    assert_equal(coefs['ad'], expected_ad)


def test_idwtn_axes():
    data = np.array([[0, 1, 2, 3],
                     [1, 1, 1, 1],
                     [1, 4, 2, 8]])
    coefs = pywt.dwtn(data, 'haar', axes=(1, 1))
    assert_allclose(pywt.idwtn(coefs, 'haar', axes=(1, 1)), data, atol=1e-14)


def test_idwt2_axes():
    data = np.array([[0, 1, 2, 3],
                     [1, 1, 1, 1],
                     [1, 4, 2, 8]])
    coefs = pywt.dwt2(data, 'haar', axes=(1, 1))
    assert_allclose(pywt.idwt2(coefs, 'haar', axes=(1, 1)), data, atol=1e-14)


def test_negative_axes():
    data = np.array([[0, 1, 2, 3],
                     [1, 1, 1, 1],
                     [1, 4, 2, 8]])
    coefs1 = pywt.dwtn(data, 'haar', axes=(1, 1))
    coefs2 = pywt.dwtn(data, 'haar', axes=(-1, -1))
    assert_equal(coefs1, coefs2)

    rec1 = pywt.idwtn(coefs1, 'haar', axes=(1, 1))
    rec2 = pywt.idwtn(coefs1, 'haar', axes=(-1, -1))
    assert_equal(rec1, rec2)


def test_dwtn_idwtn_dtypes():
    wavelet = pywt.Wavelet('haar')
    for dt_in, dt_out in zip(dtypes_in, dtypes_out):
        x = np.ones((4, 4), dtype=dt_in)
        errmsg = "wrong dtype returned for {0} input".format(dt_in)

        coeffs = pywt.dwtn(x, wavelet)
        for k, v in coeffs.items():
            assert_(v.dtype == dt_out, "dwtn: " + errmsg)

        x_roundtrip = pywt.idwtn(coeffs, wavelet)
        assert_(x_roundtrip.dtype == dt_out, "idwtn: " + errmsg)


def test_idwt2_size_mismatch_error():
    LL = np.zeros((6, 6))
    LH = HL = HH = np.zeros((5, 5))

    assert_raises(ValueError, pywt.idwt2, (LL, (LH, HL, HH)), wavelet='haar')


if __name__ == '__main__':
    run_module_suite()
