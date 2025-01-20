FROM python:3.10

LABEL MAINTAINER="Rithish Sripaul <rithishsripaul@gmail.com>"

ENV GROUP_ID=1000 \
    USER_ID=1000

WORKDIR /var/www/

ADD ./requirements.txt /var/www/requirements.txt
RUN pip install -r requirements.txt
ADD . /var/www/
RUN pip install gunicorn

RUN addgroup -gid $GROUP_ID www
RUN adduser --disabled-password --uid $USER_ID --ingroup www --shell /bin/sh www

USER www

EXPOSE 5000

CMD [ "gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]