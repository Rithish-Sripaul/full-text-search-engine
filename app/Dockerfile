FROM python:3.10

LABEL MAINTAINER="Rithish Sripaul <rithishsripaul@gmail.com>"

ENV GROUP_ID=1000 \
    USER_ID=1000 

# Set working directory
WORKDIR /var/www/

# Install required system packages
RUN apt-get update && apt-get install -y \
    ghostscript \
    tesseract-ocr \
    pngquant \
    unpaper \
    libleptonica-dev \
    automake \
    make \
    pkg-config \
    libsdl-pango-dev \
    libicu-dev \
    libcairo2-dev \
    bc \
    ffmpeg \
    libsm6 \
    libxext6 \
    wget \
    unzip \
    libpango1.0-dev && \
    rm -rf /var/lib/apt/lists/*

# Verify installations
RUN tesseract --version && \
    gs --version && \
    pngquant --version && \
    unpaper --version

# Add requirements.txt and install Python dependencies
ADD ./requirements.txt /var/www/requirements.txt
RUN pip install -r requirements.txt

# Add the application code
ADD . /var/www/

# Install gunicorn for production use
RUN pip install gunicorn

# Ensure the converted_pdf directory exists
RUN mkdir -p /var/www/converted_pdf

# Set the appropriate permissions for converted_pdf directory
RUN chmod -R 777 /var/www/converted_pdf

# Create the www user and group, and set them for running the application
RUN addgroup -gid $GROUP_ID www
RUN adduser --disabled-password --uid $USER_ID --ingroup www --shell /bin/sh www

# Set proper environment variables
ENV PATH="/usr/local/bin:${PATH}"

# Switch to the www user
USER www

# Expose port 5000 for the Flask application
EXPOSE 5000

# Start the application using Gunicorn with 4 workers
CMD [ "gunicorn", "-w", "4", "--timeout", "300", "--bind", "0.0.0.0:5000", "wsgi:app"]