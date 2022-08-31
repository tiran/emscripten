# Copyright 2016 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import os
import logging

TAG = 'version_2'
HASH = '317b22ad9b6b2f7b40fac7b7c426da2fa2da1803bbe58d480631f1e5b190d730763f2768c77c72affa806c69a1e703f401b15a1be3ec611cd259950d5ebc3711'

deps = ['sdl2']
settings = {"USE_SDL_NET": False}


def needed(settings):
  return settings.USE_SDL_NET == 2


def get(ports, settings, shared):
  sdl_build = os.path.join(ports.get_build_dir(), 'sdl2')
  assert os.path.exists(sdl_build), 'You must use SDL2 to use SDL2_net'
  ports.fetch_project('sdl2_net', 'https://github.com/emscripten-ports/SDL2_net/archive/' + TAG + '.zip', 'SDL2_net-' + TAG, sha512hash=HASH)

  def create(final):
    logging.info('building port: sdl2_net')
    src_dir = os.path.join(ports.get_dir(), 'sdl2_net', 'SDL2_net-' + TAG)
    ports.install_headers(src_dir, target='SDL2')
    srcs = 'SDLnet.c SDLnetselect.c SDLnetTCP.c SDLnetUDP.c'.split()
    commands = []
    o_s = []
    build_dir = ports.clear_project_build('sdl2_net')
    shared.safe_ensure_dirs(build_dir)
    for src in srcs:
      o = os.path.join(build_dir, shared.replace_suffix(src, '.o'))
      commands.append([shared.EMCC, '-c', os.path.join(src_dir, src),
                       '-O2', '-sUSE_SDL=2', '-o', o, '-w'])
      o_s.append(o)
    ports.run_commands(commands)
    ports.create_lib(final, o_s)

  return [shared.Cache.get_lib('libSDL2_net.a', create, what='port')]


def clear(ports, settings, shared):
  shared.Cache.erase_lib('libSDL2_net.a')


def process_dependencies(settings):
  settings.USE_SDL = 2


def process_args(ports):
  return []


def show():
  return 'SDL2_net (zlib license)'
