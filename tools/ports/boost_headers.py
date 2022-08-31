# Copyright 2015 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import logging
import os

TAG = '1.75.0'
HASH = '8c38be1ebef1b8ada358ad6b7c9ec17f5e0a300e8085db3473a13e19712c95eeb3c3defacd3c53482eb96368987c4b022efa8da2aac2431a154e40153d3c3dcd'

settings = {"USE_BOOST_HEADERS": False}


def needed(settings):
  return settings.USE_BOOST_HEADERS == 1


def get(ports, settings, shared):
  ports.fetch_project('boost_headers', 'https://github.com/emscripten-ports/boost/releases/download/boost-1.75.0/boost-headers-' + TAG + '.zip',
                      'boost', sha512hash=HASH)

  def create(final):
    logging.info('building port: boost_headers')
    build_dir = ports.clear_project_build('boost_headers')

    # includes
    source_path_include = os.path.join(ports.get_dir(), 'boost_headers', 'boost')
    ports.install_header_dir(source_path_include, 'boost')

    # write out a dummy cpp file, to create an empty library
    # this is needed as emscripted ports expect this, even if it is not used
    dummy_file = os.path.join(build_dir, 'dummy.cpp')
    shared.safe_ensure_dirs(os.path.dirname(dummy_file))
    with open(dummy_file, 'w') as f:
      f.write('static void dummy() {}')

    commands = []
    o_s = []
    obj = dummy_file + '.o'
    command = [shared.EMCC, '-c', dummy_file, '-o', obj]
    commands.append(command)
    ports.run_commands(commands)
    o_s.append(obj)
    ports.create_lib(final, o_s)

  return [shared.Cache.get_lib('libboost_headers.a', create, what='port')]


def clear(ports, settings, shared):
  shared.Cache.erase_lib('libboost_headers.a')


def process_args(ports):
  return ['-DBOOST_ALL_NO_LIB']


def show():
  return 'Boost headers v1.70.0 (USE_BOOST_HEADERS=1; Boost license)'
