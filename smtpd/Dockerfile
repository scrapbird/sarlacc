FROM alpine

# Install python3.6
RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
	if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
	rm -r /root/.cache

# Install psycopg2 deps
RUN apk add postgresql-dev gcc python3-dev musl-dev

# Set up project
ADD ./src /smtpd
WORKDIR /smtpd
RUN pip install -r requirements.txt

# Add user
RUN adduser -S sarlacc
RUN mkdir -p /home/sarlacc/.config/radare2 \
        && touch /home/sarlacc/.radare2rc
RUN chown -R sarlacc /home/sarlacc/
USER sarlacc

CMD python -u app.py

