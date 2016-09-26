sudo yum update -y

sudo yum install git
mkdir gspotsyncer
cd gspotsyncer/

git clone https://github.com/jumpinghooligans/gspotsyncer.git .

sudo curl -fsSL https://get.docker.com/ | sh

curl -L https://github.com/docker/compose/releases/download/1.8.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

exit

cd gspotsyncer
sudo service docker start
docker-compose up -d