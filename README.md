# LinkedInScraper

[![Build Status](https://travis-ci.com/ThiesDS/LinkedInScraper.svg?branch=main)](https://travis-ci.com/ThiesDS/LinkedInScraper)

## NOTE
This is a dockerized version fully refactored but inspired by the project [LinkedInScraping](https://github.com/federicohaag/LinkedInScraping).

## Setup

Install docker on your environment following [these](https://docs.docker.com/get-docker/) instructions.

Then, set the following environment variables:

```bash
export LINKEDIN_EMAIL=<YOUR LINKEDIN EMAIL>
export LINKEDIN_PASSWORD=<YOUR LINKEDIN PASSWORD>
```

## Input

The scraper need to know what you want to scrape. This is specified by a .txt file in the `/input/` folder. 

To scrape all posts with a certain hashtag, you have to list these hashtags in the file `input_hashtags.txt`. E.g. the file might look like this:

```
myfirsthashtag
mysecondhashtag
```

The app will go through all these hashtags, scrape the posts that contian these hashtags and store it in the `/output` folder.

## Usage

### Build image from Github

To build the application from scratch, pull the repository first. 

Navigate to the folder `/LinkedInScraper` and build the docker image with

```bash
docker build -t linkedinscraper:v0.3 .
```

Alter the version to your needs.

### Pull image from DockerHub

```bash
docker pull sventhies/linkedinscraper:v0.3
```

Alter the version to your needs.

### Run container 

After creating the image, you can run the app with 

```bash
docker run -v ${PWD}/input:/input \
           -v ${PWD}/output:/output \
           -e LINKEDIN_EMAIL=${LINKEDIN_EMAIL} \
           -e LINKEDIN_PASSWORD=${LINKEDIN_PASSWORD} \
           -e SCRAPER=profiles \
           -e SCROLL_DEPTH=10 \
           -e OUTPUT_FORMAT=csv \
           --shm-size=2gb \
           linkedinscraper:dev #v0.3
```

where `SCRAPER` can be one of `hashtags` or `profiles` depending on what you want to scrape (and what input you provided). If `SCRAPER=hashtags`,  `SCROLL_DEPTH` must be provided, otherwise this variable will be ignored. `SCROLL_DEPTH` can be used to controll the amount of posts scraped - this is a preliminary solution. Finally, `OUTPUT_FORMAT` can be one of `csv` or `json` depending on your prefered format of saving the output.

NOTE: The version has to be the same as in the build/pull of the image.
