
### Installation

### Install MongoDB
```sh
- Install MongoDB server (Refer https://www.mongodb.com/try/download/community)
- Modify  MONGODB_HOST = "mongodb://192.168.0.102:27017/aichat" 

```
### Using Docker
# Build docker Image
```sh
docker build --tag aichat .
```
# Run Docker
- Pre-requsite - Ensure MongoDB is configured and running as above
```sh
docker run aichat
```
Refer 
### Using docker-compose 
```sh
docker-compose up -d
```

# setup 
- Create Bot Example Playload:
  ```sh
  EndPoint - http://<dockerIP>:9080/agents/
  Method - POST
  Sample Payload
  --------------
   {
    "enterprise_name":"accessnetworks",
    "name":"text",
    "confidence_threshold":0.50,
    "model_dir":"generic"
    }

- Create intents
```sh
EndPoint - http://<dockerIP>:9080/intents/
  Method - POST
  Sample Payload
  --------------
```
 Sample Payloads and default Json for Intents are in https://github.com/ramakrishnan-s/aichatbot/tree/main/examples


- Build model
```sh
EndPoint - http://127.0.0.1:9080/nlu/build_models
Payload
-------
{ }
```
- Send Bot Message

```sample welcome (initial start of conversation) message
{
    "enterprise_name":"accessnetworks",
    "bot_name":"text",
    "currentNode": "",
    "complete": "None",
	"sequence_id":0,
    "context": {},
    "parameters": [],
    "extractedParameters": {},
    "speechResponse": "",
    "intent": {},
    "input": "Hi",
    "missingParameters": []
}
```

restaurant search
```sh
{
    "enterprise_name": "mitra",
    "bot_name": "text",
    "currentNode": "cuisine",
    "complete": false,
    "sequence_id": 2,
    "context": {},
    "parameters": [
        {
            "name": "location",
            "type": "free_text",
            "required": true
        },
        {
            "name": "cuisine",
            "type": "free_text",
            "required": true
        }
    ],
    "extractedParameters": {
        "location": "malleswaram"
    },
    "speechResponse": [
        "Ok. ",
        " What type cuisine are you looking for?"
    ],
    "intent": {
        "object_id": "66f53987b8b6906dea1af873",
        "confidence": 0.9847961046915221,
        "id": "restaurant_search"
    },
    "input": "Looking for a restaurant in malleswaram",
    "missingParameters": [
        "cuisine"
    ]
}
```

### without docker

* Setup Virtualenv and install python requirements
```sh
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python run.py
```

