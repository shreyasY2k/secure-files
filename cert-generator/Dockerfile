FROM alpine:latest

RUN apk add --no-cache openssl

COPY generate-certs.sh /generate-certs.sh
RUN chmod +x /generate-certs.sh

CMD ["/generate-certs.sh"]