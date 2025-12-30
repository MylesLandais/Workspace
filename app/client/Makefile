# Bunny Client - Development Commands
# All commands run inside Docker containers

DOCKER_IMAGE = oven/bun:1.1-slim
WORKDIR = /app
DOCKER_RUN = docker run --rm -it -v $(PWD):$(WORKDIR) -w $(WORKDIR) $(DOCKER_IMAGE)

.PHONY: init dev build clean

# Initialize Next.js project (run once)
init:
	@echo "Initializing Next.js project with Bun..."
	$(DOCKER_RUN) bunx create-next-app@latest . \
		--typescript \
		--tailwind \
		--eslint \
		--app \
		--src-dir \
		--no-import-alias \
		--package-manager bun \
		--yes
	@echo "Installing additional dependencies..."
	$(DOCKER_RUN) bun add lucide-react
	$(DOCKER_RUN) bun add -d vitest @vitejs/plugin-react jsdom
	@echo "Done! Run 'make dev' to start development server."

# Start development server
dev:
	docker compose up --build

# Build for production
build:
	$(DOCKER_RUN) bun run build

# Install dependencies (after pulling)
install:
	$(DOCKER_RUN) bun install

# Clean generated files
clean:
	rm -rf node_modules .next
