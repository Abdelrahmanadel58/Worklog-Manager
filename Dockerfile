#FROM python:3.11-slim

#WORKDIR /app

#COPY requirements.txt requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt

#COPY . .

#ENV FLASK_APP=app.py

#CMD ["flask", "run", "--host=0.0.0.0"]

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
