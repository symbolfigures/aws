#!/bin/bash


# AMI SETUP


# IAM =================================================================


# role
# name: ChatbotEC2InstanceProfile
# policies:
# - AmazonEC2ContainerRegistryReadOnly
# - AmazonElasticContainerRegistryPublicFullAccess
# - AmazonSSMManagedInstanceCore
# - CloudWatchAgentServerPolicy
# - ChatbotAppPolicy

# security group
# name: ec2-pub-sg
# inbound:
# - 443 0.0.0.0/0
# - 80 0.0.0.0/0
# - 22 myIP
# outbound:
# - all


sudo su


# PACKAGES =================================================================


dnf install -y certbot docker fail2ban iptables-services nginx;
aws s3 cp s3://<DOMAIN>/files.zip .;
unzip files.zip


# SSL =================================================================


mkdir -p /etc/letsencrypt/live/<DOMAIN>/;
mv files/fullchain.pem /etc/letsencrypt/live/<DOMAIN>/fullchain.pem;
mv files/privkey.pem /etc/letsencrypt/live/<DOMAIN>/privkey.pem;
chown -R nginx:nginx /etc/letsencrypt/live/<DOMAIN>;
mv files/ssl-cert.sh /usr/local/bin/ssl-cert.sh;
mv files/ssl-cert.service /etc/systemd/system/ssl-cert.service;
mv files/ssl-cert.timer /etc/systemd/system/ssl-cert.timer;
systemctl daemon-reload;
systemctl start ssl-cert.timer;
systemctl enable ssl-cert.timer


# NGINX =================================================================


mv files/<DOMAIN>.conf /etc/nginx/conf.d/<DOMAIN>.conf;
chown nginx:nginx /etc/nginx/conf.d/<DOMAIN>.conf;
systemctl start nginx;
systemctl enable nginx


# ROBOTS =================================================================


mkdir -p /var/www/<DOMAIN>;
mv files/robots.txt /var/www/<DOMAIN>/robots.txt;
chown -R nginx:nginx /var/www/<DOMAIN>


# FAIL2BAN =================================================================


mv files/jail.local /etc/fail2ban/jail.local;
systemctl start fail2ban;
systemctl enable fail2ban


# LOGS =================================================================


mv files/logs-push.sh /usr/local/bin/logs-push.sh;
chmod +x /usr/local/bin/logs-push.sh;
mv files/logs-push.service /etc/systemd/system/logs-push.service;
mv files/logs-push.timer /etc/systemd/system/logs-push.timer;
systemctl daemon-reload;
systemctl enable logs-push.timer;
systemctl start logs-push.timer


# IPTABLES =================================================================


systemctl stop firewalld;
systemctl disable firewalld;

iptables -A INPUT -p tcp --dport 80 -j ACCEPT;
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT;
iptables -A INPUT -p tcp --dport 443 -j ACCEPT;
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT;
iptables -A INPUT -p tcp --dport 8501 -j ACCEPT;
iptables -A OUTPUT -p tcp --dport 8501 -j ACCEPT;

ipset create banned_ips hash:ip;
while read -r ip; do ipset add banned_ips "$ip"; done < files/banned_ips.txt;
ipset save | tee /etc/sysconfig/ipset;
iptables -A INPUT -m set --match-set banned_ips src -j DROP;

mv files/iptables-restore.service /etc/systemd/system/iptables-restore.service;
systemctl enable iptables-restore.service;

service iptables save;
systemctl start iptables.service;
systemctl enable iptables.service


# DOCKER =================================================================


systemctl enable --now docker;
usermod -aG docker ec2-user;
newgrp docker;

mv files/chatbot-docker.service /etc/systemd/system/chatbot-docker.service;
systemctl daemon-reload;
systemctl enable chatbot-docker.service


# AMI =================================================================


rm -rf files;
rm -f files.zip;
rm -rf /tmp/*;
rm -rf /var/cache/*;
journalctl --vacuum-time=1w;
history -c


#aws ec2 create-image --instance-id i-xxxxxxxxxxxxxxxxx --name "ami-chatbot-docker-v1"

































