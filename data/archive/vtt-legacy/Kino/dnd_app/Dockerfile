# Multi-stage Dockerfile for Phoenix application with Bun asset compilation

# Builder stage: Install Bun and compile assets
FROM oven/bun:1 AS builder

WORKDIR /app

# Copy package files for assets
COPY package.json bun.lockb* ./
COPY assets/package.json ./assets/
COPY assets/build.ts ./assets/

# Install dependencies (from assets directory)
WORKDIR /app/assets
RUN bun install --frozen-lockfile

# Copy assets source and config
COPY assets ./assets
COPY tailwind.config.js ../tailwind.config.js

# Create output directory and build assets
RUN mkdir -p ../priv/static/assets && \
    bun run build

# Runtime stage: Elixir/Phoenix application
FROM hexpm/elixir:1.15.7-erlang-26.0.2-alpine-3.18.0

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache build-base git

# Install Hex and Rebar
RUN mix local.hex --force && \
    mix local.rebar --force

# Copy application files (excluding assets, they're copied from builder)
COPY mix.exs mix.lock ./
COPY config ./config
COPY lib ./lib
COPY priv ./priv
COPY test ./test

# Copy built assets from builder stage
COPY --from=builder /app/priv/static/assets ./priv/static/assets

# Install Elixir dependencies
RUN mix deps.get && \
    mix deps.compile

# Compile application
RUN mix compile

# Expose port
EXPOSE 4000

# Default command (can be overridden in docker-compose.yml)
CMD ["mix", "phx.server"]

