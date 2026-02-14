ARG NODE_VERSION=20
ARG PHOENIX_VERSION=1.7

FROM elixir:1.15

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN apt-get update && apt-get install -y sudo git curl inotify-tools build-essential \
    && groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Node.js for assets
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs

# Hex, Rebar, Phoenix
RUN mix local.hex --force && mix local.rebar --force \
    && mix archive.install hex phx_new ${PHOENIX_VERSION} --force

USER $USERNAME
WORKDIR /workspace

EXPOSE 4000

