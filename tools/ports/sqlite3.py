# Copyright 2022 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import os
import shutil
import logging

# sqlite amalgamation download URL uses relase year and tag
# 2022  and (3, 38, 5) -> '/2022/sqlite-amalgamation-3380500.zip'
VERSION = (3, 39, 0)
VERSION_YEAR = 2022
HASH = 'cbaf4adb3e404d9aa403b34f133c5beca5f641ae1e23f84dbb021da1fb9efdc7c56b5922eb533ae5cb6d26410ac60cb3f026085591bc83ebc1c225aed0cf37ca'

deps = []
settings = {"USE_SQLITE3": False}
variants = {'sqlite3-mt': {'USE_PTHREADS': 1}}


def needed(settings):
  return settings.USE_SQLITE3


def get_lib_name(settings):
  return 'libsqlite3' + ('-mt' if settings.USE_PTHREADS else '') + '.a'


def get(ports, settings, shared):
  release = f'sqlite-amalgamation-{VERSION[0]}{VERSION[1]:02}{VERSION[2]:02}00'
  # TODO: Fetch the file from an emscripten-hosted mirror.
  ports.fetch_project('sqlite3', f'https://www.sqlite.org/{VERSION_YEAR}/{release}.zip', release, sha512hash=HASH)

  def create(final):
    logging.info('building port: libsqlite3')

    source_path = os.path.join(ports.get_dir(), 'sqlite3', release)
    dest_path = ports.clear_project_build('sqlite3')

    shutil.copytree(source_path, dest_path)

    ports.install_headers(dest_path)

    # flags are based on sqlite-autoconf output.
    # SQLITE_HAVE_ZLIB is only used by shell.c
    flags = [
      '-DSTDC_HEADERS=1',
      '-DHAVE_SYS_TYPES_H=1',
      '-DHAVE_SYS_STAT_H=1',
      '-DHAVE_STDLIB_H=1',
      '-DHAVE_STRING_H=1',
      '-DHAVE_MEMORY_H=1',
      '-DHAVE_STRINGS_H=1',
      '-DHAVE_INTTYPES_H=1',
      '-DHAVE_STDINT_H=1',
      '-DHAVE_UNISTD_H=1',
      '-DHAVE_FDATASYNC=1',
      '-DHAVE_USLEEP=1',
      '-DHAVE_LOCALTIME_R=1',
      '-DHAVE_GMTIME_R=1',
      '-DHAVE_DECL_STRERROR_R=1',
      '-DHAVE_STRERROR_R=1',
      '-DHAVE_POSIX_FALLOCATE=1',
      '-DSQLITE_OMIT_LOAD_EXTENSION=1',
      '-DSQLITE_ENABLE_MATH_FUNCTIONS=1',
      '-DSQLITE_ENABLE_FTS4=1',
      '-DSQLITE_ENABLE_FTS5=1',
      '-DSQLITE_ENABLE_RTREE=1',
      '-DSQLITE_ENABLE_GEOPOLY=1',
      '-DSQLITE_OMIT_POPEN=1',
    ]
    if settings.USE_PTHREADS:
      flags += [
        '-sUSE_PTHREADS',
        '-DSQLITE_THREADSAFE=1',
      ]
    else:
      flags += ['-DSQLITE_THREADSAFE=0']

    ports.build_port(dest_path, final, flags=flags, exclude_files=['shell.c'])

  return [shared.Cache.get_lib(get_lib_name(settings), create, what='port')]


def clear(ports, settings, shared):
  shared.Cache.erase_lib(get_lib_name(settings))


def process_args(ports):
  return []


def show():
  return 'sqlite (USE_SQLITE3=1); public domain)'
