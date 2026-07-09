# Linux Shell Scripting

Shell scripting automates tasks in the Linux terminal.

## Basic commands
- ls lists files
- grep searches text
- find locates files by name or date
- sed and awk process text streams

## Variables
Bash uses VAR=value without spaces. Access with $VAR or ${VAR}.

## Control structures
if [ -f somefile ]; then
  echo "file exists"
fi

## Relationship with Docker
Many Dockerfiles use shell scripting for container setup. See [[permanentes/docker-essentials|Docker Essentials]] for details. Mastering bash helps write efficient Docker images.
