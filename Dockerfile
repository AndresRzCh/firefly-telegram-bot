# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY bot/requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY bot/ ./

# Make the data directory
RUN mkdir -p /usr/src/app/data

# Run bot.py when the container launches
CMD ["python", "./bot.py"]
