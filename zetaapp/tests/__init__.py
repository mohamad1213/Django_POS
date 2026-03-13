import unittest

def discover_tests():
    return unittest.defaultTestLoader.discover(__name__)
