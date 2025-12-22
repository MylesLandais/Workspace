# Image Graph Vectorizer

A production-ready Elixir application that combines image vectorization with hot-reloading, Neo4j graph database integration, and real-time file watching.

## Features

- **Hot-reloading**: Automatically processes new and modified images in real-time
- **Vector embeddings**: Generates image embeddings using external API (CLIP-compatible)
- **Graph database**: Stores images and their relationships in Neo4j with vector similarity search
- **Idempotent operations**: Safe to run multiple times without data loss
- **Fault-tolerant**: Built on Elixir/OTP with supervision trees
- **Parallel processing**: Utilizes all CPU cores for efficient batch processing

## Architecture

```
image_graph_vectorizer/
├── mix.exs                              # Project dependencies
├── config/
│   ├── config.exs                       # Main configuration
│   └── runtime.exs                      # Runtime-specific config
├── lib/
│   ├── image_graph_vectorizer.ex        # Public API
│   ├── image_graph_vectorizer/
│   │   ├── application.ex               # Application supervisor
│   │   ├── db/
│   │   │   └── neo4j.ex                 # Neo4j operations
│   │   ├── embedder.ex                  # Image embedding generation
│   │   ├── watcher.ex                   # File system watcher
│   │   └── processor.ex                 # Image processing logic
│   └── test/
└── README.md
```

## Setup

### Prerequisites

- Elixir 1.14+
- Neo4j 5.0+ with vector search capabilities
- Image embedding API (e.g., CLIP model server)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd image_graph_vectorizer
```

2. Install dependencies:
```bash
mix deps.get
```

3. Configure your environment:
```bash
export WATCH_DIR="/path/to/your/images"
export EMBEDDING_API="http://localhost:8100/v1/embeddings"
export NEO4J_PASSWORD="your_neo4j_password"
```

4. Update Neo4j configuration in `config/config.exs` if needed:
```elixir
config :bolt_sips, Bolt,
  url: "bolt://localhost:7687",
  basic_auth: [username: "neo4j", password: "your_password"],
  pool_size: 10,
  max_overflow: 5
```

### Running

Start the application:

```bash
iex -S mix
```

The application will:
1. Initialize Neo4j schema (constraints and vector indexes)
2. Perform initial batch scan of the watch directory
3. Start watching for file changes

## Usage

### Finding Similar Images

```elixir
# Find 5 most similar images to a query image
{:ok, similar_images} = ImageGraphVectorizer.find_similar("/path/to/query/image.jpg", 5)
```

### Getting Statistics

```elixir
{:ok, stats} = ImageGraphVectorizer.stats()
# Returns: %{total_images: 1000, total_topics: 25, images_with_topics: 950}
```

### Manual Directory Processing

```elixir
# Process a specific directory manually
ImageGraphVectorizer.process_directory("/path/to/new/images")
```

## Configuration

### Environment Variables

- `WATCH_DIR`: Directory to watch for images (default: "/path/to/images")
- `EMBEDDING_API`: Embedding API endpoint (default: "http://localhost:8100/v1/embeddings")
- `VECTOR_DIM`: Vector dimensions (default: "768")
- `NEO4J_PASSWORD`: Neo4j database password

### Application Config

In `config/config.exs`:

```elixir
config :image_graph_vectorizer,
  watch_dir: "/path/to/images",
  embedding_api: "http://localhost:8100/v1/embeddings",
  vector_dimensions: 768,
  image_extensions: [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
  batch_size: 50,
  processing_timeout: 30_000
```

## Key Improvements Over Python

### 1. Idempotency
- **Python**: Clears entire DB on every run (destructive)
- **Elixir**: Uses `MERGE` in Cypher - updates existing records, no data loss

### 2. Fault Tolerance
- **Python**: Script crash = monitoring stops
- **Elixir**: Supervisor automatically restarts crashed processes

### 3. Real-Time Processing
- **Python**: Manual re-run required for new files
- **Elixir**: `FileSystem` triggers instant processing on file changes

### 4. Concurrency
- **Python**: Sequential processing
- **Elixir**: Parallel processing using `Task.async_stream` with all CPU cores

### 5. Production Ready
- Environment-based configuration
- Proper error handling and logging
- Graceful degradation
- Resource management (connection pooling)

## Neo4j Schema

The application creates:

### Constraints
- `image_path_unique`: Ensures each image path is unique
- `topic_name_unique`: Ensures each topic name is unique

### Vector Index
- `image_embeddings`: Vector index for similarity search using cosine similarity

### Graph Model
```
(:Image {path, embedding, updated_at, size_kb, format})-[:BELONGS_TO]->(:Topic {name, created_at})
```

## API Integration

The application expects an embedding API that accepts:

```json
{
  "image_base64": ["<base64_encoded_image>"],
  "image_urls": []
}
```

And returns:

```json
{
  "embeddings": [[0.1, 0.2, 0.3, ...]]
}
```

## Deployment

### Docker

Create a `Dockerfile`:

```dockerfile
FROM elixir:1.14-alpine

WORKDIR /app
COPY . .

RUN mix deps.get --only prod
RUN mix compile

EXPOSE 4000

CMD ["mix", "run", "--no-halt"]
```

### Releases

Build a release for deployment:

```bash
MIX_ENV=prod mix release
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.