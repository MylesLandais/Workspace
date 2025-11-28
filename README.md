# Maya

A versatile Discord bot built in Go, designed to enhance your server with music streaming capabilities and integration with generative AI systems for media creation, article summarization, and more.

## Features

- **Music Streaming**: Stream music directly in your Discord voice channels.
- **AI Integration**: Communicate with generative AI systems to create media, summarize articles, and perform various AI-powered tasks.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/System-Nebula/maya.git
   cd maya
   ```

2. Install dependencies:
   ```
   go mod tidy
   ```

3. Set up your environment variables (e.g., Discord bot token, AI API keys).

4. Build and run:
   ```
   nix build
   ./result/bin/maya
   ```

## Development with Nix

This project uses Nix for reproducible development environments. To get started:

1. Ensure Nix is installed with flakes support.

2. Enter the development shell:
   ```
   nix develop
   ```
   Or if using nix-shell:
   ```
   nix-shell
   ```

3. Within the shell, you can run `go build` or `go run main.go` as usual.

4. To build the project using Nix:
   ```
   nix build
   ```

## Usage

TBD

