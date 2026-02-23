FROM jrottenberg/ffmpeg:6.0-ubuntu

RUN apt update && apt install -y python3 python3-pip

WORKDIR /app
COPY . .

RUN pip3 install -r requirements.txt

CMD ["python3", "bot.py"]
