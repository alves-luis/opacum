FROM python:3.8.2
RUN pip3 install flask docker
COPY . /flask
WORKDIR /flask
ENV FLASK_APP=app.py
EXPOSE 5000
CMD python3 app.py
