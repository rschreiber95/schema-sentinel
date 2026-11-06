FROM python:3.13-slim
WORKDIR /app
COPY runtimes/python/requirements.txt ./runtimes/python/requirements.txt
RUN pip install --no-cache-dir -r runtimes/python/requirements.txt
COPY generated/python ./generated/python
COPY runtimes/python ./runtimes/python
COPY testbed/tests ./testbed/tests
CMD ["python", "runtimes/python/main.py", "--serve"]
