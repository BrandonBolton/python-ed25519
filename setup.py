from __future__ import print_function
import sys, os, timeit
from setuptools import setup, Extension, Command
from sysconfig import get_platform
import versioneer
import unittest

LONG_DESCRIPTION = """\
Python bindings to the Ed25519 public-key signature system.

This offers a comfortable python interface to a C implementation of the
Ed25519 public-key signature system (http://ed25519.cr.yp.to/), using the
portable 'ref' code from the 'SUPERCOP' benchmarking suite.

This system provides high (128-bit) security, short (32-byte) keys, short
(64-byte) signatures, and fast (2-6ms) operation. Please see the README for
more details.

## Not Recommended For New Applications: Use pynacl Instead

For new applications, I recommend you use
[`pynacl`](https://github.com/pyca/pynacl) instead of this repository.
`PyNaCl` is larger and takes longer to build (it contains the complete
NaCl/libsodium library, not just the ed25519 portion), but it is
well-maintained by the diligent and conscientious PyCA team, whereas I've
allowed this repository to languish. `PyNaCl` is also about 10-20 times
faster. A guide for migration fron `python-ed25519` to `PyNaCl` is included
below.
"""

sources = ["src/ed25519-glue/ed25519module.c"]
sources.extend(["src/ed25519-supercop-ref/" + s
                for s in os.listdir("src/ed25519-supercop-ref")
                if s.endswith(".c") and s != "test.c"])

m = Extension("ed25519._ed25519",
              include_dirs=["src/ed25519-supercop-ref"], sources=sources)

commands = versioneer.get_cmdclass().copy()


class Test(Command):
    description = "run tests"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def setup_path(self):
        # copied from distutils/command/build.py
        self.plat_name = get_platform()
        plat_specifier = ".%s-%s" % (self.plat_name, sys.version[0:3])
        self.build_lib = os.path.join("build", "lib" + plat_specifier)
        sys.path.insert(0, self.build_lib)

    def run(self):
        self.setup_path()
        test_loader = unittest.defaultTestLoader
        test_runner = unittest.TextTestRunner(verbosity=2)
        test_suite = test_loader.loadTestsFromName("ed25519.test_ed25519")

        result = test_runner.run(test_suite)
        if not result.wasSuccessful():
            sys.exit(1)
        sys.exit(0)


commands["test"] = Test


class KnownAnswerTest(Test):
    description = "run known-answer-tests"

    def run(self):
        self.setup_path()
        import unittest
        test = unittest.defaultTestLoader.loadTestsFromName("test_ed25519_kat")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test)
        sys.exit(not result.wasSuccessful())


commands["test_kat"] = KnownAnswerTest


class Speed(Test):
    description = "run benchmark suite"

    def run(self):
        self.setup_path()

        def do(setup_statements, statement):
            # extracted from timeit.py
            t = timeit.Timer(stmt=statement,
                             setup="\n".join(setup_statements))
            # determine number so that 0.2 <= total time < 2.0
            for i in range(1, 10):
                number = 10 ** i
                x = t.timeit(number)
                if x >= 0.2:
                    break
            return x / number

        def abbrev(t):
            if t > 1.0:
                return "%.3fs" % t
            if t > 1e-3:
                return "%.2fms" % (t * 1e3)
            return "%.2fus" % (t * 1e6)

        S1 = "import ed25519; msg=b'hello world'"
        S2 = "sk,vk = ed25519.create_keypair()"
        S3 = "sig = sk.sign(msg)"
        S4 = "vk.verify(sig, msg)"

        generate = do([S1], S2)
        sign = do([S1, S2], S3)
        verify = do([S1, S2, S3], S4)

        print("generate: %s" % abbrev(generate))
        print("sign: %s" % abbrev(sign))
        print("verify: %s" % abbrev(verify))


commands["speed"] = Speed

setup(name="python-ed25519",
      version='1.0',
      description="Ed25519 public-key signatures",
      long_description=LONG_DESCRIPTION,
      long_description_content_type="text/markdown",
      author="Brandon Bolton",
      author_email="email@brandonbolton.com",
      license="MIT",
      url="https://github.com/BrandonBolton/python-ed25519",
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.12",
          "Topic :: Security :: Cryptography",
      ],
      ext_modules=[m],
      packages=["ed25519"],
      package_dir={"ed25519": "src/ed25519"},
      scripts=["bin/edsig"],
      cmdclass=commands,
      )
