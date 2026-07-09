# Docker Essentials

Docker solves the "works on my machine" problem with isolated containers.

## Key concepts
- Image: read-only template built from a Dockerfile
- Container: running instance of an image
- Volume: persistent data outside the container
- Network: communication between containers

## Basic Dockerfile
A Dockerfile defines the image build steps: base image, working directory, copying files, installing dependencies, and a start command.

## Best practices
- Use slim/alpine images to reduce size
- Combine RUN commands to reduce layers
- Use .dockerignore to skip git and build artifacts

## Integration
Shell automation with [[permanentes/linux-shell-scripting|bash scripting]] is ideal for container entrypoints and healthchecks. Async Python apps like [[inbox/python-async-patterns|FastAPI with asyncio]] deploy easily in containers.
