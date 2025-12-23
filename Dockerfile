FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
# run tests by default
CMD ["/bin/bash", "./run_test.sh", "all"]
