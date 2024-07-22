import collections.abc
import gc

import numpy
import pytest
from numpy.testing import assert_array_equal

from ..plans import count
from ..utils import PersistentDict
from sqlitedict import SqliteDict as PersistentDict
from functools import partial
import msgpack_numpy

PersistentDict = partial(PersistentDict, autocommit=True, journal_mode="OFF")

def test_persistent_dict(tmp_file):
    d = PersistentDict(tmp_file)
    d["a"] = 1
    d["b"] = (1, 2)
    d["c"] = numpy.zeros((5, 5))
    d["d"] = {"a": 10, "b": numpy.ones((5, 5))}
    expected = dict(d)
    actual = PersistentDict(tmp_file)
    recursive_assert_equal(actual, expected)

    # Update a value and check again.
    d["a"] = 2
    expected = dict(d)
    # actual.reload()  # Force load changes from disk
    recursive_assert_equal(actual, expected)

    # Test element deletion
    del d["b"]
    with pytest.raises(KeyError):
        d["b"]
    assert "b" not in d

    # Smoke test the accessor and the __repr__.
    assert d.filename == tmp_file
    d.__repr__()


def test_persistent_dict_mutable_value(tmp_file):
    d = PersistentDict(tmp_file)
    print(f"1. {dict(d) = }")
    d["a"] = []
    print(f"2. {dict(d) = }")
    d["a"].append(1)
    print(f"3. {dict(d) = }")
    expected = {"a": [1]}
    # Check the in-memory version is updated
    recursive_assert_equal(d, expected)
    # Check that the __repr__ reflects this.
    assert "{'a': [1]}" in repr(d)
    # d.sync()
    # Check that contents are synced to disk at exit.
    # del d
    # 
    # gc.collect()
    actual = PersistentDict(tmp_file)
    recursive_assert_equal(actual, expected)


def test_pop(tmp_file):
    d = PersistentDict(tmp_file)
    d["a"] = 1
    d["b"] = 2
    d.pop("b")
    expected = {"a": 1}
    # Check the in-memory version is updated
    recursive_assert_equal(d, expected)
    # Check that the __repr__ reflects this.
    assert "{'a': 1}" in repr(d)
    # Check that contents are synced to disk at exit.
    del d
    gc.collect()
    actual = PersistentDict(tmp_file)
    recursive_assert_equal(actual, expected)


def test_popitem(tmp_file):
    d = PersistentDict(tmp_file)
    d["a"] = 1
    d["b"] = 2
    d.popitem()
    expected = {"a": 1}
    # Check the in-memory version is updated
    recursive_assert_equal(d, expected)
    # Check that the __repr__ reflects this.
    assert "{'a': 1}" in repr(d)
    # Check that contents are synced to disk at exit.
    del d
    gc.collect()
    actual = PersistentDict(tmp_file)
    recursive_assert_equal(actual, expected)


def test_update(tmp_file):
    d = PersistentDict(tmp_file)
    d.update(a=1)
    expected = {"a": 1}
    # Check the in-memory version is updated
    recursive_assert_equal(d, expected)
    # Check that the __repr__ reflects this.
    assert "{'a': 1}" in repr(d)
    # Check that contents are synced to disk at exit.
    del d
    gc.collect()
    actual = PersistentDict(tmp_file)
    recursive_assert_equal(actual, expected)


def test_setdefault(tmp_file):
    d = PersistentDict(tmp_file)
    d.setdefault("a", 1)
    expected = {"a": 1}
    # Check the in-memory version is updated
    recursive_assert_equal(d, expected)
    # Check that the __repr__ reflects this.
    assert "{'a': 1}" in repr(d)
    # Check that contents are synced to disk at exit.
    del d
    gc.collect()
    actual = PersistentDict(tmp_file)
    recursive_assert_equal(actual, expected)


def test_clear(tmp_file):
    d = PersistentDict(tmp_file)
    d["a"] = 1
    d.clear()
    expected = {}
    # Check the in-memory version is updated
    recursive_assert_equal(d, expected)
    # Check that the __repr__ reflects this.
    assert "{}" in repr(d)
    # Check that contents are synced to disk at exit.
    del d
    gc.collect()
    actual = PersistentDict(tmp_file)
    recursive_assert_equal(actual, expected)


def test_integration(tmp_file, RE, hw):
    """
    Test integration with RE.

    Not looking for anything *specific* here, just general paranoia in case
    unforseen future changes create a bad interaction between PersistentDict
    and RE, as happened with HistoryDict and RE.
    """
    d = PersistentDict(tmp_file)
    d["a"] = 1
    d["b"] = (1, 2)
    d["c"] = numpy.zeros((5, 5))
    d["d"] = {"a": 10, "b": numpy.ones((5, 5))}
    expected = dict(d)
    expected["scan_id"] = 1

    RE.md = d
    RE(count([hw.det]))
    recursive_assert_equal(RE.md, expected)

    reloaded = PersistentDict(tmp_file)
    recursive_assert_equal(reloaded, expected)


def recursive_assert_equal(actual, expected):
    assert set(actual.keys()) == set(expected.keys())
    for key in actual:
        if isinstance(actual[key], collections.abc.MutableMapping):
            recursive_assert_equal(actual[key], expected[key])
        else:
            assert_array_equal(actual[key], expected[key])
