from mongoengine.fields import DictField
from mongoengine.fields import Document
from mongoengine.fields import StringField


class Bot(Document):
    name = StringField(max_length=100, required=True, unique=False)
    enterprise_name = StringField(max_length=100, required=True, unique=False)
    model_dir = StringField(max_length=100, required=False)
    config = DictField(required=True, default={
        "confidence_threshold": .50
    })
