# Copyright 2014 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import os
import shutil
import logging
from pathlib import Path

VERSION = '9c'
HASH = 'b2affe9a1688bd49fc033f4682c4a242d4ee612f1affaef532f5adcb4602efc4433c4a52a4b3d69e7440ff1f6413b1b041b419bc90efd6d697999961a9a6afb7'

settings = {"USE_LIBJPEG": False}


def needed(settings):
  return settings.USE_LIBJPEG


def get(ports, settings, shared):
  # Archive mirrored from http://www.ijg.org/files/jpegsrc.v9c.tar.gz.
  # We have issues where python urllib was not able to load from the www.ijg.org webserver
  # and was resulting in 403: Forbidden.
  ports.fetch_project('libjpeg', 'https://storage.googleapis.com/webassembly/emscripten-ports/jpegsrc.v9c.tar.gz', 'jpeg-9c', sha512hash=HASH)

  def create(final):
    logging.info('building port: libjpeg')

    source_path = os.path.join(ports.get_dir(), 'libjpeg', 'jpeg-9c')
    dest_path = ports.clear_project_build('libjpeg')
    shutil.copytree(source_path, dest_path)

    Path(dest_path, 'jconfig.h').write_text(jconfig_h)
    ports.install_headers(dest_path)

    ports.build_port(
      dest_path, final,
      exclude_files=[
        'ansi2knr.c', 'cjpeg.c', 'ckconfig.c', 'djpeg.c', 'example.c',
        'jmemansi.c', 'jmemdos.c', 'jmemmac.c', 'jmemname.c',
        'jpegtran.c', 'rdjpgcom.c', 'wrjpgcom.c',
      ]
    )

  return [shared.Cache.get_lib('libjpeg.a', create, what='port')]


def clear(ports, settings, shared):
  shared.Cache.erase_lib('libjpeg.a')


def process_args(ports):
  return []


def show():
  return 'libjpeg (USE_LIBJPEG=1; BSD license)'


jconfig_h = '''/* jconfig.h.  Generated from jconfig.cfg by configure.  */
/* jconfig.cfg --- source file edited by configure script */
/* see jconfig.txt for explanations */

#define HAVE_PROTOTYPES 1
#define HAVE_UNSIGNED_CHAR 1
#define HAVE_UNSIGNED_SHORT 1
/* #undef void */
/* #undef const */
/* #undef CHAR_IS_UNSIGNED */
#define HAVE_STDDEF_H 1
#define HAVE_STDLIB_H 1
#define HAVE_LOCALE_H 1
/* #undef NEED_BSD_STRINGS */
/* #undef NEED_SYS_TYPES_H */
/* #undef NEED_FAR_POINTERS */
/* #undef NEED_SHORT_EXTERNAL_NAMES */
/* Define this if you get warnings about undefined structures. */
/* #undef INCOMPLETE_TYPES_BROKEN */

/* Define "boolean" as unsigned char, not enum, on Windows systems. */
#ifdef _WIN32
#ifndef __RPCNDR_H__		/* don't conflict if rpcndr.h already read */
typedef unsigned char boolean;
#endif
#ifndef FALSE			/* in case these macros already exist */
#define FALSE	0		/* values of boolean */
#endif
#ifndef TRUE
#define TRUE	1
#endif
#define HAVE_BOOLEAN		/* prevent jmorecfg.h from redefining it */
#endif

#ifdef JPEG_INTERNALS

/* #undef RIGHT_SHIFT_IS_UNSIGNED */
#define INLINE __inline__
/* These are for configuring the JPEG memory manager. */
/* #undef DEFAULT_MAX_MEM */
/* #undef NO_MKTEMP */

#endif /* JPEG_INTERNALS */

#ifdef JPEG_CJPEG_DJPEG

#define BMP_SUPPORTED		/* BMP image file format */
#define GIF_SUPPORTED		/* GIF image file format */
#define PPM_SUPPORTED		/* PBMPLUS PPM/PGM image file format */
/* #undef RLE_SUPPORTED */
#define TARGA_SUPPORTED		/* Targa image file format */

/* #undef TWO_FILE_COMMANDLINE */
/* #undef NEED_SIGNAL_CATCHER */
/* #undef DONT_USE_B_MODE */

/* Define this if you want percent-done progress reports from cjpeg/djpeg. */
/* #undef PROGRESS_REPORT */

#endif /* JPEG_CJPEG_DJPEG */
'''
