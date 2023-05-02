# Use the official Python image as the base image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libsdl2-dev alsa-utils\
    && rm -rf /var/lib/apt/lists/*

# Copy the pyproject.toml file and install Python dependencies
COPY pyproject.toml ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install

# Clone the whispercpp repository and build the wheel
RUN git clone https://github.com/aarnphm/whispercpp.git && \
    cd whispercpp && \
    git submodule update --init --recursive && \
    python3 -m build -w && \
    pip install dist/*.whl

RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    npm install --global yarn

# Copy the rest of the application code
COPY . .

# Start the application
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
