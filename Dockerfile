FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    build-essential \
    g++-mingw-w64-x86-64 \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

CMD ["sh", "-c", "make clean && make CC=x86_64-w64-mingw32-g++"]