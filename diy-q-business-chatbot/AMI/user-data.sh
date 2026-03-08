#!/bin/bash

# authenticate to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <AWS_ID>.dkr.ecr.<REGION>.amazonaws.com

# pull
docker pull <AWS_ID>.dkr.ecr.<REGION>.amazonaws.com/chatbot-rag:latest

# run once to create the container with all parameters
docker run -d \
	--name chatbot-rag \
	-p 127.0.0.1:8501:8501 \
	--restart unless-stopped \
	-e BUCKET_APP=<BUCKET_APP> \
	-e BUCKET_LOG=<BUCKET_LOG> \
	<AWS_ID>.dkr.ecr.<REGION>.amazonaws.com/chatbot-rag:latest

systemctl restart chatbot-docker