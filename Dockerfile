FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
# set safe defaults for environment (can be overridden at runtime)
ENV PAYMENT_TOKEN="tok_example"
ENV MAIL_SERVER_KEY="mail_example"
ENV INTERNAL_AUTH_SECRET="secret_example"
ENV ALLOWED_NOTIFY_HOSTS="localhost,127.0.0.1"

CMD ["python", "auto_test.py"]
