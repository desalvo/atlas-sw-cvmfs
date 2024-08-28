FROM centos:7
ARG TARGETPLATFORM
LABEL maintainer="Alessandro.DeSalvo@roma1.infn.it"

RUN sed -i s/mirror.centos.org/vault.centos.org/g /etc/yum.repos.d/*.repo && \
    sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/*.repo && \
    sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/*.repo
RUN yum -y install epel-release && yum -y install openssh-clients singularity
RUN groupadd -g 320 cvatlas && useradd -ms /bin/bash -u 320 -g 320 cvatlas
COPY buildSingularityImage buildApptainerImage /usr/local/bin/
