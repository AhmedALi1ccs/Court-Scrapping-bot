# Use wine to build Windows executables on non-Windows systems
FROM ubuntu:20.04

# Prevent timezone prompt
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wine64 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Windows Python using Wine
RUN wget https://www.python.org/ftp/python/3.9.0/python-3.9.0-amd64.exe \
    && wine64 python-3.9.0-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 \
    && rm python-3.9.0-amd64.exe

# Set up Wine Python
ENV WINEPATH="C:\\users\\root\\AppData\\Local\\Programs\\Python\\Python39\\python.exe"

# Set working directory
WORKDIR /app

# Copy your application files
COPY . /app/

# Install requirements using Windows Python
RUN wine64 python -m pip install -r requirements.txt
RUN wine64 python -m pip install pyinstaller

# Create the executable
RUN wine64 python -m PyInstaller --onefile --add-data "templates;templates" --name CourtScraper run.py

CMD ["bash"]
