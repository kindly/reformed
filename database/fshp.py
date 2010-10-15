"""Fairly Secure Hashed Passwords. A PBKDF1 similar implementation.

Fairly Secure Hashed Password (FSHP) is a salted, iteratively hashed
password hashing implementation.

Design principle is similar with PBKDF1 specification in RFC 2898
(a.k.a: PKCS #5: Password-Based Cryptography Specification Version 2.0)

FSHP allows choosing the salt length, number of iterations and the
underlying cryptographic hash function among SHA-1 and SHA-2 (256, 384, 512).

SECURITY:
Default FSHP1 uses 8 byte salts, with 4096 iterations of SHA-256 hashing.
  - 8 byte salt renders rainbow table attacks impractical by multiplying the
    required space with 2^64.
  - 4096 iterations causes brute force attacks to be fairly expensive.
  - There are no known attacks against SHA-256 to find collisions with
    a computational effort of fewer than 2^128 operations at the time of
    this release.

BASIC OPERATION:
  >>> fsh = fshp.crypt('OrpheanBeholderScryDoubt')
  >>> print fsh
  {FSHP1|8|4096}GVSUFDAjdh0vBosn1GUhzGLHP7BmkbCZVH/3TQqGIjADXpc+6NCg3g==
  >>> fshp.check('OrpheanBeholderScryDoubt', fsh)
  True

CUSTOMIZING THE CRYPT:
Let's set a higher password storage security baseline.
  - Increase the salt length from default 8 to 16.
  - Increase the hash rounds from default 4096 to 8192.
  - Select FSHP3 with SHA-512 as the underlying hash algorithm.

  >>> fsh = fshp.crypt('ExecuteOrder66', saltlen=16, rounds=8192, variant=3)
  >>> print fsh
  {FSHP3|16|8192}0aY7rZQ+/PR+Rd5/I9ssRM7cjguyT8ibypNaSp/U1uziNO3BVlg5qPUng+zHUDQC3ao/JbzOnIBUtAeWHEy7a2vZeZ7jAwyJJa2EqOsq4Io=

"""


import random
import hashlib
import base64
import re


__author__ = 'Berk D. Demir <bdd@mindcast.org>'
__license__ = """
Authors of this computer software disclaim their respective copyright
on the source code and related documentation, thus releasing their work
to Public Domain.

In case you are forced by your lawyer to get a copyright license,
you may contact any of the authors to get this software (and its related
documentation) with a BSD type license.
"""
__version__ = '0.2.1'


FSHP_META_FMTSTR = '{FSHP%d|%d|%d}'
FSHP_REGEX = """
^                               # BEGIN
\{                              # meta decorator, open
FSHP                            # fshp signature
(?P<variant>\d+)                # variant
\|                              # meta separator
(?P<saltlen>\d+)                # salt length
\|                              # meta separator
(?P<rounds>\d+)                 # number of hash iterations
\}                              # meta decorator, close
(?P<b64saltdigest>[\d\w\+\/=]+) # Base64 encoded 'salt' + 'digest'
$                               # END
"""

def crypt(passwd, salt=None, saltlen=8, rounds=4096, variant=1):
    """Return an FSHP hash string of byte string ``passwd``.

    ``salt`` is a byte string. If ``None``, a random salt will be
    generated with respect to ``saltlen`` bytes

    ``variant`` selects the underlying hash function to be used.
        0: sha1   (not recommended)
        1: sha256 (default)
        2: sha384
        3: sha512
    """

    # Type cast to integer.
    saltlen, rounds, variant = map(int, (saltlen, rounds, variant))

    # Ensure we have sane values for salt length and rounds.
    if saltlen < 0: saltlen = 0
    if rounds  < 1: rounds  = 1

    if salt is None:
        salt = ''
        for i in range(saltlen):
            salt += chr(random.randint(0, 127))
    else:
        saltlen = len(salt)

    salt = unicode(salt)

    algorithm = { 0: 'sha1', 1: 'sha256', 2: 'sha384', 3: 'sha512' }
    if not algorithm.has_key(variant):
        raise Exception("Unsupported FSHP variant '%d'" % variant)

    h = hashlib.new(algorithm[variant])
    h.update(salt + passwd)
    digest = h.digest()
    for i in range(1, rounds):
        h = hashlib.new(algorithm[variant])
        h.update(digest)
        digest = h.digest()

    meta = FSHP_META_FMTSTR % (variant, saltlen, rounds)
    b64saltdigest = base64.encodestring(salt.encode("ascii") + digest).replace('\n','')

    return meta + b64saltdigest

def check(passwd, ciphertext):
    """Check if ``ciphertext`` is an FSHP hash of ``password``.

    Return value is boolean.
    """

    # Regular expression match. Yes, it's ugly.
    r = re.compile(FSHP_REGEX, re.VERBOSE)
    match = r.match(ciphertext)
    if match is None:
        return False
    m = match.groupdict()

    # Decode base64 string, read first 'saltlen' bytes to get 'salt'.
    salt = base64.decodestring(m['b64saltdigest'])[:int(m['saltlen'])]
    salt = unicode(salt)

    return crypt(passwd, salt,
                 m['saltlen'], m['rounds'], m['variant']) == ciphertext
