FROM python:3.11-alpine
ENV PROJECT_NAME=pyupnp-server
ENV WORKDIR=/${PROJECT_NAME}
WORKDIR ${WORKDIR}
ADD . ${WORKDIR}/${PROJECT_NAME}

ARG DJANGO_SUPERUSER_USERNAME=admin
ARG DJANGO_SUPERUSER_EMAIL=admin@localhost
ARG DJANGO_SUPERUSER_PASSWORD=admin

RUN eval "pip install ${WORKDIR}/${PROJECT_NAME}" \
    && rm -r ${WORKDIR}/${PROJECT_NAME}
RUN manage collectstatic
RUN manage migrate --run-syncdb
RUN manage createsuperuser --no-input

ENTRYPOINT ["manage"]
CMD ["runserver", "0.0.0.0:9000"]

EXPOSE 9000