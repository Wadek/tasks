FROM python:3.12-alpine
WORKDIR /app
COPY app/ /app/
ENV DATA_FILE=/data/tasks.json
EXPOSE 8080
CMD ["python", "server.py"]
