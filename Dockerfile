FROM jupyter/minimal-notebook 

# grab thermocalc executable
COPY --from=thermocalc/thermocalc:3.50 /bin/thermo /bin/thermo

# copy in tawnycalc 
COPY . /home/jovyan/tawnycalc

WORKDIR /home/jovyan/tawnycalc/examples

ENV PYTHONPATH=$PYTHONPATH:/home/jovyan/tawnycalc/
ENV THERMOCALC_EXECUTABLE=/bin/thermo

# add other things
USER root
RUN pip install -q tabulate matplotlib
USER jovyan