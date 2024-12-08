# base image
FROM python:3.12.0-slim

USER root


RUN apt-get update && \
    apt-get -y install procps net-tools wget curl vim nginx gunicorn supervisor bash --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


ENV env=stage
ENV APP_PATH=/usr/src/app

# set working directory
RUN mkdir -p $APP_PATH && \
    mkdir -p /var/log/emailwhiz

WORKDIR $APP_PATH
ENV PYTHONPATH=${APP_PATH}

# copy only the files needed for dependency resolution
COPY pyproject.toml poetry.lock /usr/src/app/

# install poetry and dependencies
RUN python -m pip install poetry && poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# add the rest of the application files
COPY . /usr/src/app/
# RUN ls -al /usr/src/app/
# setup supervisord
RUN mkdir -p /var/log/supervisord/ && \
    mkdir -p /var/log/gunicorn/



# # Remove the default Nginx configuration
# RUN rm /etc/nginx/sites-enabled/default

# # Copy the Nginx configuration file
# COPY nginx.conf /etc/nginx/sites-available/

# RUN ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled/
# add this line to make supervisor include *.ini config file from /etc/supervisor/conf.d/

RUN echo "files = /etc/supervisor/conf.d/*.ini" >> /etc/supervisor/supervisord.conf
COPY emailwhiz-supervisord.ini /etc/supervisor/conf.d/

EXPOSE 5000

# Health check must be on gunicorn port.
# HEALTHCHECK --interval=300s --timeout=10s --retries=1 CMD curl -f http://127.0.0.1:8000/ || exit 1

# run server
CMD ["supervisord", "--nodaemon", "-c", "/etc/supervisor/supervisord.conf"]
