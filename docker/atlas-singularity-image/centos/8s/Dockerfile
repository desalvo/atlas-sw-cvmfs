FROM cern/cs8-base
ARG TARGETPLATFORM
LABEL maintainer="Alessandro.DeSalvo@roma1.infn.it"

RUN yum -y install epel-release && yum -y install openssh-clients singularity
RUN groupadd -g 320 cvatlas && useradd -ms /bin/bash -u 320 -g 320 cvatlas
COPY buildSingularityImage buildApptainerImage /usr/local/bin/
