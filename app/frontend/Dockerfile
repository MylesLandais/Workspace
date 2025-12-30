FROM oven/bun:latest

WORKDIR /app

# Copy package files
COPY package.json bun.lockb* ./

# Install dependencies
RUN bun install

# Copy source code
COPY . .

# Expose Astro dev server port
EXPOSE 4321

# Start dev server
CMD ["bun", "run", "dev", "--host", "0.0.0.0"]


