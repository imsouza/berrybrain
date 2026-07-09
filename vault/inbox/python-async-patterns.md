# Python Async Patterns

Python 3.12+ offers mature asyncio for I/O-bound workloads.

## async/await
The async/await syntax enables non-blocking I/O. Use asyncio.gather() to run multiple coroutines concurrently. This is ideal for API calls, database queries, and file operations.

## FastAPI
FastAPI is an async-native web framework. Routes are async def by default, with a thread pool for sync operations. Combined with uvicorn, it delivers high throughput for web APIs.

## When to use async
- I/O intensive workloads (APIs, databases, files): async is ideal
- CPU intensive workloads (crypto, ML): use ProcessPoolExecutor instead

## Deployment
FastAPI packaged in [[permanentes/docker-essentials|Docker]] simplifies deployment with uvicorn and healthcheck probes. Shell scripts for [[permanentes/linux-shell-scripting|automation]] manage the container lifecycle.
