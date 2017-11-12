FROM python:3.6
ADD ./src /smtpd
WORKDIR /smtpd
RUN pip install -r requirements.txt
CMD python -u app.py

