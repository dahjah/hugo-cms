FROM python:3.10-slim

# Install system dependencies (curl for fetching Hugo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Hugo Extended binary (the CMS requires it to generate static sites)
# Dynamically pull amd64 or arm64 depending on the deployment server's arch
ENV HUGO_VERSION=0.121.1
RUN ARCH=$(dpkg --print-architecture) && \
    curl -LO https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-${ARCH}.tar.gz \
    && tar -zxvf hugo_extended_${HUGO_VERSION}_linux-${ARCH}.tar.gz -C /usr/local/bin/ \
    && rm hugo_extended_${HUGO_VERSION}_linux-${ARCH}.tar.gz

WORKDIR /app

# Install Python requirements first to cache the layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project
COPY . .

# Expose the port Coolify will route to
EXPOSE 8000

# Run migrations and start standard Django standalone server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
