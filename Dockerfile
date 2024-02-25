#
# VERSION 0.2
# DOCKER-VERSION  25.0.3
# AUTHOR:         Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
# DESCRIPTION:    A multi-stage image with tskit dependencies
# TO_BUILD:       docker build --rm -t bunop/tskitetude .
# TO_RUN:         docker run --rm -ti bunop/tskitetude bash
# TO_TAG:         docker tag bunop/tskitetude:latest bunop/tskitetude:0.2
#

###############################################################################
# Those variables are defined before the FROM scope: to use them after, recall
# ARG in build stages
ARG APP_NAME=tskitetude
ARG APP_PATH=/opt/$APP_NAME
ARG PYTHON_VERSION=3.9
ARG POETRY_VERSION=1.7.1

FROM python:${PYTHON_VERSION}

# MAINTAINER is deprecated. Use LABEL instead
LABEL maintainer="paolo.cozzi@ibba.cnr.it"

# Import ARGs which I need in this build stage
# IMPORTANT!: without this redefinition, you can't use variables defined
# before the first FROM statement
ARG POETRY_VERSION
ARG APP_NAME
ARG APP_PATH

# Set some useful variables
ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1
ENV \
    POETRY_VERSION=${POETRY_VERSION} \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install Poetry - require $POETRY_VERSION & $POETRY_HOME environment variables
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="$POETRY_HOME/bin:$PATH"

# CREATE APP_PATH
RUN mkdir -p ${APP_PATH}
WORKDIR ${APP_PATH}

# Need to copy all the files declared in pyproject.toml
COPY poetry.lock pyproject.toml README.md ./
COPY tskitetude/ ./tskitetude/

# Install stuff
RUN poetry install

ARG VIRTUAL_ENV=${APP_PATH}/.venv

# See https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV \
    VIRTUAL_ENV=${VIRTUAL_ENV} \
    PATH="${VIRTUAL_ENV}/bin:${PATH}"

WORKDIR ${APP_PATH}
