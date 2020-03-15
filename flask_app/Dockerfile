FROM python:3.8.2
RUN pip3 install flask
COPY . /flask
WORKDIR /flask
ENV FLASK_APP=app.py
EXPOSE 5000
CMD flask run --host=0.0.0.0
