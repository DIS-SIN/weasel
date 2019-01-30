# Use an official Python runtime as a parent image
FROM python:3.7-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 5052

# Define environment variable
ENV NAME weasel

# UNCOMMENT WHEN APPLICATION IS READY
# Run app.py when the container launches
# CMD ["python", "application.py"]

# COMMENT OUT WHEN APPLICATION READY
# UI TEST
CMD ["python", "application.py"]

############################################################################
# docker for newbs manpage
# Working windows? probably are, if so:
# Get docker! It's awesome, but there's a learning curve
#
# So...
#
# Watch this: https://www.youtube.com/watch?v=YFl2mCHdv24
# Go here: https://hub.docker.com/editions/community/docker-ce-desktop-windows
# Go here: https://hub.docker.com/?ref=login
# Go here: https://docs.docker.com/get-started/
# Go here: https://docs.docker.com/machine/overview/
# Go here: https://hub.docker.com/_/python
# Go here: https://denibertovic.com/posts/handling-permissions-with-docker-volumes/
# Go here: https://docs.docker.com/storage/bind-mounts/
# go here: https://rominirani.com/docker-tutorial-series-part-3-more-on-images-and-containers-68ce7a026fc1
#
# -- IN DOCKERFILE
# -- this is going to make 5050 available to the actual machine in the real world
#
# EXPOSE 5051
#
# -- IN FLASK APP
# -- this is magic, the zeros allow you to tap into the arcane 
# -- and let the real world find you
#
# app.run(host = '0.0.0.0', port=5052)
#
# -- IN GIT BASH: PRE LAUNCH CLEANUP
# -- If you like to test, probably need to clean up
# -- the ### is the first 3 alpha/num of the item (container or image)
#
# docker container ls
# docker container stop ###
# docker rm ###
# docker image ls
# docker rmi ###
#
# -- IN GIT BASH: Start the docker magic
# -- note the period. That's key magic
# docker build --tag=weasel .
#
# -- note the /tcp, That's key magic
# -- you are punching a hole through realities and wiring them up
#
# docker run -p 5052:5052/tcp weasel
#
# -- in the real world
# http://localhost:5052/
#
# Celebrate human, it used to take a team of dev ops to do what you just did
# the future, tis wow.
#
# Oh and one more tip. Use Git Bash (from MINGW64), it's worth it
#