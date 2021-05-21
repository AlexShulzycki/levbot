FROM arm32v7/python:buster

COPY Client .

RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
RUN apt-get update
RUN apt-get install python3-tflite-runtime -y

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
RUN tar -zxvf ta-lib-0.4.0-src.tar.gz
RUN cd ta-lib && ./configure --prefix=/usr && make && make install


RUN pip3 install --no-cache-dir -r requirements.txt



EXPOSE 80

CMD ["python", "./server.py"]
