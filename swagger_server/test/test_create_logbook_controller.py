# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.request_post_logbook_entry import RequestPostLogbookEntry  # noqa: E501
from swagger_server.models.request_post_logbook_out import RequestPostLogbookOut  # noqa: E501
from swagger_server.models.response_error import ResponseError  # noqa: E501
from swagger_server.models.response_post_logbook_entry import ResponsePostLogbookEntry  # noqa: E501
from swagger_server.models.response_post_logbook_out import ResponsePostLogbookOut  # noqa: E501
from swagger_server.test import BaseTestCase


class TestCreateLogbookController(BaseTestCase):
    """CreateLogbookController integration test stubs"""

    def test_post_logbook_entry(self):
        """Test case for post_logbook_entry

        Guarda la bitacora de ingreso en la base de datos.
        """
        body = RequestPostLogbookEntry()
        response = self.client.open(
            '/post/logbook-entry',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_post_logbook_out(self):
        """Test case for post_logbook_out

        Guarda la bitacora de salida en la base de datos.
        """
        body = RequestPostLogbookOut()
        response = self.client.open(
            '/post/logbook-out',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
