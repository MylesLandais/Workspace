# --- 1. Build Stage ---
FROM elixir:1.18.4-alpine AS build

RUN apk add --no-cache \
    build-base \
    ffmpeg \
    python3 \
    py3-pip \
    git \
    yt-dlp

WORKDIR /app

COPY mix.exs mix.lock ./
COPY config ./config
RUN mix local.hex --force && mix deps.get

COPY . .
RUN mix compile

# --- 2. Release Stage ---
FROM elixir:1.18.4-alpine AS app

WORKDIR /app

RUN apk add --no-cache ffmpeg python3 py3-pip yt-dlp

COPY --from=build /app .

CMD ["mix", "run", "--no-halt"]
