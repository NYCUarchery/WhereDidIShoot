FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS dev

COPY app ./app
COPY gunicorn.conf.py ./
COPY wsgi.py ./

ENV FLASK_APP=wsgi:app
ENV FLASK_DEBUG=1

EXPOSE 5000

CMD ["flask", "run", "--debug", "--host=0.0.0.0", "--port=5000"]

FROM base AS runtime

COPY app ./app
COPY gunicorn.conf.py ./
COPY wsgi.py ./

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
