#!/usr/bin/env python3
import logging
import os
import connexion
from swagger_server import encoder
from connexion.resolver import MethodViewResolver
from swagger_server.resources.db import db
from flask_cors import CORS
from flask import request
from urllib.parse import quote
from swagger_server.config.access import access
from swagger_server.utils.logs.logging import log
from swagger_server.models.response_error import ResponseError
from swagger_server.utils.transactions.transaction import Transaction as transactionUuids
from urllib.parse import urlparse
from swagger_server.utils.utils import format_uri_connection
from swagger_server.exception.register import add_handler

from swagger_server.utils.log import configure_logger
from swagger_server.encoder import JSONEncoder

config = access()

log()

transaction: transactionUuids

# Configurar el logger de loguru
configure_logger()

# VARIABLES
MS_NAME: str = 'zent-logbook-ms'
MS_PORT: int = 2120


# ------------------------------------------------------------------------

def get_transaction():
    return transaction


def global_transaction_uuids():
    parsed_uri = urlparse(request.base_url)
    logging.info(parsed_uri.path)
    if parsed_uri.path in (
            "/rest/z-logbook-api/v1.0/post/logbook-entry",
            "/rest/z-logbook-api/v1.0/post/logbook-out"
    ):
        global transaction
        transaction = transactionUuids()

        transaction.id_external_transaction = request.json['externalTransactionId']
        transaction.channel = request.json['channel']


def create_app():
    configure_logger()

    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml',
                arguments={
                    'title': 'zent-logbook-api'
                },
                pythonic_params=True,
                resolver=MethodViewResolver('swagger_server.controllers')
                )

    user = config["DB"]["POSTGRESQL"]["USER"]
    host = config["DB"]["POSTGRESQL"]["HOST"]
    port = config["DB"]["POSTGRESQL"]["PORT"]
    database = config["DB"]["POSTGRESQL"]["DB"]
    password = quote(config["DB"]["POSTGRESQL"]["PASSWORD"], safe='')
    string_connection = (
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    )

    app.app.config["SQLALCHEMY_DATABASE_URI"] = string_connection
    app.app.config["SQLALCHEMY_ENGINE_OPTIONS"] = config["DB"]["SQLALCHEMY_ENGINE_OPTIONS"]
    db.init_app(app.app)
    CORS(app.app, resources={r"/*": {"origins": "*"}})
    add_handler(app)

    app.app.before_request(global_transaction_uuids)

    add_handler(app)

    return app


def create_app_test():
    app = create_app()

    driver = os.getenv("DATABASE_DRIVER", "postgresql")
    app.app.config["SQLALCHEMY_DATABASE_URI"] = format_uri_connection(access()["DB"][driver])
    app.app.config["SQLALCHEMY_ENGINE_OPTIONS"] = access()["DB"]["SQLALCHEMY_ENGINE_OPTIONS"]

    return app.app


if __name__ == '__main__':
    app = create_app()
    app.run(port=MS_PORT, debug=False)  # Para hacer debug con el IDE, se debe colocar en "False"
