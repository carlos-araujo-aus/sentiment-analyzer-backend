# Use a recent, lightweight official Python image as a base.
# 'slim' is a minimal variant that reduces the final image size.
FROM python:3.11-slim

# Set environment variables for optimizing Python in containerized environments.
# PYTHONDONTWRITEBYTECODE=1: Prevents Python from writing .pyc files to the container.
# PYTHONUNBUFFERED=1: Ensures that Python output (like 'print' statements) is sent
#                   straight to the terminal, which makes viewing logs easier.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container. All subsequent commands
# (COPY, RUN) will be executed from this path.
WORKDIR /app

# Copy and install Python dependencies. We don't need system-level dependencies
# (like libpq-dev) because the psycopg2-binary package already includes them.
# Copying the requirements file first leverages Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code into the container.
COPY . .

# Create a system-level group and user with limited permissions for security.
# This is a critical security best practice ("hardening").
RUN addgroup --system appgroup && adduser --system --no-create-home --ingroup appgroup appuser

# Change the ownership of the application files to the new user.
RUN chown -R appuser:appgroup /app

# Switch to the non-privileged user to run the application. From this point on,
# all commands will be executed as 'appuser'.
USER appuser

# The command to run when a container is started from this image.
# We use the "shell" form to allow the expansion of the $PORT environment variable,
# which is injected by the deployment platform (e.g., DigitalOcean App Platform).
#
# gunicorn: Our production-ready WSGI server.
# --bind 0.0.0.0:$PORT: Binds Gunicorn to all network interfaces on the port
#                       specified by the $PORT variable.
# run:app: Tells Gunicorn to look for an object named 'app' inside the 'run.py' file.
CMD gunicorn --bind 0.0.0.0:$PORT run:app