import nose
import unittest

import datetime
import numpy as np

from pandas import compat
from pandas.compat import u
from pandas import (Series, DataFrame, Panel, MultiIndex, bdate_range,
                    date_range, period_range, Index, SparseSeries, SparseDataFrame,
                    SparsePanel)
import pandas.util.testing as tm
from pandas.util.testing import ensure_clean
from pandas.tests.test_series import assert_series_equal
from pandas.tests.test_frame import assert_frame_equal
from pandas.tests.test_panel import assert_panel_equal

import pandas
from pandas.sparse.tests.test_sparse import assert_sp_series_equal, assert_sp_frame_equal
from pandas import Timestamp, tslib

nan = np.nan

from pandas.io.packers import to_msgpack, read_msgpack

_multiprocess_can_split_ = False


def check_arbitrary(a, b):

    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        assert(len(a) == len(b))
        for a_, b_ in zip(a, b):
            check_arbitrary(a_, b_)
    elif isinstance(a, Panel):
        assert_panel_equal(a, b)
    elif isinstance(a, DataFrame):
        assert_frame_equal(a, b)
    elif isinstance(a, Series):
        assert_series_equal(a, b)
    else:
        assert(a == b)


class Test(unittest.TestCase):

    def setUp(self):
        self.path = '__%s__.msg' % tm.rands(10)

    def tearDown(self):
        pass

    def encode_decode(self, x, **kwargs):
        with ensure_clean(self.path) as p:
            to_msgpack(p, x, **kwargs)
            return read_msgpack(p, **kwargs)

class TestAPI(Test):

    def test_string_io(self):

        df = DataFrame(np.random.randn(10,2))
        s = df.to_msgpack(None)
        result = read_msgpack(s.getvalue())
        tm.assert_frame_equal(result,df)

        s = to_msgpack(None,df)
        result = read_msgpack(s.getvalue())
        tm.assert_frame_equal(result, df)

        with ensure_clean(self.path) as p:

            s = df.to_msgpack(None)
            fh = open(p,'wb')
            fh.write(s.getvalue())
            fh.close()
            result = read_msgpack(p)
            tm.assert_frame_equal(result, df)

    def test_iterator_with_string_io(self):

        dfs = [ DataFrame(np.random.randn(10,2)) for i in range(5) ]
        s = to_msgpack(None,*dfs)
        for i, result in enumerate(read_msgpack(s.getvalue(),iterator=True)):
            tm.assert_frame_equal(result,dfs[i])

        s = to_msgpack(None,*dfs)
        for i, result in enumerate(read_msgpack(s,iterator=True)):
            tm.assert_frame_equal(result,dfs[i])

class TestNumpy(Test):

    def test_numpy_scalar_float(self):
        x = np.float32(np.random.rand())
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_numpy_scalar_complex(self):
        x = np.complex64(np.random.rand() + 1j * np.random.rand())
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_scalar_float(self):
        x = np.random.rand()
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_scalar_complex(self):
        x = np.random.rand() + 1j * np.random.rand()
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_list_numpy_float(self):
        raise nose.SkipTest('buggy test')
        x = [np.float32(np.random.rand()) for i in range(5)]
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_list_numpy_float_complex(self):
        if not hasattr(np, 'complex128'):
            raise nose.SkipTest('numpy cant handle complex128')

        # buggy test
        raise nose.SkipTest('buggy test')
        x = [np.float32(np.random.rand()) for i in range(5)] + \
            [np.complex128(np.random.rand() + 1j * np.random.rand())
             for i in range(5)]
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_list_float(self):
        x = [np.random.rand() for i in range(5)]
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_list_float_complex(self):
        x = [np.random.rand() for i in range(5)] + \
            [(np.random.rand() + 1j * np.random.rand()) for i in range(5)]
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_dict_float(self):
        x = {'foo': 1.0, 'bar': 2.0}
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_dict_complex(self):
        x = {'foo': 1.0 + 1.0j, 'bar': 2.0 + 2.0j}
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_dict_numpy_float(self):
        x = {'foo': np.float32(1.0), 'bar': np.float32(2.0)}
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_dict_numpy_complex(self):
        x = {'foo': np.complex128(
            1.0 + 1.0j), 'bar': np.complex128(2.0 + 2.0j)}
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_numpy_array_float(self):

        # run multiple times
        for n in range(10):
            x = np.random.rand(10)
            for dtype in ['float32','float64']:
                x = x.astype(dtype)
                x_rec = self.encode_decode(x)
                tm.assert_almost_equal(x,x_rec)

    def test_numpy_array_complex(self):
        x = (np.random.rand(5) + 1j * np.random.rand(5)).astype(np.complex128)
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

    def test_list_mixed(self):
        x = [1.0, np.float32(3.5), np.complex128(4.25), u('foo')]
        x_rec = self.encode_decode(x)
        tm.assert_almost_equal(x,x_rec)

class TestBasic(Test):

    def test_timestamp(self):

        for i in [Timestamp(
            '20130101'), Timestamp('20130101', tz='US/Eastern'),
                Timestamp('201301010501')]:
            i_rec = self.encode_decode(i)
            self.assert_(i == i_rec)

    def test_datetimes(self):

        for i in [datetime.datetime(
            2013, 1, 1), datetime.datetime(2013, 1, 1, 5, 1),
                datetime.date(2013, 1, 1), np.datetime64(datetime.datetime(2013, 1, 5, 2, 15))]:
            i_rec = self.encode_decode(i)
            self.assert_(i == i_rec)

    def test_timedeltas(self):

        for i in [datetime.timedelta(days=1),
                  datetime.timedelta(days=1, seconds=10),
                  np.timedelta64(1000000)]:
            i_rec = self.encode_decode(i)
            self.assert_(i == i_rec)


class TestIndex(Test):

    def setUp(self):
        super(TestIndex, self).setUp()

        self.d = {
            'string': tm.makeStringIndex(100),
            'date': tm.makeDateIndex(100),
            'int': tm.makeIntIndex(100),
            'float': tm.makeFloatIndex(100),
            'empty': Index([]),
            'tuple': Index(zip(['foo', 'bar', 'baz'], [1, 2, 3])),
            'period': Index(period_range('2012-1-1', freq='M', periods=3)),
            'date2': Index(date_range('2013-01-1', periods=10)),
            'bdate': Index(bdate_range('2013-01-02', periods=10)),
        }

        self.mi = {
            'reg': MultiIndex.from_tuples([('bar', 'one'), ('baz', 'two'), ('foo', 'two'),
                                           ('qux', 'one'), ('qux', 'two')], names=['first', 'second']),
        }

    def test_basic_index(self):

        for s, i in self.d.items():
            i_rec = self.encode_decode(i)
            self.assert_(i.equals(i_rec))

    def test_multi_index(self):

        for s, i in self.mi.items():
            i_rec = self.encode_decode(i)
            self.assert_(i.equals(i_rec))

    def test_unicode(self):
        i = tm.makeUnicodeIndex(100)

        # this currently fails
        self.assertRaises(UnicodeEncodeError, self.encode_decode, i)

        #i_rec = self.encode_decode(i)
        #self.assert_(i.equals(i_rec))


class TestSeries(Test):

    def setUp(self):
        super(TestSeries, self).setUp()

        self.d = {}

        s = tm.makeStringSeries()
        s.name = 'string'
        self.d['string'] = s

        s = tm.makeObjectSeries()
        s.name = 'object'
        self.d['object'] = s

        s = Series(tslib.iNaT, dtype='M8[ns]', index=range(5))
        self.d['date'] = s

        data = {
            'A': [0., 1., 2., 3., np.nan],
            'B': [0, 1, 0, 1, 0],
            'C': ['foo1', 'foo2', 'foo3', 'foo4', 'foo5'],
            'D': date_range('1/1/2009', periods=5),
            'E': [0., 1, Timestamp('20100101'), 'foo', 2.],
        }

        self.d['float'] = Series(data['A'])
        self.d['int'] = Series(data['B'])
        self.d['mixed'] = Series(data['E'])

    def test_basic(self):

        # run multiple times here
        for n in range(10):
            for s, i in self.d.items():
                i_rec = self.encode_decode(i)
                assert_series_equal(i, i_rec)


class TestNDFrame(Test):

    def setUp(self):
        super(TestNDFrame, self).setUp()

        data = {
            'A': [0., 1., 2., 3., np.nan],
            'B': [0, 1, 0, 1, 0],
            'C': ['foo1', 'foo2', 'foo3', 'foo4', 'foo5'],
            'D': date_range('1/1/2009', periods=5),
            'E': [0., 1, Timestamp('20100101'), 'foo', 2.],
        }

        self.frame = {
            'float': DataFrame(dict(A=data['A'], B=Series(data['A']) + 1)),
            'int': DataFrame(dict(A=data['B'], B=Series(data['B']) + 1)),
            'mixed': DataFrame(dict([(k, data[k]) for k in ['A', 'B', 'C', 'D']]))}

        self.panel = {
            'float': Panel(dict(ItemA=self.frame['float'], ItemB=self.frame['float'] + 1))}

    def test_basic_frame(self):

        for s, i in self.frame.items():
            i_rec = self.encode_decode(i)
            assert_frame_equal(i, i_rec)

    def test_basic_panel(self):

        for s, i in self.panel.items():
            i_rec = self.encode_decode(i)
            assert_panel_equal(i, i_rec)

    def test_multi(self):

        i_rec = self.encode_decode(self.frame)
        for k in self.frame.keys():
            assert_frame_equal(self.frame[k], i_rec[k])

        l = tuple(
            [self.frame['float'], self.frame['float'].A, self.frame['float'].B, None])
        l_rec = self.encode_decode(l)
        check_arbitrary(l, l_rec)

        # this is an oddity in that packed lists will be returned as tuples
        l = [self.frame['float'], self.frame['float']
             .A, self.frame['float'].B, None]
        l_rec = self.encode_decode(l)
        self.assert_(isinstance(l_rec, tuple))
        check_arbitrary(l, l_rec)

    def test_iterator(self):

        l = [self.frame['float'], self.frame['float']
             .A, self.frame['float'].B, None]

        with ensure_clean(self.path) as path:
            to_msgpack(path, *l)
            for i, packed in enumerate(read_msgpack(path, iterator=True)):
                check_arbitrary(packed, l[i])


class TestSparse(Test):

    def _check_roundtrip(self, obj, comparator, **kwargs):

        # currently these are not implemetned
        #i_rec = self.encode_decode(obj)
        #comparator(obj, i_rec, **kwargs)
        self.assertRaises(NotImplementedError, self.encode_decode, obj)

    def test_sparse_series(self):

        s = tm.makeStringSeries()
        s[3:5] = np.nan
        ss = s.to_sparse()
        self._check_roundtrip(ss, tm.assert_series_equal,
                              check_series_type=True)

        ss2 = s.to_sparse(kind='integer')
        self._check_roundtrip(ss2, tm.assert_series_equal,
                              check_series_type=True)

        ss3 = s.to_sparse(fill_value=0)
        self._check_roundtrip(ss3, tm.assert_series_equal,
                              check_series_type=True)

    def test_sparse_frame(self):

        s = tm.makeDataFrame()
        s.ix[3:5, 1:3] = np.nan
        s.ix[8:10, -2] = np.nan
        ss = s.to_sparse()

        self._check_roundtrip(ss, tm.assert_frame_equal,
                              check_frame_type=True)

        ss2 = s.to_sparse(kind='integer')
        self._check_roundtrip(ss2, tm.assert_frame_equal,
                              check_frame_type=True)

        ss3 = s.to_sparse(fill_value=0)
        self._check_roundtrip(ss3, tm.assert_frame_equal,
                              check_frame_type=True)

    def test_sparse_panel(self):

        items = ['x', 'y', 'z']
        p = Panel(dict((i, tm.makeDataFrame().ix[:2, :2]) for i in items))
        sp = p.to_sparse()

        self._check_roundtrip(sp, tm.assert_panel_equal,
                              check_panel_type=True)

        sp2 = p.to_sparse(kind='integer')
        self._check_roundtrip(sp2, tm.assert_panel_equal,
                              check_panel_type=True)

        sp3 = p.to_sparse(fill_value=0)
        self._check_roundtrip(sp3, tm.assert_panel_equal,
                              check_panel_type=True)


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__, '-vvs', '-x', '--pdb', '--pdb-failure'],
                   exit=False)
