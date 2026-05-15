FROM python:3.12-slim

WORKDIR /opt/elephant

COPY . /opt/elephant/

RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir -e .

ENV ELEPHANT_HOME=/var/lib/elephant

ENTRYPOINT ["elephant"]
CMD ["health"]
