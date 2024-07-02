# Use Ubuntu 20.04 as base image
FROM ubuntu:20.04

# Set environment variables to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update and install necessary dependencies
RUN apt-get update && apt-get install -y \
    sudo \
    software-properties-common \
    git \
    libusb-1.0-0-dev \
    usbutils \
    android-tools-adb \
    udev \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    gfortran \
    libblas-dev \
    liblapack-dev \
    gcc \
    libcairo2 \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    shared-mime-info && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    pkg-config \
    python3-pip \
    python3-cffi \
    python3.10 \
    python3.10-venv \
    python3.10-dev && \
    apt-get clean

# Create a symlink for python
RUN ln -s /usr/bin/python3.10 /usr/bin/python    

# Add a non-root user and give sudo privileges
RUN useradd -m -s /bin/bash devuser && \
    echo "devuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER devuser
WORKDIR /home/devuser

# Copy udev rules to the container
COPY 99-usb-serial.rules /etc/udev/rules.d/

# Ensure USB devices are accessible by the non-root user
RUN sudo usermod -a -G dialout devuser

# Copy package list and install additional packages
COPY packages.list /tmp/
RUN sudo apt-get update && sudo apt-get install -y dselect && sudo dpkg --set-selections < /tmp/packages.list && sudo apt-get dselect-upgrade -y

# Clone the repository and set up the environment
RUN git clone https://github.com/abhishek-tiwari01/FlightControllerTestSuite.git
WORKDIR /home/devuser/FlightControllerTestSuite

# Install the latest pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3.10 get-pip.py

# Install numpy and pyserial globally using pre-built wheel to avoid compilation issues
RUN python3.10 -m pip install --no-cache-dir numpy pyserial

# Install the remaining Python dependencies
COPY requirements.txt .
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

# Ensure PATH is set correctly and Python path is correctly recognized
RUN echo 'export PATH="$PATH:/home/devuser/.local/bin"' >> /home/devuser/.bashrc
RUN echo 'export PYTHONPATH="$PYTHONPATH:/home/devuser/.local/lib/python3.10/site-packages"' >> /home/devuser/.bashrc

# Add the user to the dialout group
RUN sudo usermod -a -G dialout devuser

# Disable ModemManager
# RUN sudo apt-get remove modemmanager brltty

# Remove unnecessary services
RUN sudo apt-get remove -y modemmanager brltty && sudo apt-get autoremove -y && sudo apt-get clean

# Verify the installation of cffi and weasyprint
RUN python3 -m pip install --no-cache-dir weasyprint cffi && \
    python3 -c "import cffi; import weasyprint"

# Default command to run when the container starts
CMD ["/bin/bash"]

# docker run --privileged -v /dev/bus/usb:/dev/bus/usb -v /dev/serial:/dev/serial -it flight-controller-test-suite
