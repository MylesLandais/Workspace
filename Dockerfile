# 1. Build stage
FROM elixir:1.18.4-alpine AS build

RUN apk add --no-cache build-base ffmpeg python3 py3-pip git yt-dlp

WORKDIR /app

COPY mix.exs mix.lock ./
COPY config ./config

# Set the environment (this is KEY)
ENV MIX_ENV=prod

# Install Hex and dependencies for dev
RUN mix local.hex --force && mix deps.get

COPY . .
RUN mix compile

# 2. Release stage
FROM elixir:1.18.4-alpine

RUN apk add --no-cache ffmpeg python3 py3-pip yt-dlp

WORKDIR /app

COPY --from=build /app .

ENV MIX_ENV=prod

CMD ["mix", "run", "--no-halt"]
