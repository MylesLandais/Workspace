FROM quay.io/jupyter/base-notebook:python-3.11
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    yt-dlp \
    ffmpeg \
    git \
    jq \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install runpodctl CLI (Linux x86_64). This downloads the latest release from GitHub
# and installs the binary to /usr/local/bin. If you need a different arch, update the URL.
RUN set -eux; \
    TMPDIR=$(mktemp -d); \
    cd "$TMPDIR"; \
    # Prefer a pinned runpodctl release for reproducible builds
    RUNPODCTL_VERSION="v1.14.4"; \
    PINNED_TARBALL="https://github.com/runpod/runpodctl/releases/download/${RUNPODCTL_VERSION}/runpodctl_1.14.4_linux_amd64.tar.gz"; \
    if curl -fsSL -o runpodctl.tar.gz "$PINNED_TARBALL"; then \
        echo "Downloaded pinned runpodctl $RUNPODCTL_VERSION"; \
    else \
        echo "Pinned asset not available, falling back to dynamic discovery"; \
        REL_JSON=$(curl -sS https://api.github.com/repos/runpod/runpodctl/releases/latest); \
        echo "$REL_JSON" > rel.json; \
        URL=$(jq -r '.assets[] | select(.name | test("linux.*(amd64|x86[_-]?64)|amd64"; "i")) | .browser_download_url' rel.json | head -n1); \
        if [ -z "$URL" ] || [ "$URL" = "null" ]; then echo "Failed to locate runpodctl linux asset in release" >&2; cat rel.json >&2; exit 1; fi; \
        curl -fsSL -o runpodctl.tar.gz "$URL"; \
    fi; \
    tar -xzf runpodctl.tar.gz; \
    install -m 0755 runpodctl /usr/local/bin/runpodctl; \
    rm -rf "$TMPDIR";
RUN mkdir -p /home/jovyan/work && chown ${NB_UID}:${NB_GID} /home/jovyan/work
RUN mkdir -p /home/jovyan/downloads/ytdlp && chown ${NB_UID}:${NB_GID} /home/jovyan/downloads/ytdlp
USER ${NB_UID}:${NB_GID}
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt
EXPOSE 8888

WORKDIR /home/jovyan/workspaces

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
