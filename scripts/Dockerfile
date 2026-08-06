FROM amazonlinux:2023

RUN dnf install -y openssh-server sudo passwd && \
    ssh-keygen -A

RUN useradd -m ec2-user && \
    echo "ec2-user:password123" | chpasswd

# Add ec2-user to the wheel group
RUN usermod -aG wheel ec2-user

# Allow wheel members to use sudo
RUN sed -i 's/^# %wheel/%wheel/' /etc/sudoers

# Allow password authentication
RUN sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd","-D","-e"]