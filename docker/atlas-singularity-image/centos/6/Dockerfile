FROM centos:6
ARG TARGETPLATFORM
LABEL maintainer="Alessandro.DeSalvo@roma1.infn.it"

COPY CentOS-Base.repo /etc/yum.repos.d
RUN yum -y install epel-release && yum -y install openssh-clients singularity
RUN groupadd -g 320 cvatlas && useradd -ms /bin/bash -u 320 -g 320 cvatlas
COPY buildSingularityImage /usr/local/bin/
