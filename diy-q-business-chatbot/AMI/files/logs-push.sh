#!/bin/bash
# push nginx logs to s3

BUCKET="<BUCKET_LOG>"
LOGS_ACCESS="/var/log/nginx/access*.gz"
PREFIX_ACCESS="chatbot/access/"
LOGS_ERROR="/var/log/nginx/error*.gz"
PREFIX_ERROR="chatbot/error/"

for file in $LOGS_ACCESS; do
	aws s3 cp $file "s3://$BUCKET/$PREFIX_ACCESS"
done

for file in $LOGS_ERROR; do
	aws s3 cp $file "s3://$BUCKET/$PREFIX_ERROR"
done



