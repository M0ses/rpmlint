import os

import pytest
from rpmlint.checks.BinariesCheck import BinariesCheck
from rpmlint.filter import Filter
from rpmlint.lddparser import LddParser
from rpmlint.pkg import FakePkg

from Testing import CONFIG, get_tested_path


@pytest.fixture(scope='function', autouse=True)
def binariescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    return output, test


def get_full_path(path):
    return str(get_tested_path(os.path.join('ldd', path)))


def lddparser(path, system_path=None):
    if system_path is None:
        system_path = path
    return LddParser(get_full_path(path), system_path)


def test_unused_dependency():
    ldd = lddparser('libtirpc.so.3.0.0')
    assert not ldd.parsing_failed
    assert len(ldd.unused_dependencies) >= 1
    assert 'liXXXsapi_krb5.so.2' in ldd.unused_dependencies


def test_undefined_symbol():
    ldd = lddparser('libtirpc.so.3.0.0')
    assert not ldd.parsing_failed
    assert len(ldd.undefined_symbols) >= 22
    assert 'GSS_C_NT_HOSTBASED_SERVICE' in ldd.undefined_symbols


def test_ldd_parser_failure():
    ldd = lddparser('not-existing-file')
    assert ldd.parsing_failed


def test_dependencies():
    ldd = lddparser('libtirpc.so.3.0.0')
    assert not ldd.parsing_failed
    assert len(ldd.dependencies) == 5
    assert any([d for d in ldd.dependencies if d.startswith('linux-vdso.so.1')])


def test_unused_dependency_in_package(binariescheck):
    output, test = binariescheck
    test.run_elf_checks(FakePkg('fake'), get_full_path('libtirpc.so.3.0.0'), '/lib64/x.so')
    assert not test.readelf_parser.parsing_failed()
    assert not test.ldd_parser.parsing_failed
    out = output.print_results(output.results)
    assert 'unused-direct-shlib-dependency ' in out


def test_opt_dependency(binariescheck):
    output, test = binariescheck
    test.run_elf_checks(FakePkg('fake'), get_full_path('opt-dependency'), '/bin/opt-dependency')
    assert not test.readelf_parser.parsing_failed()
    assert not test.ldd_parser.parsing_failed
    out = output.print_results(output.results)
    assert 'E: linked-against-opt-library /bin/opt-dependency /opt/libfoo.so' in out


def test_usr_dependency(binariescheck):
    output, test = binariescheck
    test.run_elf_checks(FakePkg('fake'), get_full_path('usr-dependency'), '/bin/usr-dependency')
    assert not test.readelf_parser.parsing_failed()
    assert not test.ldd_parser.parsing_failed
    out = output.print_results(output.results)
    assert 'W: linked-against-usr-library /bin/usr-dependency /usr/libfoo.so' in out