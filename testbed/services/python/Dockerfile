FROM python:3.13-slim

WORKDIR /app

COPY services/python/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --requirement /app/requirements.txt

COPY proto /app/proto
RUN mkdir -p /app/generated \
    && touch /app/generated/__init__.py \
    && python -m grpc_tools.protoc \
        --proto_path=/app/proto \
        --python_out=/app/generated \
        /app/proto/testbed.proto

COPY services/python/src /app/src

ENV PYTHONPATH=/app

CMD ["python", "-m", "src.app"]
