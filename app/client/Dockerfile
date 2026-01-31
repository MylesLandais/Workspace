# 1) Base Bun image
FROM oven/bun:1.1 AS base
WORKDIR /app

# 2) Install dependencies in a cached layer
FROM base AS deps
COPY bun.lockb package.json ./
RUN echo "[BUILD] Installing system dependencies..." && \
    apt-get update && apt-get install -y python3 build-essential && \
    echo "[BUILD] Installing Node modules..." && \
    bun install --frozen-lockfile && \
    echo "[BUILD] Dependencies installed successfully"

# 3) Test/build stage
FROM base AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=test
# run unit tests during build
RUN echo "[BUILD] Running tests..." && \
    bun test && \
    echo "[BUILD] Tests passed"

# Build the Next.js app
RUN echo "[BUILD] Building Next.js application..." && \
    echo "[BUILD] Environment: ${NODE_ENV}" && \
    bun run build && \
    echo "[BUILD] Build complete"

# 4) Runtime image
FROM base AS runtime
WORKDIR /app
ENV NODE_ENV=production

# Copy only what's needed for the runtime
RUN echo "[RUNTIME] Preparing runtime environment..."
COPY --from=build /app/public ./public
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
RUN echo "[RUNTIME] Files copied successfully"

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD curl -f http://localhost:3000/api/health || exit 1

RUN echo "[RUNTIME] Container ready"
CMD echo "[RUNTIME] Starting application..." && bun run server.js
