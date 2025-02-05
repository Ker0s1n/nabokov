sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker # start docker permissions without reboot

sudo service docker restart # start docker without reboot