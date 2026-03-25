FROM python:3.10-slim

# Install system dependencies (curl for fetching Hugo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Hugo Extended binary (the CMS requires it to generate static sites)
# Using the same version you were using locally (0.121.1)
ENV HUGO_VERSION=0.121.1
RUN curl -LO https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz \
    && tar -zxvf hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz -C /usr/local/bin/ \
    && rm hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz

WORKDIR /app

# Install Python requirements first to cache the layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project
COPY . .

# Expose the port Coolify will route to
EXPOSE 8000

# Run standard Django standalone server
# (Note: For a true high-volume production setup, you could change this to gunicorn,
# but for internal CMS usage runserver works flawlessly out of the box).
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
