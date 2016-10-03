# gspotsyncer
Sync Spotify and Google Music playlists together

## Setup and Install
```
sudo yum update -y
sudo yum install git -y
mkdir gspotsyncer
cd gspotsyncer/
git clone https://github.com/jumpinghooligans/gspotsyncer.git .

sudo su
curl -fsSL https://get.docker.com/ | sh
usermod -aG docker ec2-user
curl -L https://github.com/docker/compose/releases/download/1.8.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```
logout and log back in for everything to take effect

```
cd gspotsyncer
sudo service docker start
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

there's some fuckery around jenkins/ file permissions - until I figure out how to pre-permission the volume or move to a SCM sync implementation I've been running a (bad) chmod:
```
sudo chmod -R 777 jenkins/
```
