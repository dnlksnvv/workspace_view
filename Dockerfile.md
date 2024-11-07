
FROM mongo:latest


VOLUME /data/db


CMD ["mongod"]