# Use the official Python slim image as the base
FROM python:3.1-slim

# Set the working directory inside the container
WORKDIR /app

# Set up environment variables for SOCKS proxy
ENV HTTP_PROXY=<SOCKS_PROXY>
ENV HTTPS_PROXY=<SOCKS_PROXY>

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libappindicator3-1 \
    libasound2 \
    fonts-liberation \
    libnspr4 \
    libx11-xcb1 \
    libxss1 \
    libxtst6 \
    proxychains4 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies using pip through the proxy
RUN proxychains4 pip install --no-cache-dir selenium pandas webdriver-manager

# Copy application files to the container
COPY TikTok_Scraping_Selenium.py /app/
COPY sample_5k.json /app/

# Set environment variable to disable SSL verification
ENV PYTHONUNBUFFERED=1

# Command to run the Python script
CMD ["proxychains4", "python", "TikTok_Scraping_Selenium.py"]
