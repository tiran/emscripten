# Copyright 2014 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import os
import shutil

VERSION = '1.0.6'
HASH = '512cbfde5144067f677496452f3335e9368fd5d7564899cb49e77847b9ae7dca598218276637cbf5ec524523be1e8ace4ad36a148ef7f4badf3f6d5a002a4bb2'

settings = {"USE_BZIP2": False}


def needed(settings):
  return settings.USE_BZIP2


def get(ports, settings, shared):
  ports.fetch_project('bzip2', 'https://github.com/emscripten-ports/bzip2/archive/' + VERSION + '.zip', 'bzip2-' + VERSION, sha512hash=HASH)

  def create(final):
    dest_path = ports.clear_project_build('bzip2')
    source_path = os.path.join(ports.get_dir(), 'bzip2', 'bzip2-' + VERSION)
    shutil.copytree(source_path, dest_path)

    # build
    srcs = [
      'blocksort.c', 'compress.c', 'decompress.c', 'huffman.c',
      'randtable.c', 'bzlib.c', 'crctable.c',
    ]
    commands = []
    o_s = []
    for src in srcs:
      o = os.path.join(dest_path, shared.replace_suffix(src, '.o'))
      shared.safe_ensure_dirs(os.path.dirname(o))
      commands.append([shared.EMCC, '-c', os.path.join(dest_path, src), '-O2', '-o', o, '-I' + dest_path, '-w', ])
      o_s.append(o)
    ports.run_commands(commands)

    ports.create_lib(final, o_s)
    ports.install_headers(source_path)

  return [shared.Cache.get_lib('libbz2.a', create, what='port')]


def clear(ports, settings, shared):
  shared.Cache.erase_lib('libbz2.a')


def process_args(ports):
  return []


def show():
  return 'bzip2 (USE_BZIP2=1; BSD license)'
