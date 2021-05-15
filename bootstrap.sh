#!/usr/bin/env bash

sudo apt-get update
sudo apt-get --yes install git python3-venv

# Docker, instructions copied from
# https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
sudo apt-get --yes install apt-transport-https ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get --yes install docker-ce docker-ce-cli containerd.io

# Add user to docker group and enable.
sudo usermod -aG docker $USER
newgrp docker
