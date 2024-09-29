from bson.objectid import ObjectId
from flask import Blueprint, request

from app.commons import build_response
from app.intents.models import Intent
from app.nlu.tasks import train_models

train = Blueprint('train_blueprint', __name__,
                  url_prefix='/train')


@train.route('/', methods=['POST'])
def save_training_data():
    """
    Save training data for given story
    :param story_id:
    :return:
    """
    content = request.get_json(silent=True)
    name = content.get("name")
    enterprise_name = content.get("enterprise_name")
    bot_name = content.get("bot_name")
    trainingData = content.get("trainingData")
    story = Intent.objects.get(name=name, enterprise_name=enterprise_name,bot_name=bot_name )
    story.trainingData = trainingData
    story.save()
#    train_models()
    return build_response.sent_ok()


@train.route('/enterprise_id/service_id/story_id', methods=['GET'])
def get_training_data(enterprise_id, service_id, story_id):
    """
    retrieve training data for a given story
    :param story_id:
    :return:
    """

    def get_training_data(enterprise_id, service_id, story_id):

        story = Intent.objects.get(name=story_id, enterprise_name=enterprise_id, bot_name= service_id)
        return build_response.build_json(story.trainingData)
