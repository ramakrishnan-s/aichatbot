import json

from flask import Response


def build_json(result):
    return Response(response=json.dumps(result),
                    status=200,
                    mimetype="application/json")


def sent_json(result):
    return Response(response=result,
                    status=200,
                    mimetype="application/json")


def sent_ok():
    return Response(response=json.dumps({"result": True}),
                    status=200,
                    mimetype="application/json")


def sent_plain_text(result):
    return Response(response=result.strip(), status=200, mimetype="text")


def sent_error(result, error_code):
    return Response(response=json.dumps({"result": False}),
                    status=error_code,
                    mimetype="application/json")


def sent_error_not_found(result):
    return Response(response=json.dumps({"result": False}),
                    status=404,
                    mimetype="application/json")