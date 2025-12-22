# STAGE 1: Builder - Compile MakeMKV (Optional - commented out until correct version/URL is found)
# MakeMKV can be installed manually or added later. The pipeline works with FFmpeg fallback.
# FROM ubuntu:24.04 AS makemkv-builder
# ENV DEBIAN_FRONTEND=noninteractive
# ENV MAKEMKV_VERSION=1.17.8
# RUN apt-get update && apt-get install -y \
#     build-essential pkg-config libc6-dev libssl-dev libexpat1-dev \
#     libavcodec-dev libgl1-mesa-dev qtbase5-dev zlib1g-dev wget less \
#     && rm -rf /var/lib/apt/lists/*
# WORKDIR /tmp
# RUN wget https://www.makemkv.com/download/makemkv-bin-${MAKEMKV_VERSION}.tar.gz && \
#     wget https://www.makemkv.com/download/makemkv-oss-${MAKEMKV_VERSION}.tar.gz && \
#     tar -zxvf makemkv-bin-${MAKEMKV_VERSION}.tar.gz && \
#     tar -zxvf makemkv-oss-${MAKEMKV_VERSION}.tar.gz
# WORKDIR /tmp/makemkv-oss-${MAKEMKV_VERSION}
# RUN ./configure && make && make install
# WORKDIR /tmp/makemkv-bin-${MAKEMKV_VERSION}
# RUN mkdir -p /tmp/makemkv-bin-${MAKEMKV_VERSION}/tmp && \
#     echo "accepted" > /tmp/makemkv-bin-${MAKEMKV_VERSION}/tmp/eula_accepted && \
#     make install

# STAGE 2: Runtime - Jupyter base (MakeMKV optional, will use FFmpeg fallback)
FROM quay.io/jupyter/base-notebook:python-3.11

USER root

# Install runtime dependencies including MakeMKV runtime libraries
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

# MakeMKV installation commented out - will use FFmpeg fallback
# To enable MakeMKV, uncomment the builder stage above and these COPY commands:
# COPY --from=makemkv-builder /usr/bin/makemkvcon /usr/bin/makemkvcon
# COPY --from=makemkv-builder /usr/lib/libdriveio.so.0 /usr/lib/libdriveio.so.0
# COPY --from=makemkv-builder /usr/lib/libmakemkv.so.1 /usr/lib/libmakemkv.so.1
# COPY --from=makemkv-builder /usr/lib/libmmbd.so.0 /usr/lib/libmmbd.so.0
# RUN ldconfig

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
# Note: Project installation happens at runtime via volume mount
# The workspace is mounted at /home/jovyan/workspaces, so no build-time install needed
EXPOSE 8888

WORKDIR /home/jovyan/workspaces

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
