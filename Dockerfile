FROM python:3.11-slim

# Устанавливаем ffmpeg
RUN apt update && apt install -y ffmpeg \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Сначала копируем зависимости (кешируется лучше)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Потом копируем остальной код
COPY . .

CMD ["python", "bot.py"]
