from connexion.exceptions import ValidationError, ProblemException, BadRequestProblem, NonConformingResponse, \
    UnsupportedMediaTypeProblem, AuthenticationProblem
from werkzeug.exceptions import default_exceptions
from swagger_server.utils.transactions.transaction import Transaction as transactionUuids
import json

from swagger_server.models import ResponseError

common_exception = [
    AuthenticationProblem,
    UnsupportedMediaTypeProblem,
    ProblemException,
    BadRequestProblem,
    NonConformingResponse,
    ValidationError
]

transaction: transactionUuids


def add_handler(app):
    for ex in common_exception:
        app.add_error_handler(ex, handle_common_exception)

    for ex in default_exceptions:
        app.add_error_handler(ex, handle_default_exception)

    """if code_exception:
        for ex in code_exception:
            app.add_error_handler(ex.error, ex.handler)
    """

def handle_default_exception(e):
    response = e.get_response()

    response.content_type = "application/json"

    response.data = json.dumps({
        "code": -1,
        "message": str(e.code) + " " + e.name + " " + e.description,
    })

    return response


def handle_common_exception(e):

    error_response = ResponseError(
        error_code=-1,
        message=str(e.status) + " " + e.title + " " + e.detail,
        external_transaction_id=transactionUuids().id_external_transaction,
        internal_transaction_id=transactionUuids().id_internal_transaction
    )

    return error_response.to_dict()
