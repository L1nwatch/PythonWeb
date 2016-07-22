#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
对首页视图进行单元测试
"""
from django.test import TestCase

__author__ = '__L1n__w@tch'


class SmokeTest(TestCase):
    def test_bad_maths(self):
        self.assertEqual(1 + 1, 3)


if __name__ == "__main__":
    pass
