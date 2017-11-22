#!/usr/bin/env python
# Copyright (c) 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit Tests for auth.py"""

import __builtin__
import datetime
import json
import logging
import os
import unittest
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from testing_support import auto_stub
from third_party import httplib2
from third_party import mock

import auth


class TestGetLuciContextAccessToken(auto_stub.TestCase):
  def _mock_local_auth(self, account_id, secret, rpc_port):
    default_test_path = 'default/test/path'
    self.mock(os, 'environ', mock.Mock())
    os.environ.return_value(default_test_path)
    local_auth_dict = {
      'default_account_id': account_id,
      'secret': secret,
      'rpc_port': rpc_port,
    }
    self.mock(__builtin__, 'open',
        mock.mock_open(read_data=json.dumps({'local_auth': local_auth_dict})))

  def _mock_loc_server_resp(self, status, content):
    mock_resp = mock.Mock()
    mock_resp.status = status
    self.mock(httplib2.Http, 'request', mock.Mock())
    httplib2.Http.request.return_value = (mock_resp, content)

  def testCorrectLocalAuthFormat(self):
    self._mock_local_auth('dead', 'beef', 10)
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    resp_content = {
      'error_code': None,
      'error_message': None,
      'access_token': 'token',
      'expiry': time.mktime(expiry_time.timetuple()),
    }
    self._mock_loc_server_resp(200, json.dumps(resp_content))
    token = auth.get_luci_context_access_token()
    self.assertEquals(token.token, 'token')

  def testIncorrectPortFormat(self):
    self._mock_local_auth('foo', 'bar', 'bar')
    self.assertRaises(auth.LuciContextAuthError,
        auth.get_luci_context_access_token)

  def testNoAccountId(self):
    self._mock_local_auth(None, 'bar', 10)
    token = auth.get_luci_context_access_token()
    self.assertIsNone(token)

  def testExpiredToken(self):
    self._mock_local_auth('dead', 'beef', 10)
    resp_content = {
      'error_code': None,
      'error_message': None,
      'access_token': 'token',
      'expiry': time.mktime(datetime.datetime.min.timetuple()),
    }
    self._mock_loc_server_resp(200, json.dumps(resp_content))
    self.assertRaises(auth.LuciContextAuthError,
        auth.get_luci_context_access_token)

  def testIncorrectExpiryFormatReturned(self):
    self._mock_local_auth('dead', 'beef', 10)
    resp_content = {
      'error_code': None,
      'error_message': None,
      'access_token': 'token',
      'expiry': 'dead',
    }
    self._mock_loc_server_resp(200, json.dumps(resp_content))
    self.assertRaises(auth.LuciContextAuthError,
        auth.get_luci_context_access_token)

  def testIncorrectResponseContentFormat(self):
    self._mock_local_auth('dead', 'beef', 10)
    self._mock_loc_server_resp(200, '5')
    self.assertRaises(auth.LuciContextAuthError,
        auth.get_luci_context_access_token)


if __name__ == '__main__':
  if '-v' in sys.argv:
    logging.basicConfig(level=logging.DEBUG)
  unittest.main()
