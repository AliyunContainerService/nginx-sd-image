FROM nginx:1.9.8
MAINTAINER Chang Hai Yan <danielyanch@hotmail.com>
#ADD sources.list /etc/apt/sources.list
ADD serviceSync.py /usr/local/bin/serviceSync.py
ADD supervisord.conf /etc/supervisord.conf
# install
RUN apt-get update && \
    apt-get install --force-yes -y curl python supervisor && \
    chmod +x /usr/local/bin/serviceSync.py && \
    echo "* * * * * root /usr/local/bin/serviceSync.py > /dev/null 2>&1" >> /etc/crontab

CMD supervisord -n
