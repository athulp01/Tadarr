FROM python:3-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev
# Copy files to container
COPY . /app

RUN	pip install --no-cache-dir -r requirements.txt --upgrade

RUN apk del gcc musl-dev libffi-dev

ENTRYPOINT ["python", "/app/tadarr.py"]
