# Base image: pinned Python 3.12 (Debian slim) from the pre-approved
# public.ecr.aws/docker/library mirror.
#

FROM public.ecr.aws/docker/library/python@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Lattice-reduction library (fpylll) and its numeric/signal dependencies, plus
# the verifier's test runner. All pinned.
RUN pip install --no-cache-dir \
    cysignals==1.12.6 \
    fpylll==0.6.4 \
    pytest==8.3.4 \
    pytest-json-ctrf==0.3.5


COPY data /app/data
