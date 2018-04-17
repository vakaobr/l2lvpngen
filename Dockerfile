FROM python:3

ADD requirements.txt /requirements.txt
RUN pip install -r requirements.txt
ADD l2lvpngen.py /l2lvpngen.py
