FROM python:3.12.3
LABEL authors="BRIDGES"
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["fastapi","dev","app.py","--port", "8080"]