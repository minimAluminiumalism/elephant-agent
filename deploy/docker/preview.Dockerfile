FROM python:3.12-slim

WORKDIR /srv/site

COPY apps/site/dist/ /srv/site/

EXPOSE 8080

CMD ["python3", "-m", "http.server", "8080", "--directory", "/srv/site"]
