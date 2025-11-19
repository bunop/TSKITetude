#
# VERSION 0.5.1
# DOCKER-VERSION  27.2.0
# AUTHOR:         Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
# DESCRIPTION:    A codespaces base image with tskitetude installed
# TO_BUILD:       docker build --rm -t bunop/tskitetude .
# TO_RUN:         docker run --rm -ti bunop/tskitetude bash
# TO_TAG:         docker tag bunop/tskitetude:latest bunop/tskitetude:0.5.1
#

FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

LABEL maintainer="paolo.cozzi@ibba.cnr.it"

# set user for installing stuff
USER root

# Install stuff
# software-properties-common is needed for add-apt-repository
RUN apt-get update && \
    apt-get install -y \
        tmux \
        tree \
        build-essential \
        default-jre \
        wget \
        curl \
        graphviz \
        singularity-container && \
    apt-get clean && rm -rf /var/lib/apt/lists/

# set environment variables
ENV CONDA_BASE="/opt/miniconda"

# Install Conda
RUN wget -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \
    bash Miniforge3.sh -b -p "$CONDA_BASE" && \
    rm Miniforge3.sh

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_BASE/bin:$PATH

# update base channel
RUN conda init bash && \
    conda config --add envs_dirs /workspaces/.conda/envs

# Some environment variables for nextflow
ENV \
    NXF_OPTS="-Xms1g -Xmx4g" \
    NXF_SINGULARITY_CACHEDIR="${HOME}/.nxf_singularity_cachedir" \
    NXF_EXECUTOR="local"

# download and install nextflow
RUN wget -qO- https://get.nextflow.io | bash && \
    mv nextflow /usr/local/bin/ && \
    chmod +rx /usr/local/bin/nextflow

# Set some useful variables
ARG POETRY_VERSION=2.2.1

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

# Copy project files
WORKDIR /workspaces/tskitetude
COPY pyproject.toml poetry.lock ./
COPY tskitetude/ ./tskitetude/
COPY README.md ./

# Install the project with docs dependencies
RUN poetry install --with docs

# ovverride bashrc
COPY .github/bashrc /home/vscode/.bashrc

# Fix user permissions
RUN chown -R vscode:vscode /home/vscode/ /workspaces

# Change user to vscode
USER vscode

WORKDIR /workspaces
