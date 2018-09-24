FROM gcr.io/google-appengine/python

# Create the venv for dependencies
RUN virtualenv -p python3.6 /env

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

# Copy req file and install dependencies
ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Add app source code to image
ADD . /app

# expose port 25
EXPOSE 25

CMD [ "python", "./main.py" ]