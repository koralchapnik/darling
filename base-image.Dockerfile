FROM python:3.8.3-alpine3.12
ENV PYTHONPATH /cep
COPY requirements.txt ./
RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
RUN apk --no-cache --update-cache add gcc gfortran build-base wget freetype-dev libpng-dev openblas-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir /cep
WORKDIR /cep
