{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    (pkgs.python3.withPackages (ps: with ps; [
      requests
      pydantic
      neo4j
      python-dotenv
      pandas
      numpy
      pillow
      redis
      beautifulsoup4
      feedparser
      minio
      boto3

      # Task Scheduler (Celery + PostgreSQL)
      celery
      flower
      psycopg2
      python-dateutil
      typer
      tabulate

      # Development
      pytest
      pytest-asyncio
    ]))

    # System packages
    pkgs.git
    pkgs.gnumake
    pkgs.postgresql_16
    pkgs.docker-compose
    pkgs.nodejs
    pkgs.uv
  ];
}

