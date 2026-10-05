FROM python:3.13.7-alpine3.22

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MAILFORGE_SINK_DATA=/var/lib/mailforge/sink

WORKDIR /opt/mailforge
COPY server.py /opt/mailforge/server.py
EXPOSE 2525
CMD ["python", "/opt/mailforge/server.py"]
