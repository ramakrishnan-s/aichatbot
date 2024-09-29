import os
from bson.json_util import dumps
from bson.json_util import loads
from bson.objectid import ObjectId
from flask import Blueprint, request, Response
from flask import abort
from flask import current_app as app
from mongoengine import DoesNotExist

from app.commons import build_response
from app.commons.utils import update_document
from app.intents.models import ApiDetails
from app.intents.models import Intent
from app.intents.models import Parameter
from app.nlu.tasks import train_models

intents = Blueprint('intents_blueprint', __name__,
                    url_prefix='/intents')


@intents.route('/', methods=['POST'])
def create_intent():
    """
    Create a story from the provided json
    :return:
    """
    content = request.get_json(silent=True)

    uid = None
    name = None
    bot_name = None
    enterprise_name = None
    intent_org_object = None
    intent = Intent()
    name = content.get("name")
    intent.name = name
    enterprise_name = content.get("enterprise_name")
    intent.enterprise_name = enterprise_name
    bot_name = content.get("bot_name")
    intent.bot_name = bot_name
    intent.intentId = content.get("intentId")
    intent.speechResponse = content.get("speechResponse")
    intent.trainingData = []

    if content.get("apiTrigger") is True:
        intent.apiTrigger = True
        api_details = ApiDetails()
        isJson = content.get("apiDetails").get("isJson")
        api_details.isJson = isJson
        if isJson:
            api_details.jsonData = content.get("apiDetails").get("jsonData")
        api_details.url = content.get("apiDetails").get("url")
        api_details.headers = content.get("apiDetails").get("headers")
        api_details.requestType = content.get("apiDetails").get("requestType")
        intent.apiDetails = api_details
    else:
        intent.apiTrigger = False

    if content.get("parameters"):
        for param in content.get("parameters"):
            parameter = Parameter()
            update_document(parameter, param)
            intent.parameters.append(parameter)
    if content.get("trainingData"):
        intent.trainingData = content.get("trainingData")
    try:
        if name is not None and bot_name is not None and enterprise_name is not None:
            intent_org_obj = Intent.objects.get(name=name, bot_name=bot_name, enterprise_name=enterprise_name)
            if intent_org_obj is not None:
                intent.pk = intent_org_obj.pk
                intent_org_obj.delete()
                story_id = intent.save(force_insert=True, upsert=True)
                return build_response.build_json({
                    "_id": str(story_id.id)})
    except DoesNotExist:
        print(f"No matching object available. Will save new Object")
    try:
        story_id = intent.save(force_insert=True, upsert=True)
        return build_response.build_json({
            "_id": str(story_id.id)})
    except Exception as e:
        return build_response.build_json({"error": str(e)})


@intents.route('/<enterprise_name>', methods=['GET'])
def read_intents(enterprise_name):
    """
    find list of intents for the agent
    :return:
    """
    if enterprise_name is not None:
        try:
            all_intents = Intent.objects(enterprise_name=enterprise_name)
            return build_response.sent_json(all_intents.to_json())
        except DoesNotExist:
            print(f"No matching object available. ")
            return "No matching intents available", 400
        except Exception as err:
            print(f"Persistence {err=}, {type(err)=}")
            return "Error in getting intents", 400
    else:
        return build_response.sent_error("Internal Error", 500)


@intents.route('/<name>/<bot_name>/<enterprise_name>')
def get_intent(name, bot_name, enterprise_name):
    """
    Find details for the given intent id
    :param name,
    :param bot_name,
    :param enterprise_name
    :return:
    """
    return Response(response=dumps(
        Intent.objects.get(
            name=name, bot_name=bot_name, enterprise_name=enterprise_name).to_mongo().to_dict()),
        status=200,
        mimetype="application/json")


@intents.route('/<id>')
def read_intent(id):
    """
    Find details for the given intent id
    :param id:
    :return:
    """
    return Response(response=dumps(
        Intent.objects.get(
            id=ObjectId(id)).to_mongo().to_dict()),
        status=200,
        mimetype="application/json")


@intents.route('/', methods=['PUT'])
def update_intent():
    """
    Update a story from the provided json
    :return:
    """
    name = None
    uid = None
    bot_name = None
    enterprise_name = None
    intent_org_obj = None
    intent = Intent()
    json_data = loads(request.get_data())
    uid = json_data.get("_id")
    name = json_data.get("name")
    enterprise_name = json_data.get("enterprise_name")
    intent._id = uid
    bot_name = json_data.get("bot_name")
    intent.bot_name = bot_name
    intent.enterprise_name = enterprise_name
    try:
        if name is not None and bot_name is not None and enterprise_name is not None:
            intent = update_document(intent, json_data)
            intent_org_obj = Intent.objects.get(name=name, bot_name=bot_name, enterprise_name=enterprise_name)
            if intent_org_obj is not None:
                intent.pk = intent_org_obj.pk
                intent_org_obj.delete()
                story_id = intent.save(force_insert=True, upsert=True)
                return build_response.build_json({
                    "_id": str(story_id.id)})
    except DoesNotExist:
        print(f"No matching object available. Will save new Object")
    try:
        story_id = intent.save(force_insert=True, upsert=True)
        return build_response.build_json({
            "_id": str(story_id.id)})
    except Exception as e:
        return build_response.build_json({"error": str(e)})


@intents.route('/', methods=['DELETE'])
def delete_intent():
    """
    Delete a intent
    """

    name = None
    uid = None
    bot_name = None
    enterprise_name = None
    intent = None
    json_data = loads(request.get_data())
    uid = json_data.get("_id")
    name = json_data.get("name")
    bot_name = json_data.get("bot_name")
    enterprise_name = json_data.get("enterprise_name")
    if name is not None and bot_name is not None and enterprise_name is not None and uid is not None:
        intent = Intent.objects.get(name=name, enterprise_name=enterprise_name, bot_name=bot_name)
        if intent is not None:
            intent.delete()
    try:
        train_models()
    except BaseException:
        pass

    # remove NER model for the deleted story
    try:
        os.remove("{}/{}.model".format(app.config["MODELS_DIR"], id))
    except OSError:
        pass
    return build_response.sent_ok()


@intents.route('/export', methods=['GET'])
def export_intents():
    """
    Deserialize and export MongoEngine as jsonfile
    :return:
    """
    intents_json = Intent.objects.to_json()
    app.logger.info(intents_json)
    return Response(intents_json,
                    mimetype='application/json',
                    headers={'Content-Disposition': 'attachment;filename=intents.json'})


@intents.route('/import', methods=['POST'])
def import_intents():
    """
    Convert json files to Intents objects and insert to MongoDB
    :return:
    """
    # check if the post request has the file part
    if 'file' not in request.files:
        abort(400, 'No file part')
    json_file = request.files['file']
    all_intents = import_json(json_file)

    return build_response.build_json({"num_intents_created": len(all_intents)})


def import_json(json_file):
    json_data = json_file.read()
    # intents = Intent.objects.from_json(json_data)
    all_intents = loads(json_data)

    creates_intents = []
    for intent in all_intents:
        new_intent = Intent()
        new_intent = update_document(new_intent, intent)
        new_intent.save()
        creates_intents.append(new_intent)
    return creates_intents
