# 1) Base Bun image
FROM oven/bun:1.1 AS base
WORKDIR /app

# 2) Install dependencies in a cached layer
FROM base AS deps
COPY bun.lockb package.json ./
RUN bun install --frozen-lockfile

# 3) Test/build stage
FROM base AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=test
# run unit tests during build
RUN bun test

# Build the Next.js app
RUN bun run build

# 4) Runtime image
FROM base AS runtime
WORKDIR /app
ENV NODE_ENV=production

# Copy only what's needed for the runtime
COPY --from=build /app/public ./public
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["bun", "run", "server.js"]
