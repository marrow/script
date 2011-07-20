# encoding: utf-8

"""Release information about Marrow Script."""

from collections import namedtuple


__all__ = ['version_info', 'version']


version_info = namedtuple('version_info', ('major', 'minor', 'micro', 'releaselevel', 'serial'))(2, 0, 0, 'beta', 1)

version = ".".join([str(i) for i in version_info[:3]]) + (version_info.releaselevel[0] + str(version_info.serial)) if version_info.releaselevel != 'final' else ''
