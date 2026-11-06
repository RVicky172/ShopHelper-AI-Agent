# One image, two runtimes:
#  - ECS Fargate runs uvicorn directly behind the ALB.
#  - Lambda runs the same container; the AWS Lambda Web Adapter extension translates
#    Lambda invokes into plain HTTP requests to uvicorn on :8080.
FROM public.ecr.aws/docker/library/python:3.13-slim

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src \
    PORT=8080 \
    AWS_LWA_PORT=8080 \
    AWS_LWA_READINESS_CHECK_PATH=/health

WORKDIR /app
# Hash-pinned dependencies exported from uv.lock (uv export --no-dev --no-emit-project)
COPY requirements.txt .
RUN pip install --require-hashes -r requirements.txt

COPY src/ src/

RUN useradd --create-home app
USER app

EXPOSE 8080
CMD ["uvicorn", "shophelper.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
