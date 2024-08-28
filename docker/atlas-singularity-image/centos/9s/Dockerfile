FROM quay.io/centos/centos:stream9
ARG TARGETPLATFORM
ARG TARGETPLATFORM
LABEL maintainer="Alessandro.DeSalvo@roma1.infn.it"

RUN dnf -y install dnf-plugins-core
RUN dnf config-manager --set-enabled crb
RUN yum -y install epel-release && yum -y install openssh-clients apptainer apptainer-suid
RUN groupadd -g 320 cvatlas && useradd -ms /bin/bash -u 320 -g 320 cvatlas
COPY buildSingularityImage buildApptainerImage /usr/local/bin/
