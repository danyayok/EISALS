# СТАДИЯ 1: Сборка CSS
FROM node:18-alpine AS css-builder
WORKDIR /build
COPY package*.json tailwind.config.js ./
COPY ./app/templates ./app/templates
COPY ./app/static/css/input.css ./app/static/css/input.css
RUN npm install
RUN npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/styles.css --minify

# СТАДИЯ 2: Python сервер
FROM python:3.13
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=css-builder /build/app/static/css/styles.css ./app/static/css/styles.css

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
