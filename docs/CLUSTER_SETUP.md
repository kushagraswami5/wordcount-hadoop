# Setting up the 3-laptop Hadoop cluster

The project rules ask for **1 master + at least 2 workers on separate PCs**.

| Role    | Hostname  | Runs                                      |
|---------|-----------|-------------------------------------------|
| Master  | `master`  | NameNode, ResourceManager, the dashboard |
| Worker  | `worker1` | DataNode, NodeManager                     |
| Worker  | `worker2` | DataNode, NodeManager                     |

You do **steps 1–6 on all three laptops** and steps 7–9 on the master only.

Tested layout: Ubuntu 22.04/24.04 (a native install or WSL2 on Windows), Java 11, Hadoop 3.3.6.

> **Windows laptops:** install Ubuntu through WSL2 and turn on *mirrored networking* so the
> other laptops can reach it. Create `C:\Users\<you>\.wslconfig` containing
> `[wsl2]` and `networkingMode=mirrored` on separate lines, then run `wsl --shutdown`.
> Also allow ports 9000, 9864, 9866, 9870, 8088, 8030–8033, 8040, 8042 and 5000 through
> Windows Firewall.

---

## 1. Put all laptops on the same network
Use the same WiFi or a phone hotspot. College WiFi often blocks laptop-to-laptop
traffic, so **a phone hotspot is the safest option for the demo.**

Find each laptop's IP address:
```bash
hostname -I
```

## 2. Create the same user on every laptop
```bash
sudo adduser hadoop
sudo usermod -aG sudo hadoop
su - hadoop
```

## 3. Install Java, SSH and Python
```bash
sudo apt update
sudo apt install -y openjdk-11-jdk openssh-server python3 python3-pip git
```

## 4. Map hostnames to IPs
Edit `/etc/hosts` (`sudo nano /etc/hosts`) on **every** laptop and add the lines from
`configs/hosts.example`, using your real IPs.
Remove or comment out any line like `127.0.1.1 master`, because it makes Hadoop listen only on localhost.

Check that every laptop can reach the others: `ping worker1`, `ping master` and so on.

## 5. Install Hadoop
```bash
cd ~
wget https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzf hadoop-3.3.6.tar.gz
mv hadoop-3.3.6 hadoop
```
Add these lines to `~/.bashrc`, then run `source ~/.bashrc`:
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=$HOME/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```
Also set `JAVA_HOME` in `$HADOOP_HOME/etc/hadoop/hadoop-env.sh`:
```bash
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh
```

## 6. Copy the config files
From this repo:
```bash
cp configs/*.xml configs/workers $HADOOP_HOME/etc/hadoop/
mkdir -p ~/hadoopdata/namenode ~/hadoopdata/datanode
```

---

## 7. Passwordless SSH from master to the workers (master only)
```bash
ssh-keygen -t rsa -P "" -f ~/.ssh/id_rsa
ssh-copy-id hadoop@master
ssh-copy-id hadoop@worker1
ssh-copy-id hadoop@worker2
ssh worker1 exit    # should log in without asking for a password
```

## 8. Format HDFS (master only, FIRST TIME ONLY)
```bash
hdfs namenode -format
```
Never run this again once you have data. Formatting a second time breaks the DataNodes,
with a "clusterID mismatch" error. If that happens, delete `~/hadoopdata/datanode/*` on
the workers and start the cluster again.

## 9. Start the cluster (master only)
```bash
start-dfs.sh
start-yarn.sh
```

### Check it's working
```bash
jps                       # master: NameNode, SecondaryNameNode, ResourceManager
ssh worker1 jps           # workers: DataNode, NodeManager
hdfs dfsadmin -report     # should say "Live datanodes (2)"
yarn node -list           # should list 2 nodes
```
Web UIs, which are good to show the examiner:
- HDFS: http://master:9870, under *Datanodes*, should list both workers
- YARN: http://master:8088, where your job appears while it runs

### Stop the cluster
```bash
stop-yarn.sh
stop-dfs.sh
```

---

## Common problems

| Symptom | Fix |
|---|---|
| `Live datanodes (0)` | Check `/etc/hosts` on every laptop, check the firewall (`sudo ufw disable` during the demo), and look in `$HADOOP_HOME/logs/*datanode*.log` on the worker |
| `Connection refused master:9000` | Remove the `127.0.1.1 master` line from `/etc/hosts`, then run stop-dfs and start-dfs again |
| Job stuck at `ACCEPTED` | YARN has too little memory. Lower the memory values in `yarn-site.xml` and `mapred-site.xml` |
| `python3: command not found` in a job | Install python3 on **both workers** |
| IPs changed (new WiFi) | Update `/etc/hosts` on all 3 laptops |
