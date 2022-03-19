FROM ubuntu:18.04

MAINTAINER Daniel Vagg "https://github.com/ezeakeal/vadix-identify"

RUN apt-get update && \
	apt-get install -y \
        curl wget vim \
		python3 python3-virtualenv \
		python3-pip libxml2-dev libxslt1-dev \
		libsasl2-dev python3-dev libldap2-dev libssl-dev \
        graphviz libgraphviz-dev libjpeg-dev postgresql-client

WORKDIR /opt/vdx_id

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY src/requirements.txt /opt/vdx_id/requirements.txt
RUN pip3 install -r /opt/vdx_id/requirements.txt

COPY src /opt/vdx_id/
WORKDIR /opt/vdx_id

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
