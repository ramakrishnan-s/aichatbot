from flask import Blueprint, request
from mongoengine import NotUniqueError, DoesNotExist
from pymongo.errors import DuplicateKeyError

from app.agents.models import Bot
from app.commons import build_response

bots = Blueprint('bots_blueprint', __name__,
                 url_prefix='/agents/')


@bots.route('/', methods=['POST'])
def set_bot():
    """
    Read bot config
    :param :
    :return:
    """
    bot = Bot()
    bot.name = "default"
    bot.model_dir = "model_files/"
    bot.enterprise_name = "default"
    enterprise_name = None
    models_dir = None

    try:
        content = request.get_json(silent=True)
        if content.get('name') is not None:
            name = content.get('name')
            bot.name= name
        if content.get('confidence_threshold') is not None:
            confidence = content.get('confidence_threshold')
            del bot.config["confidence_threshold"]
            bot.config["confidence_threshold"] = confidence

        if content.get('enterprise_name') is not None:
            enterprise_name = content.get('enterprise_name')
            bot.enterprise_name = enterprise_name
        if content.get('model_dir') is not None:
            models_dir = content.get('model_dir')
            bot.model_dir = "model_files/" + bot.enterprise_name + "/" + models_dir + "/"
        try:
            bot_org_obj = Bot.objects.get(name=bot.name, enterprise_name = bot.enterprise_name )
            bot.pk = bot_org_obj.pk
            bot_org_obj.delete()
        except DoesNotExist:
            print(f"No matching object available. Will save new Object")
        except Exception as err:
            print(f"Persistence {err=}, {type(err)=}")
            return "Error in creating new Bot", 400

        result = bot.save()
        if result is not None:
           return build_response.sent_ok()
        else:
           return "Error in saving new Bot", 400
    except DuplicateKeyError as err:
       print(f"Duplicate Key {err=}, {type(err)=}")
    except NotUniqueError as err:
       print(f"NotUnique Key {err=}, {type(err)=}")
    except Exception as err:
       print(f"Unexpected {err=}, {type(err)=}")
    return "Error in creating new Bot", 400


@bots.route('/', methods=['PUT'])
def put_bot():
    """
    Read bot config
    :param :
    :return:
    """
    enterprise_name = None
    model_dir = None

    try:
        content = request.get_json(silent=True)
        name = content.get('name')
        if content.get('enterprise_name') is not None:
            enterprise_name = content.get('enterprise_name')
        try:
            bot = Bot.objects.get(name=name, enterprise_name=enterprise_name)
        except DoesNotExist:
            print(f"No matching object available. Will save new Object")
            bot = Bot(name=name, enterprise_name=enterprise_name)
        except Exception as err:
            print(f"Query {err=} will save as new object, {type(err)=}")
            bot = Bot(name=name, enterprise_name=enterprise_name)
        if content.get('confidence_threshold') is not None:
            confidence = content.get('confidence_threshold')
            del bot.config["confidence_threshold"]
            bot.config["confidence_threshold"] = confidence

        #        bot.config = content

        if content.get('model_dir') is not None:
            model_dir = content.get('model_dir')
        if enterprise_name is not None and model_dir is not None:
            del bot.enterprise_name
            bot.enterprise_name = enterprise_name
            del bot.model_dir
            bot.model_dir = "model_files/" + bot.enterprise_name + "/" + model_dir
        try:
            bot_org_obj = Bot.objects.get(name=bot.name)
            if bot_org_obj is not None:
                bot.pk = bot_org_obj.pk
        except DoesNotExist:
            print(f"No matching object available. Will save new Object")
        except Exception as err:
            print(f"Persistence {err=}, {type(err)=}")
            return "Error in creating new Bot", 400
        bot.save()
        print("Updated  bot: " + name)
        return build_response.sent_ok()
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")


@bots.route('/', methods=['GET'])
def get_bot():
    name = None
    enterprise_name = None
    try:
        args = request.args
        name = args.get("name")
        enterprise_name = args.get("enterprise_name")
        if name is None:
            return build_response.sent_error("invalid argument. name is Null", 200)
        if enterprise_name is None:
            return build_response.sent_error("invalid argument. name is Null", 200)
        bot = Bot.objects.get(name=name, enterprise_name=enterprise_name)
        return build_response.sent_json(bot.to_json())
    except DoesNotExist:
        print(
            f"No matching bot {name=} available for {enterprise_name=}. t, {type(name)=},  {type(enterprise_name)=}")
        return build_response.sent_error_not_found(
            f"No matching bot {name=} available for {enterprise_name=}. t, {type(name)=},  {type(enterprise_name)=}")
    except Exception as err:
        print(f"Internal Error {err=}, {type(err)=}")
        return build_response.sent_error("Internal Error {err=}, {type(err)=}", 500)


@bots.route('/', methods=['DELETE'])
def delete_bot():
    enterprise_name = None
    name = None
    try:
        content = request.get_json(silent=True)
        if content.get('name') is not None:
            name = content.get('name')
        if content.get('enterprise_name') is not None:
            enterprise_name = content.get('enterprise_name')
        bot = Bot.objects.get(name=name, enterprise_name=enterprise_name)
        if bot is not None:
            bot.delete()
            return build_response.sent_ok()
    except DoesNotExist as err:
        print(
            f"No matching bot {name=} available for {enterprise_name=}. t, {type(name)=},  {type(enterprise_name)=}")
        return build_response.sent_error_not_found(
            f"No matching bot {name=} available for {enterprise_name=}. t, {type(name)=},  {type(enterprise_name)=}")
    except Exception as err:
        print(f"Internal Error {err=}, {type(err)=}")
        return build_response.sent_error("Internal Error {err=}, {type(err)=}", 500)
