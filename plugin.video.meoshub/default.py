# -*- coding: utf-8 -*-
"""MEOS Hub - plugin entry point (Kodi invokes this file directly)."""
import sys

from resources.lib import router

if __name__ == '__main__':
    router.run(sys.argv)
