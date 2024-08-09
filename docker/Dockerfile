FROM slac_epics_base_rhel7

RUN pip3.6 install --upgrade pip

COPY ../requirements.txt /BEAMS/
RUN cd BEAMS && pip3.6 install -r requirements.txt

COPY ../beams/ /BEAMS/beams
COPY ../tests/ /BEAMS/tests
COPY ../venv/ /BEAMS/venv
COPY docker/Makefile /BEAMS/
COPY ../setup.py /BEAMS/
RUN cd BEAMS && make update_beams && make gen_grpc
