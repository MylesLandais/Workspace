# -- 1. Build Stage --
FROM elixir:1.18.4-alpine AS build

# Install system dependencies and build tools
RUN apk add --no-cache \
    build-base \
    ffmpeg \
    python3 \
    py3-pip \
    git
RUN pip install --upgrade yt-dlp

WORKDIR /app

# Cache dependencies
COPY mix.exs mix.lock ./
COPY config ./config
RUN mix local.hex --force && mix deps.get

# Copy source and compile
COPY . .
RUN mix compile

# -- 2. Release Stage --
FROM elixir:1.18.4-alpine AS app

WORKDIR /app

# Install runtime deps only (not build tools)
RUN apk add --no-cache ffmpeg python3 py3-pip
RUN pip install --upgrade yt-dlp

# Copy compiled app from build stage
COPY --from=build /app .

# By default, Elixir apps need /tmp and /root writable
RUN mkdir -p /tmp

CMD ["mix", "run", "--no-halt"]
