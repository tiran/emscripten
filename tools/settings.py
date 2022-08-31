# Copyright 2021 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import difflib
import os
import re

from .utils import path_from_root, exit_with_error
from . import diagnostics

# Subset of settings that take a memory size (i.e. 1Gb, 64kb etc)
MEM_SIZE_SETTINGS = {
    'TOTAL_STACK',
    'INITIAL_MEMORY',
    'MEMORY_GROWTH_LINEAR_STEP',
    'MEMORY_GROWTH_GEOMETRIC_CAP',
    'GL_MAX_TEMP_BUFFER_SIZE',
    'MAXIMUM_MEMORY',
    'DEFAULT_PTHREAD_STACK_SIZE'
}

# PORTS_SETTINGS are now provided by each individual port.

# Subset of settings that apply at compile time.
# (Keep in sync with [compile] comments in settings.js)
COMPILE_TIME_SETTINGS = {
    'MEMORY64',
    'INLINING_LIMIT',
    'DISABLE_EXCEPTION_CATCHING',
    'DISABLE_EXCEPTION_THROWING',
    'MAIN_MODULE',
    'SIDE_MODULE',
    'RELOCATABLE',
    'STRICT',
    'EMSCRIPTEN_TRACING',
    'USE_PTHREADS',
    'SHARED_MEMORY',
    'SUPPORT_LONGJMP',
    'DEFAULT_TO_CXX',
    'WASM_OBJECT_FILES',
    'WASM_WORKERS',

    # Internal settings used during compilation
    'EXCEPTION_CATCHING_ALLOWED',
    'WASM_EXCEPTIONS',
    'LTO',
    'OPT_LEVEL',
    'DEBUG_LEVEL',

    # This is legacy setting that we happen to handle very early on
    'RUNTIME_LINKED_LIBS',
    # TODO: should not be here
    'AUTO_ARCHIVE_INDEXES',
    'DEFAULT_LIBRARY_FUNCS_TO_INCLUDE',
}


class SettingsManager:
  attrs = {}
  types = {}
  allowed_settings = set()
  legacy_settings = {}
  alt_names = {}
  internal_settings = set()

  def __init__(self):
    self.attrs.clear()
    self.legacy_settings.clear()
    self.alt_names.clear()
    self.internal_settings.clear()
    self.allowed_settings.clear()

    # Load the JS defaults into python.
    def read_js_settings(filename, attrs):
      with open(filename) as fh:
        settings = fh.read()
      # Use a bunch of regexs to convert the file from JS to python
      # TODO(sbc): This is kind hacky and we should probably covert
      # this file in format that python can read directly (since we
      # no longer read this file from JS at all).
      settings = settings.replace('//', '#')
      settings = re.sub(r'var ([\w\d]+)', r'attrs["\1"]', settings)
      settings = re.sub(r'=\s+false\s*;', '= False', settings)
      settings = re.sub(r'=\s+true\s*;', '= True', settings)
      exec(settings, {'attrs': attrs})

    internal_attrs = {}
    read_js_settings(path_from_root('src/settings.js'), self.attrs)
    read_js_settings(path_from_root('src/settings_internal.js'), internal_attrs)
    self.attrs.update(internal_attrs)
    self.infer_types()

    if 'EMCC_STRICT' in os.environ:
      self.attrs['STRICT'] = int(os.environ.get('EMCC_STRICT'))

    # Special handling for LEGACY_SETTINGS.  See src/setting.js for more
    # details
    for legacy in self.attrs['LEGACY_SETTINGS']:
      if len(legacy) == 2:
        name, new_name = legacy
        self.legacy_settings[name] = (None, 'setting renamed to ' + new_name)
        self.alt_names[name] = new_name
        self.alt_names[new_name] = name
        default_value = self.attrs[new_name]
      else:
        name, fixed_values, err = legacy
        self.legacy_settings[name] = (fixed_values, err)
        default_value = fixed_values[0]
      assert name not in self.attrs, 'legacy setting (%s) cannot also be a regular setting' % name
      if not self.attrs['STRICT']:
        self.attrs[name] = default_value

    self.internal_settings.update(internal_attrs.keys())

  def infer_types(self):
    for key, value in self.attrs.items():
      self.types[key] = type(value)

  def dict(self):
    return self.attrs

  def keys(self):
    return self.attrs.keys()

  def limit_settings(self, allowed):
    self.allowed_settings.clear()
    if allowed:
      self.allowed_settings.update(allowed)

  def update_port_settings(self, port_setting):
    self.attrs.update(port_setting)
    # All port-related settings are valid at compile time
    COMPILE_TIME_SETTINGS.update(set(port_setting))

  def __getattr__(self, attr):
    if self.allowed_settings:
      assert attr in self.allowed_settings, f"internal error: attempt to read setting '{attr}' while in limited settings mode"

    if attr in self.attrs:
      return self.attrs[attr]
    else:
      raise AttributeError(f"no such setting: '{attr}'")

  def __setattr__(self, name, value):
    if self.allowed_settings:
      assert name in self.allowed_settings, f"internal error: attempt to write setting '{name}' while in limited settings mode"

    if name == 'STRICT' and value:
      for a in self.legacy_settings:
        self.attrs.pop(a, None)

    if name in self.legacy_settings:
      # TODO(sbc): Rather then special case this we should have STRICT turn on the
      # legacy-settings warning below
      if self.attrs['STRICT']:
        exit_with_error('legacy setting used in strict mode: %s', name)
      fixed_values, error_message = self.legacy_settings[name]
      if fixed_values and value not in fixed_values:
        exit_with_error('Invalid command line option -s ' + name + '=' + str(value) + ': ' + error_message)
      diagnostics.warning('legacy-settings', 'use of legacy setting: %s (%s)', name, error_message)

    if name in self.alt_names:
      alt_name = self.alt_names[name]
      self.attrs[alt_name] = value

    if name not in self.attrs:
      msg = "Attempt to set a non-existent setting: '%s'\n" % name
      valid_keys = set(self.attrs.keys()).difference(self.internal_settings)
      suggestions = difflib.get_close_matches(name, valid_keys)
      suggestions = [s for s in suggestions if s not in self.legacy_settings]
      suggestions = ', '.join(suggestions)
      if suggestions:
        msg += ' - did you mean one of %s?\n' % suggestions
      msg += " - perhaps a typo in emcc's  -sX=Y  notation?\n"
      msg += ' - (see src/settings.js for valid values)'
      exit_with_error(msg)

    self.check_type(name, value)
    self.attrs[name] = value

  def check_type(self, name, value):
    if name in ('SUPPORT_LONGJMP', 'PTHREAD_POOL_SIZE', 'SEPARATE_DWARF', 'LTO'):
      return
    expected_type = self.types.get(name)
    if not expected_type:
      return
    # Allow itegers 1 and 0 for type `bool`
    if expected_type == bool:
      if value in (1, 0):
        value = bool(value)
      if value in ('True', 'False', 'true', 'false'):
        exit_with_error('attempt to set `%s` to `%s`; use 1/0 to set boolean settings' % (name, value))
    if type(value) != expected_type:
      exit_with_error('setting `%s` expects `%s` but got `%s`' % (name, expected_type.__name__, type(value).__name__))

  def __getitem__(self, key):
    return self.attrs[key]

  def __setitem__(self, key, value):
    self.attrs[key] = value


settings = SettingsManager()
