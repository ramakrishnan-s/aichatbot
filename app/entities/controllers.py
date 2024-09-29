from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from flask import Blueprint, request, Response
from mongoengine import DoesNotExist

from app.commons import build_response
from app.commons.utils import update_document
from app.entities.models import Entity

entities_blueprint = Blueprint('entities_blueprint', __name__,
                               url_prefix='/entities')


@entities_blueprint.route('/', methods=['POST'])
def create_entity():
    """
    Create a story from the provided json
    :return:
    """
    content = request.get_json(silent=True)
    entity = Entity()
    name = content.get("name")
    entity.name = name
    enterprise_name = content.get("enterprise_name")
    entity.enterprise_name = enterprise_name
    bot_name = content.get("bot_name")
    entity.bot_name = bot_name
    entity.entity_values = []

    try:
        if content.get('entity_values') is not None:
            #json_data = content.get('entity_values')
            json_data = loads(request.get_data())
            entity = update_document(entity, json_data)
            #entity.entity_values = content.get('entity_values')

            try:
                entity_org_obj = Entity.objects.get(name=name, bot_name=bot_name, enterprise_name=enterprise_name)
                if entity_org_obj is not None:
                    entity.pk = entity_org_obj.pk
                    entity_org_obj.delete()
            except DoesNotExist:
                print(f"No matching object available. Will save new Object")
            except Exception as err:
                print(f"Persistence {err=}, {type(err)=}")
                return "Error in creating new Entity", 400
        entity_id = entity.save()
        return build_response.build_json({
            "_id": str(entity_id.id)})
    except Exception as e:
        return build_response.build_json({"error": str(e)})


@entities_blueprint.route('/<enterprise_name>', methods=['GET'])
def read_entities(enterprise_name):
    """
    find list of entities
    :return:
    """
    if enterprise_name is not None:
        entities = Entity.objects(enterprise_name=enterprise_name)
        return build_response.sent_json(entities.to_json())
    else:
        return build_response.sent_error("Internal Error", 500)


@entities_blueprint.route('/<id>', methods=['GET'])
def get_entity(id):
    """
    Find details for the given entity name
    :param id:
    :return:
    """
    return Response(
        response=dumps(Entity.objects.get(
            id=ObjectId(id)).to_mongo().to_dict()),
        status=200, mimetype="application/json")


@entities_blueprint.route('/', methods=['GET'])
def read_entity():
    """
    Find details for the given entity name
    :param :
    :return:
    """
    global entities
    uid = None
    bot_name = None
    enterprise_name = None
    entity = None
    args = request.args
    uid = args.get("_id")
    bot_name = args.get("bot_name")
    enterprise_name = args.get("enterprise_name")
    if uid is not None:
        entities = Entity.objects.get(id=ObjectId(uid))
    elif bot_name is not None and enterprise_name is not None:
        entities = Entity.objects.get(bot_name=bot_name, enterprise_name=enterprise_name)
    elif enterprise_name is not None:
        entities = Entity.objects(enterprise_name=enterprise_name)

    if entities is not None:
        return build_response.sent_json(entities.to_json())
        #return Response(response=dumps(entities.to_json()), status=200, mimetype="application/json")
    else:
        return build_response.sent_error("Internal Error", 500)


@entities_blueprint.route('/', methods=['PUT'])
def update_entity():
    """
    Update a story from the provided json
    :param :
    :return:
    """
    uid = None
    bot_name = None
    enterprise_name = None
    entity_org_obj = None
    name = None
    entity = Entity()
    json_data = loads(request.get_data())
    #args = request.args
    uid = json_data.get("_id")
    entity._id = uid
    entity.name = name
    bot_name = json_data.get("bot_name")
    entity.bot_name = bot_name
    enterprise_name = json_data.get("enterprise_name")
    entity.enterprise_name = enterprise_name
    try:
        entity = update_document(entity, json_data)
        if bot_name is not None and enterprise_name is not None:
            entity_org_obj = Entity.objects.get(name=name, bot_name=bot_name, enterprise_name=enterprise_name)
        if entity_org_obj is not None:
            entity.pk = entity_org_obj.pk
            entity_org_obj.delete()
            entity.save()
            return build_response.sent_ok()
    except DoesNotExist:
        print(f"No matching object available. Will save new Object")
        entity.save()
        return build_response.sent_ok()


@entities_blueprint.route('/', methods=['DELETE'])
def delete_entity():
    """
    Delete a intent
    :param :
    :return:
    """

    uid = None
    bot_name = None
    enterprise_name = None
    entity = None
    json_data = loads(request.get_data())
    uid = json_data.get("_id")
    bot_name = json_data.get("bot_name")
    enterprise_name = json_data.get("enterprise_name")
    if bot_name is not None and enterprise_name is not None:
        entity = Entity.objects.get(bot_name=bot_name, enterprise_name=enterprise_name)

    if entity is not None:
        entity.delete()
    return build_response.sent_ok()
