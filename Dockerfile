FROM ubuntu:latest
MAINTAINER Ryan Kortmann "ryankortmann@gmail.com"

# Packages
ADD docker/packages.txt /tmp/packages.txt
RUN apt-get update -y
RUN cat /tmp/packages.txt | xargs apt-get install -y

# PIP
ADD docker/pip.txt /tmp/pip.txt
RUN pip install --upgrade pip
RUN pip install -r /tmp/pip.txt

# AWS Environment Vars
ENV AWS_ACCESS_KEY_ID 'AKIAJPXFAKK74JXT6HMQ'
ENV AWS_SECRET_ACCESS_KEY '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'
ENV AWS_REGION 'us-east-1'

# App
COPY . /opt/gspotsyncer/

# Start server
WORKDIR /opt/gspotsyncer/
EXPOSE 5000
CMD ["python", "run.py"]