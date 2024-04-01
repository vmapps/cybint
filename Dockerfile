FROM python:alpine3.19

COPY . /cybint

RUN pip3 install --no-cache-dir -r /cybint/requirements.txt
RUN python3 -m nltk.downloader -d ./nltk_data punkt
RUN python3 -m nltk.downloader -d ./nltk_data averaged_perceptron_tagger
RUN chmod 755 /cybint/manage.py

EXPOSE 8000

WORKDIR /cybint/app/

# ENTRYPOINT [ "python3", "main.py" ]
CMD /usr/sbin/crond -b && python3 main.py

# CMD [ "-m" , "flask", "run", "--host=0.0.0.0", "--port", "8000"]
