FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/static
RUN chmod -R 755 /app/static  # Set permissions

EXPOSE 8000

ENTRYPOINT [ "sh", "entrypoint.sh" ]