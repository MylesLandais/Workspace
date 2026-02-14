FROM postgres:16

# Install build dependencies for extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-server-dev-16 \
    git \
    wget \
    flex \
    bison \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector
RUN cd /tmp && \
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install && \
    rm -rf /tmp/pgvector

# Install Apache AGE
RUN cd /tmp && \
    git clone --branch PG16 https://github.com/apache/age.git && \
    cd age && \
    make install && \
    rm -rf /tmp/age

# Cleanup
RUN apt-get purge -y --auto-remove build-essential postgresql-server-dev-16 git wget && \
    rm -rf /var/lib/apt/lists/*
