# -*- coding: utf-8 -*-
import copy
import json
from flask import Blueprint, request, abort
from jinja2 import Template
from flask import current_app as app
from mongoengine import DoesNotExist

from app.agents.models import Bot
from app.commons import build_response
from app.endpoint.utils import SilentUndefined
from app.endpoint.utils import call_api
from app.endpoint.utils import get_synonyms
from app.endpoint.utils import split_sentence
from app.intents.models import Intent
from app.nlu.classifiers.sklearn_intent_classifer import \
    SklearnIntentClassifier
from app.nlu.entity_extractor import EntityExtractor

endpoint = Blueprint('api', __name__, url_prefix='/api')
sentence_classifier = SklearnIntentClassifier()
synonyms = None
entity_extraction = None


@endpoint.route('/v1', methods=['POST'])
def api():
    """
    Endpoint to Converse with the Chatbot.
    Chat context is maintained by exchanging the payload between client and bot.
    :param :
    :return json:
    """
    intent_id = None
    intent = None
    request_json = request.get_json(silent=True)
    print(request_json)
    result_json = copy.deepcopy(request_json)
    enterprise_name = request_json.get("enterprise_name")
    bot_name = request_json.get("bot_name")
    if request_json:
        context = {"context": request_json["context"]}

        sequence_id = request_json.get("sequence_id")
        sequence_id = sequence_id + 1
        result_json["sequence_id"] = sequence_id
        # check if input method is event or raw text
        if request_json.get("input", "").startswith("/"):
            intent_id = request_json.get("input").split("/")[1]
            confidence = 1
        else:
            intent_id, confidence, suggestions = predict(request_json)

        app.logger.info("intent_id => %s" % intent_id)
        try:
            intent = Intent.objects.get(enterprise_name=enterprise_name, bot_name=bot_name, intentId=intent_id)
            if intent_id is not None and bot_name is not None and enterprise_name is not None:
                intent = Intent.objects.get(intentId=intent_id, enterprise_name=enterprise_name, bot_name=bot_name)
                # set intent as fallback intent
                if intent is None:
                    intent = Intent.objects.get(intentId=app.config["DEFAULT_FALLBACK_INTENT_NAME"],
                                                enterprise_name=enterprise_name, bot_name=bot_name)
        except DoesNotExist:
            intent = Intent.objects.get(intentId=app.config["DEFAULT_FALLBACK_INTENT_NAME"],
                                        enterprise_name=enterprise_name, bot_name=bot_name)
        except Exception as e:
            intent = Intent.objects.get(intentId=app.config["DEFAULT_FALLBACK_INTENT_NAME"],
                                        enterprise_name=enterprise_name, bot_name=bot_name)

        parameters = []
        if intent.parameters:
            parameters = intent.parameters
            result_json["extractedParameters"] = request_json.get("extractedParameters") or {}

        if (request_json.get("complete") is None) or (request_json.get("complete") is True):
            result_json["intent"] = {
                "object_id": str(intent.id),
                "confidence": confidence,
                "id": intent.intentId
            }

        if parameters:
            # Extract NER entities
            result_json["extractedParameters"].update(entity_extraction.predict(
                intent_id, request_json))

            missing_parameters = []
            result_json["missingParameters"] = []
            result_json["parameters"] = []
            for parameter in parameters:
                result_json["parameters"].append({
                    "name": parameter.name,
                    "type": parameter.type,
                    "required": parameter.required
                })

                if parameter.required:
                    if parameter.name not in result_json["extractedParameters"].keys():
                        result_json["missingParameters"].append(
                            parameter.name)
                        missing_parameters.append(parameter)

            if missing_parameters:
                result_json["complete"] = False
                current_node = missing_parameters[0]
                result_json["currentNode"] = current_node["name"]
                result_json["speechResponse"] = split_sentence(current_node["prompt"])
            else:
                result_json["complete"] = True
                context["parameters"] = result_json["extractedParameters"]
        else:
            result_json["complete"] = True

    elif request_json.get("complete") is False:
        if "cancel" not in intent.name:
            intent_id = request_json["intent"]["id"]
            app.logger.info(intent_id)
            intent = Intent.objects.get(intentId=intent_id)

            extracted_parameter = entity_extraction.replace_synonyms({
                request_json.get("currentNode"): request_json.get("input")
            })

            # replace synonyms for entity values
            result_json["extractedParameters"].update(extracted_parameter)

            result_json["missingParameters"].remove(
                request_json.get("currentNode"))

            if len(result_json["missingParameters"]) == 0:
                result_json["complete"] = True
                context = {"parameters": result_json["extractedParameters"],
                           "context": request_json["context"]}
            else:
                missing_parameter = result_json["missingParameters"][0]
                result_json["complete"] = False
                current_node = [
                    node for node in intent.parameters if missing_parameter in node.name][0]
                result_json["currentNode"] = current_node.name
                result_json["speechResponse"] = split_sentence(current_node.prompt)
        else:
            result_json["currentNode"] = None
            result_json["missingParameters"] = []
            result_json["parameters"] = {}
            result_json["intent"] = {}
            result_json["complete"] = True

    if result_json["complete"]:
        if intent.apiTrigger:
            isJson = False
            parameters = result_json["extractedParameters"]
            headers = intent.apiDetails.get_headers()
            app.logger.info("headers %s" % headers)
            url_template = Template(
                intent.apiDetails.url, undefined=SilentUndefined)
            rendered_url = url_template.render(**context)
            if intent.apiDetails.isJson:
                isJson = True
                request_template = Template(
                    intent.apiDetails.jsonData, undefined=SilentUndefined)
                parameters = json.loads(request_template.render(**context))

            try:
                result = call_api(rendered_url,
                                  intent.apiDetails.requestType, headers,
                                  parameters, isJson)
                context["result"] = result
                template = Template(
                    intent.speechResponse, undefined=SilentUndefined)
                result_json["speechResponse"] = split_sentence(template.render(**context))
            except Exception as e:
                app.logger.warn("API call failed", e)
                result_json["speechResponse"] = ["Service is not available. Please try again later."]
        else:
            context["result"] = {}
            template = Template(intent.speechResponse,
                                undefined=SilentUndefined)
            result_json["speechResponse"] = split_sentence(template.render(**context))

        app.logger.info(request_json.get("input"), extra=result_json)
    else:
        if len(result_json["missingParameters"]) == 0 or result_json["missingParameters"] is None:
            context["result"] = {}
            template = Template(intent.speechResponse,
                                undefined=SilentUndefined)
            result_json["speechResponse"] = split_sentence(template.render(**context))

    app.logger.info(request_json.get("input"), extra=result_json)
    return build_response.build_json(result_json)


def update_model():
    """
    Signal hook to be called after training is completed.
    Reloads ml models and synonyms.
    :param :
    :param :
    :param :
    :return:
    """
    global sentence_classifier

    sentence_classifier.load(app.config["MODELS_DIR"])

    synonyms = get_synonyms()

    global entity_extraction

    entity_extraction = EntityExtractor(synonyms)
    app.logger.info("Intent Model updated")


def predict(request_payload):
    """request_payload
    Predict Intent using Intent classifier
    :param request_payload:
    :return:
    """
    enterprise_name = None
    bot_name = None
    bot = None
    enterprise_name = request_payload.get("enterprise_name")
    bot_name = request_payload.get("bot_name")
    if enterprise_name is None or bot_name is None:
        bot = Bot.objects.get(name="default")
    else:
        bot = Bot.objects.get(name=bot_name, enterprise_name=enterprise_name)
    sentence = request_payload.get("input")
    predicted, intents = sentence_classifier.process(sentence)
    app.logger.info("predicted intent %s", predicted)
    app.logger.info("other intents %s", intents)
    if predicted["confidence"] < bot.config.get("confidence_threshold", .90):
        intent = Intent.objects.get(intentId=app.config["DEFAULT_FALLBACK_INTENT_NAME"], enterprise_name=enterprise_name)
        return intent.intentId, 1.0, []
    else:
        return predicted["intent"], predicted["confidence"], intents[1:]
