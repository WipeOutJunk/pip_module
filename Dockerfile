# Используем Python образ
FROM python:3.10-slim

# Установим рабочую директорию
WORKDIR /app

# Скопируем файлы проекта
COPY . /app

# Установим системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Установим зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Убедимся, что nltk данные загружаются при сборке контейнера
RUN python -m nltk.downloader stopwords punkt

# Укажем порт для Flask
EXPOSE 5000

# Команда для запуска приложения
CMD ["python", "app.py"]