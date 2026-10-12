FROM alpine:3.22
RUN apk add --no-cache postfix cyrus-sasl-login ca-certificates python3
COPY run.py sender_header.py /
CMD ["python3", "/run.py"]
