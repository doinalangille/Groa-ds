# Groa Scrapers

### Basic

To run the scrapers on auto, run:
```
python3 run_scrapers_auto.py
```

### Run as Docker Container

Make sure you have a `.env` file in the `web_scraping` directory, and run:
```
docker build . --tag scrapers
docker run scrapers
```

### Upload a Docker Image to AWS ECS

To upload a docker image to AWS ECS, first make sure you have the AWS CLI installed and configured. You must be logged in to proceed.

Run the following to obtain a AWS login for docker:
```
aws ecr get-login
```

This will output something in the form:
```
docker login -u AWS -p {API_KEY} -e none https://615018563479.dkr.ecr.us-east-1.amazonaws.com
```
Copy this output and enter it in the terminal to log in to AWS with docker.

Then you must associate your local scrapers image with the AWS task `groa-scrapers`.
```
sudo docker tag scrapers:latest 615018563479.dkr.ecr.us-east-1.amazonaws.com/groa-scrapers:latest
```

Lastly, you must push the image to amazon:
```
sudo docker push 615018563479.dkr.ecr.us-east-1.amazonaws.com/groa-scrapers:latest
```
