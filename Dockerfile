FROM ubuntu:latest
MAINTAINER Ryan Kortmann "ryankortmann@gmail.com"

# Prep for MongoDB package
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
RUN echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.0.list

# Packages
ADD docker/packages.txt /tmp/packages.txt
RUN apt-get update -y
RUN cat /tmp/packages.txt | xargs apt-get install -y

# PIP
ADD docker/pip.txt /tmp/pip.txt
RUN pip install --upgrade pip
RUN pip install -r /tmp/pip.txt

# Took this out since we link using volumes
# COPY . /opt/gspotsyncer/

# Start server
WORKDIR /opt/gspotsyncer/
EXPOSE 5000
CMD ["python", "run.py"]