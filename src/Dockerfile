FROM python:3.9.0-buster
LABEL maintainer "Sven Thies <sven_thies@web.de>"

# Update the package list and install chrome
# Set up the Chrome PPA
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Update the package list and install chrome
RUN apt-get update -y
RUN apt-get install -y google-chrome-stable

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install python requirements
COPY requirements.txt .
RUN pip install --requirement requirements.txt

# Create app folder and copy
RUN mkdir /app/
WORKDIR /app/
COPY app .

# Add non-root user
RUN useradd -ms /bin/bash Scraper
USER Scraper

# Run app
CMD ["python","main.py"]