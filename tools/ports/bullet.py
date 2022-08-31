# Copyright 2015 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import logging
import os
import shutil

TAG = 'version_1'
HASH = '3922486816cf7d99ee02c3c1ef63d94290e8ed304016dd9927137d04206e7674d9df8773a4abb7bb57783d0a5107ad0f893aa87acfb34f7b316eec22ca55a536'

settings = {"USE_BULLET": False}


def needed(settings):
  return settings.USE_BULLET == 1


def get(ports, settings, shared):
  ports.fetch_project('bullet', 'https://github.com/emscripten-ports/bullet/archive/' + TAG + '.zip', 'Bullet-' + TAG, sha512hash=HASH)

  def create(final):
    logging.info('building port: bullet')

    source_path = os.path.join(ports.get_dir(), 'bullet', 'Bullet-' + TAG)
    dest_path = ports.clear_project_build('bullet')
    shutil.copytree(source_path, dest_path)
    src_path = os.path.join(dest_path, 'bullet', 'src')
    src_path = os.path.join(dest_path, 'bullet', 'src')

    dest_include_path = ports.get_include_dir('bullet')
    for base, _, files in os.walk(src_path):
      for f in files:
        if shared.suffix(f) != '.h':
          continue
        fullpath = os.path.join(base, f)
        relpath = os.path.relpath(fullpath, src_path)
        target = os.path.join(dest_include_path, relpath)
        shared.safe_ensure_dirs(os.path.dirname(target))
        shutil.copyfile(fullpath, target)

    includes = []
    for base, dirs, _ in os.walk(src_path, topdown=False):
      for dir in dirs:
        includes.append(os.path.join(base, dir))

    ports.build_port(src_path, final, includes=includes, exclude_dirs=['MiniCL'])

  return [shared.Cache.get_lib('libbullet.a', create)]


def clear(ports, settings, shared):
  shared.Cache.erase_lib('libbullet.a')


def process_args(ports):
  return ['-I' + ports.get_include_dir('bullet')]


def show():
  return 'bullet (USE_BULLET=1; zlib license)'
