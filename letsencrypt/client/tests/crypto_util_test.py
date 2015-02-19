"""Tests for letsencrypt.client.crypto_util."""
import datetime
import mock
import os
import pkg_resources
import unittest

import M2Crypto


RSA256_KEY = pkg_resources.resource_string(__name__, 'testdata/rsa256_key.pem')
RSA512_KEY = pkg_resources.resource_string(__name__, 'testdata/rsa512_key.pem')


class ValidCSRTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.valid_csr."""

    @classmethod
    def _call(cls, csr):
        from letsencrypt.client.crypto_util import valid_csr
        return valid_csr(csr)

    def _call_testdata(self, name):
        return self._call(pkg_resources.resource_string(
            __name__, os.path.join('testdata', name)))

    def test_valid_pem_true(self):
        self.assertTrue(self._call_testdata('csr.pem'))

    def test_valid_pem_san_true(self):
        self.assertTrue(self._call_testdata('csr-san.pem'))

    def test_valid_der_false(self):
        self.assertFalse(self._call_testdata('csr.der'))

    def test_valid_der_san_false(self):
        self.assertFalse(self._call_testdata('csr-san.der'))

    def test_empty_false(self):
        self.assertFalse(self._call(''))

    def test_random_false(self):
        self.assertFalse(self._call('foo bar'))


class CSRMatchesPubkeyTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.csr_matches_pubkey."""

    @classmethod
    def _call_testdata(cls, name, privkey):
        from letsencrypt.client.crypto_util import csr_matches_pubkey
        return csr_matches_pubkey(pkg_resources.resource_string(
            __name__, os.path.join('testdata', name)), privkey)

    def test_valid_true(self):
        self.assertTrue(self._call_testdata('csr.pem', RSA256_KEY))

    def test_invalid_false(self):
        self.assertFalse(self._call_testdata('csr.pem', RSA512_KEY))


class MakeKeyTest(unittest.TestCase):  # pylint: disable=too-few-public-methods
    """Tests for letsencrypt.client.crypto_util.make_key."""

    def test_it(self):  # pylint: disable=no-self-use
        from letsencrypt.client.crypto_util import make_key
        M2Crypto.RSA.load_key_string(make_key(1024))
        M2Crypto.RSA.load_key_string(make_key(2048))
        M2Crypto.RSA.load_key_string(make_key(4096))


class ValidPrivkeyTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.valid_privkey."""

    @classmethod
    def _call(cls, privkey):
        from letsencrypt.client.crypto_util import valid_privkey
        return valid_privkey(privkey)

    def test_valid_true(self):
        self.assertTrue(self._call(RSA256_KEY))

    def test_empty_false(self):
        self.assertFalse(self._call(''))

    def test_random_false(self):
        self.assertFalse(self._call('foo bar'))


class MakeSSCertTest(unittest.TestCase):
    # pylint: disable=too-few-public-methods
    """Tests for letsencrypt.client.crypto_util.make_ss_cert."""

    def test_it(self):  # pylint: disable=no-self-use
        from letsencrypt.client.crypto_util import make_ss_cert
        make_ss_cert(RSA256_KEY, ['example.com', 'www.example.com'])


class GetCertInfoTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.get_cert_info."""

    def setUp(self):
        self.cert_info = {
            'not_before': datetime.datetime(
                2014, 12, 11, 22, 34, 45, tzinfo=M2Crypto.ASN1.UTC),
            'not_after': datetime.datetime(
                2014, 12, 18, 22, 34, 45, tzinfo=M2Crypto.ASN1.UTC),
            'subject': 'C=US, ST=Michigan, L=Ann Arbor, O=University '
                       'of Michigan and the EFF, CN=example.com',
            'cn': 'example.com',
            'issuer': 'C=US, ST=Michigan, L=Ann Arbor, O=University '
                      'of Michigan and the EFF, CN=example.com',
            'serial': 1337L,
            'pub_key': 'RSA 512',
        }

    def _call(self, name):
        from letsencrypt.client.crypto_util import get_cert_info
        self.assertEqual(get_cert_info(pkg_resources.resource_filename(
            __name__, os.path.join('testdata', name))), self.cert_info)

    def test_single_domain(self):
        self.cert_info.update({
            'san': '',
            'fingerprint': '9F8CE01450D288467C3326AC0457E351939C72E',
        })
        self._call('cert.pem')

    def test_san(self):
        self.cert_info.update({
            'san': 'DNS:example.com, DNS:www.example.com',
            'fingerprint': '62F7110431B8E8F55905DBE5592518F9634AC50A',
        })
        self._call('cert-san.pem')


class GetSansFromCsrTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.get_sans_from_csr."""
    def test_extract_one_san(self):
        from letsencrypt.client.crypto_util import get_sans_from_csr
        csr = pkg_resources.resource_string(
            __name__, os.path.join('testdata', 'csr.pem'))
        result = get_sans_from_csr(csr)
        self.assertEqual(result, ['example.com'])

    def test_extract_two_sans(self):
        from letsencrypt.client.crypto_util import get_sans_from_csr
        csr = pkg_resources.resource_string(
            __name__, os.path.join('testdata', 'csr-san.pem'))
        result = get_sans_from_csr(csr)
        self.assertEqual(result, ['example.com', 'www.example.com'])

    def test_extract_six_sans(self):
        from letsencrypt.client.crypto_util import get_sans_from_csr
        csr = pkg_resources.resource_string(
            __name__, os.path.join('testdata', 'csr-6sans.pem'))
        result = get_sans_from_csr(csr)
        self.assertEqual(
            result, ["example.com", "example.org", "example.net",
                     "example.info", "subdomain.example.com",
                     "other.subdomain.example.com"])

    def test_parse_non_csr(self):
        from M2Crypto.X509 import X509Error
        from letsencrypt.client.crypto_util import get_sans_from_csr
        self.assertRaises(X509Error, get_sans_from_csr, "hello there")

    def test_parse_no_sans(self):
        from letsencrypt.client.crypto_util import get_sans_from_csr
        csr = pkg_resources.resource_string(
            __name__, os.path.join('testdata', 'csr-nosans.pem'))
        self.assertRaises(ValueError, get_sans_from_csr, csr)

    @mock.patch("M2Crypto.X509.load_request_string")
    def test_parse_weird_m2crypto_output(self, mock_lrs):
        # It's not clear how to reach this exception with invalid input,
        # because M2Crypto is likely to raise X509Error rather than
        # returning invalid output, but we can test the possibility with
        # mock.
        mock_lrs.as_text.return_value = "Something other than OpenSSL output"
        from letsencrypt.client.crypto_util import get_sans_from_csr
        self.assertRaises(ValueError, get_sans_from_csr, "input")

class MakeCSRTest(unittest.TestCase):  # pylint: disable=too-few-public-methods
    """Tests for letsencrypt.client.crypto_util.make_csr."""
    def test_make_csr(self):
        from letsencrypt.client.crypto_util import make_csr, get_sans_from_csr
        result = make_csr(RSA512_KEY, ["example.com", "foo.example.com"])[0]
        self.assertEqual(
            get_sans_from_csr(result), ["example.com", "foo.example.com"])
        req = M2Crypto.X509.load_request_string(result)
        subject = req.get_subject().as_text()
        modulus = req.get_pubkey().get_modulus()
        self.assertEqual(
            subject, "C=US, ST=Michigan, L=Ann Arbor, O=EFF, OU=University"
                     " of Michigan, CN=example.com")
        self.assertEqual(
            modulus, "F4B61171513736BFAA95E79C11C5FC2705439E3786D57EEE72C0"
                     "9AB2EB993347B4F5C998B94CF12243233BFF71E0055CBD75D15CF"
                     "115F8BCD65A47E44E5CD133")


if __name__ == '__main__':
    unittest.main()
