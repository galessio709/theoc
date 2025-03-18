# Frontend stage
FROM node:16.14.2-slim AS frontend

RUN mkdir /app
WORKDIR /app

COPY frontend/ ./
RUN npm install -y
RUN npm run build

# Backend stage
FROM python:3.9-slim AS backend

ENV MODE=PRODUCTION

RUN mkdir /app
WORKDIR /app

RUN apt-get -y update && apt-get -y install git

COPY backend/ ./
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

# Copy frontend build to backend static directory
COPY --from=frontend /app/dist /app/static

# Expose port and start the server
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]