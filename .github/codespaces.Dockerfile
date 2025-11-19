#
# VERSION 0.5.0
# DOCKER-VERSION  27.2.0
# AUTHOR:         Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
# DESCRIPTION:    A codespaces base image with tskitetude installed
# TO_BUILD:       docker build --rm -t bunop/tskitetude .
# TO_RUN:         docker run --rm -ti bunop/tskitetude bash
# TO_TAG:         docker tag bunop/tskitetude:latest bunop/tskitetude:0.5.0
#

FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

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
        software-properties-common && \
    apt-get clean && rm -rf /var/lib/apt/lists/

# Taken from: https://github.com/nextflow-io/training/blob/master/.github/gitpod.Dockerfile
# Install Apptainer (Singularity)
RUN add-apt-repository -y ppa:apptainer/ppa && \
    apt-get update --quiet && \
    apt install -y apptainer && \
    apt-get clean && rm -rf /var/lib/apt/lists/

# set environment variables
ENV CONDA_DIR="/opt/conda"

# Install Conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p ${CONDA_DIR} && \
    rm Miniconda3-latest-Linux-x86_64.sh

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH

# update base channel
RUN conda config --add channels bioconda && \
    conda config --add channels conda-forge && \
    conda config --set channel_priority strict && \
    conda config --add envs_dirs /workspaces/.conda/envs && \
    conda update --quiet --yes --all && \
    conda install --quiet --yes --name base \
        mamba && \
    conda clean --all --force-pkgs-dirs --yes

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
COPY .github/codespaces.bashrc /home/vscode/.bashrc

# Fix user permissions
RUN chown -R vscode:vscode /home/vscode/ /workspaces

# Change user to vscode
USER vscode

WORKDIR /workspaces
