
### Installation

### Using docker-compose 
```sh
docker-compose up -d
```

### Using Helm

```sh
helm dep update helm/ai-chatbot-framework

helm upgrade --install --create-namespace -n ai-chatbot-framework ai-chatbot-framework helm/ai-chatbot-framework

# port forward for local installation
kubectl port-forward --namespace=ai-chatbot-framework service/ingress-nginx-controller 8080:80
```

### Using Docker
```sh

# pull docker images
docker pull alfredfrancis/ai-chatbot-framework_backend:latest
docker pull alfredfrancis/ai-chatbot-framework_frontend:latest

# start a mongodb server
docker run --name mongodb -d mongo:3.6

# start iky backend
docker run -d --name=iky_backend --link mongodb:mongodb -e="APPLICATION_ENV=Production" alfredfrancis/ai-chatbot-framework_backend:latest

# setup default intents
docker exec -it iky_backend python manage.py migrate

# start iky gateway with frontend
docker run -d --name=iky_gateway --link iky_backend:iky_backend -p 8080:80 alfredfrancis/ai-chatbot-framework_frontend:latest

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
* Production
```sh
APPLICATION_ENV="Production" gunicorn -k gevent --bind 0.0.0.0:8080 run:app
```

