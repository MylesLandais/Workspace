FROM oven/bun:1-alpine

WORKDIR /app

COPY package.json .

# Install dependencies using Bun
# NOTE: Removed bun.lockb reference as it is not present in the workspace.
RUN bun install

COPY . .

# vite run dev uses the script defined in package.json
CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0"]
