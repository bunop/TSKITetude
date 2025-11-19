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
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tmux \
        tree \
        build-essential \
        openjdk-17-jre-headless \
        wget \
        curl \
        graphviz \
        singularity-container && \
    apt-get clean && rm -rf /var/lib/apt/lists/

# set environment variables
ENV CONDA_BASE="/opt/miniconda"

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_BASE/bin:$PATH

# Install Conda
RUN wget -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \
    bash Miniforge3.sh -b -p "$CONDA_BASE" && \
    rm Miniforge3.sh && \
    conda clean -afy

# Configure conda for bash and set envs_dirs to /workspaces for Codespaces persistence
# (Codespaces mounts the repo at /workspaces/<repo-name>, not in $HOME)
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
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR="/tmp/poetry-cache" \
    PIP_CACHE_DIR="/tmp/pip-cache"

# Install Poetry - require $POETRY_VERSION & $POETRY_HOME environment variables
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Prepare /workspaces directory and cache directories with vscode ownership before switching user
RUN mkdir -p /workspaces/tskitetude "$POETRY_CACHE_DIR" "$PIP_CACHE_DIR" && \
    chown -R vscode:vscode /workspaces "$POETRY_CACHE_DIR" "$PIP_CACHE_DIR"

# Switch to vscode user early (before COPY/install to avoid chown later)
USER vscode

# Copy project files and pre-install dependencies in /workspaces/tskitetude
# Codespaces will mount the actual repo at /workspaces/TSKITetude, reusing the .venv
WORKDIR /workspaces/tskitetude
COPY pyproject.toml poetry.lock ./
COPY tskitetude/ ./tskitetude/
COPY README.md ./

# Install the project with docs dependencies, then clean Poetry/Pip caches to reduce image size
# Cache cleanup saves hundreds of MB by removing downloaded wheels and metadata
RUN poetry install --with docs && \
    pip cache purge || true && \
    [ -x ./.venv/bin/pip ] && ./.venv/bin/pip cache purge || true && \
    rm -rf "$POETRY_CACHE_DIR" "$PIP_CACHE_DIR" ~/.cache/pip

# Override bashrc for vscode user
COPY .github/bashrc /home/vscode/.bashrc

# Set working directory to /workspaces (Codespaces will mount repo here)
WORKDIR /workspaces
