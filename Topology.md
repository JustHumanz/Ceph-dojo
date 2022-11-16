# Topology

```
                                                        +-----------------------------------------+
                                                        |                                         |
                                                        |                                         |
                                                        |                  My PC                  |
                                                        |                                         |
                                                        |                                         |
                                                        |                                         |
                                                        +---------------------+-------------------+
                                                                              ^
                                                                              |
                                                                              |
                                                                              |
                                                                              |
                                                                              |
                                                                              |
                                                                              |
                                                              Public Network  |
             +------------------------------------------------------------------------------------------------------------------------+
             |                                                                |                                                       |
             |                                                                |                                                       |
             |                                                                |                                                       |
             |                                                                |                                                       |
             |                                                                |                                                       |
             |   Rack-01                                              Rack-02 |                                           Rack-03     |
+------------+--------------------------------+      +------------------------+--------------------+     +----------------------------+----------------+
|                                             |      |                                             |     |                                             |
|  +---------------+      +---------------+   |      |  +---------------+      +---------------+   |     |  +---------------+      +---------------+   |
|  |     Host 1    |      |     Host 2    |   |      |  |     Host 4    |      |     Host 5    |   |     |  |     Host 7    |      |     Host 8    |   |
|  |  +---+ +---+  |      |  +---+ +---+  |   |      |  |  +---+ +---+  |      |  +---+ +---+  |   |     |  |  +---+ +---+  |      |  +---+ +---+  |   |
|  |  |osd| |osd|  |      |  |osd| |osd|  |   |      |  |  |osd| |osd|  |      |  |osd| |osd|  |   |     |  |  |osd| |osd|  |      |  |osd| |osd|  |   |
|  |  +---+ +---+  |      |  +---+ +---+  |   |      |  |  +---+ +---+  |      |  +---+ +---+  |   |     |  |  +---+ +---+  |      |  +---+ +---+  |   |
|  |     +---+     |      |     +---+     |   |      |  |     +---+     |      |     +---+     |   |     |  |     +---+     |      |     +---+     |   |
|  |     |osd|     |      |     |osd|     |   |      |  |     |osd|     |      |     |osd|     |   |     |  |     |osd|     |      |     |osd|     |   |
|  |     +---+     |      |     +---+     |   |      |  |     +---+     |      |     +---+     |   |     |  |     +---+     |      |     +---+     |   |
|  +---------------+      +---------------+   |      |  +---------------+      +---------------+   |     |  +---------------+      +---------------+   |
|                                             |      |                                             |     |                                             |
|              +---------------+              |      |              +---------------+              |     |              +---------------+              |
|              |     Host 3    |              |      |              |     Host 6    |              |     |              |     Host      |              |
|              |  +---+ +---+  |              |      |              |  +---+ +---+  |              |     |              |  +---+ +---+  |              |
|              |  |osd| |osd|  |              |      |              |  |osd| |osd|  |              |     |              |  |osd| |osd|  |              |
|              |  +---+ +---+  |              |      |              |  +---+ +---+  |              |     |              |  +---+ +---+  |              |
|              |     Fast      |              |      |              |     Fast      |              |     |              |     Fast      |              |
|              +---------------+              |      |              +---------------+              |     |              +---------------+              |
|                                             |      |                                             |     |                                             |
+---------------------+-----------------------+      +-----------------------+---------------------+     +----------------------+----------------------+
                      |                                                      |                                                  |
                      |                                                      |                                                  |
                      |                                                      |                                                  |
                      +------------------------------------------------------+--------------------------------------------------+
                                                                     Cluster Network (MTU 9000)

```

## Desc
in this scenario here was the topology.

Node 1 will be act for Ceph Mon+Mgr and another is Ceph OSDS, Every osds only have 10 GB of size so the will make my ceph cluster have 90GB.


## Setup
|Node|IP Public|IP Cluster|OS|Ceph Ver|
|----|--|--|--|--------|
|Node 1| 192.168.122.173 |200.0.0.10 | Ubuntu 18.04 | octopus |
|Node 2| 192.168.122.91  |200.0.0.20 | Ubuntu 18.04 | octopus |
|Node 3| 192.168.122.181 |200.0.0.30 |Ubuntu 18.04 | octopus |
|Node 4| 192.168.122.99 |200.0.0.40 |Ubuntu 18.04 | octopus |
|Node 5| 192.168.122.17 |200.0.0.50 |Ubuntu 18.04 | octopus |
|Node 6| 192.168.122.107 |200.0.0.60 |Ubuntu 18.04 | octopus |
|Node 7| 192.168.122.25  | 200.0.0.70| Ubuntu 18.04 | octopus |
|Node 8| 192.168.122.115 | 200.0.0.80| Ubuntu 18.04 | octopus |    
|Node 9| 192.168.122.33  | 200.0.0.90| Ubuntu 18.04 | octopus | 

##### All nodes
- `wget -q -O- 'https://download.ceph.com/keys/release.asc' | sudo apt-key add -`
- `sudo apt-add-repository 'deb https://download.ceph.com/debian-octopus/ bionic main'`
- `apt update; apt -y install ceph`

##### node 1 set ceph mon&mgr
- `nano /etc/ceph/ceph.conf`
```
[global]
cluster network = 200.0.0.0/24
public network = 100.0.0.0/24
fsid = 63679f4b-22cf-4180-9094-99a63d465ded
mon host = 100.0.0.10
mon initial members = humanz-ceph-dojo1
osd pool default crush rule = -1
[mon.humanz-ceph-dojo1]
host = humanz-ceph-dojo1
mon addr = 100.0.0.10
mon allow pool delete = true
```

- `ceph-authtool --create-keyring /etc/ceph/ceph.mon.keyring --gen-key -n mon. --cap mon 'allow *' `
- `ceph-authtool --create-keyring /etc/ceph/ceph.client.admin.keyring --gen-key -n client.admin --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow *' --cap mgr 'allow *' `
- `ceph-authtool --create-keyring /var/lib/ceph/bootstrap-osd/ceph.keyring --gen-key -n client.bootstrap-osd --cap mon 'profile bootstrap-osd' --cap mgr 'allow r' `
- `ceph-authtool /etc/ceph/ceph.mon.keyring --import-keyring /etc/ceph/ceph.client.admin.keyring `
- `ceph-authtool /etc/ceph/ceph.mon.keyring --import-keyring /var/lib/ceph/bootstrap-osd/ceph.keyring `

- `FSID=$(grep "^fsid" /etc/ceph/ceph.conf | awk {'print $NF'}) `
- `NODENAME=$(grep "^mon initial" /etc/ceph/ceph.conf | awk {'print $NF'}) `
- `NODEIP=$(grep "^mon host" /etc/ceph/ceph.conf | awk {'print $NF'}) `

- `monmaptool --create --add $NODENAME $NODEIP --fsid $FSID /etc/ceph/monmap`

- `mkdir /var/lib/ceph/mon/ceph-$(hostname) `
- `ceph-mon --cluster ceph --mkfs -i $NODENAME --monmap /etc/ceph/monmap --keyring /etc/ceph/ceph.mon.keyring`
- `chown ceph. /etc/ceph/ceph.*`
- `chown -R ceph. /var/lib/ceph/mon/ceph-$(hostname) /var/lib/ceph/bootstrap-osd`
- `systemctl enable --now ceph-mon@$NODENAME`

- `ceph mon enable-msgr2`
- `ceph mgr module enable pg_autoscaler`
- `mkdir /var/lib/ceph/mgr/ceph-$(hostname)`
- `ceph auth get-or-create mgr.$NODENAME mon 'allow profile mgr' osd 'allow *' mds 'allow *'`
- `ceph auth get-or-create mgr.$(hostname) | tee /etc/ceph/ceph.mgr.admin.keyring`
- `cp /etc/ceph/ceph.mgr.admin.keyring /var/lib/ceph/mgr/ceph-$(hostname)/keyring`

- `chown ceph. /etc/ceph/ceph.mgr.admin.keyring`
- `chown -R ceph. /var/lib/ceph/mgr/ceph-$(hostname)`
- `systemctl enable --now ceph-mgr@$NODENAME `

##### distributed the ceph key&conf
```
for i in {1..9}
do
    NODE=node${i}
    if [ ! i = 1 ]
    then
        scp /etc/ceph/ceph.conf ${NODE}:/etc/ceph/ceph.conf
        scp /etc/ceph/ceph.client.admin.keyring ${NODE}:/etc/ceph
        scp /var/lib/ceph/bootstrap-osd/ceph.keyring ${NODE}:/var/lib/ceph/bootstrap-osd
    fi
    ssh $NODE \
    "chown ceph. /etc/ceph/ceph.* /var/lib/ceph/bootstrap-osd/*; "
done 
```
##### create osds on all nodes
All nodes have same block disks name (vdb,vdc,vdd)

- `ceph-volume lvm create --data /dev/vdb`
- `ceph-volume lvm create --data /dev/vdc`
- `ceph-volume lvm create --data /dev/vdd`


##### create osds on all fast nodes
All nodes have same block disks name (vdb,vdc)

- `ceph-volume lvm create --data /dev/vdb`
- `ceph-volume lvm create --data /dev/vdc`


##### osds tree
```
ID   CLASS   WEIGHT    TYPE NAME                     STATUS  REWEIGHT  PRI-AFF
 -1          16.15163  root default
 -9           4.06847      rack rack01
 -3           0.04887          host ubuntu-nested-1
  0  hdd_v2   0.00980              osd.0                 up   1.00000  1.00000
  1  hdd_v2   0.00980              osd.1                 up   1.00000  1.00000
  8  hdd_v2   0.00980              osd.8                 up   1.00000  1.00000
 20  hdd_v2   0.01949              osd.20                up   1.00000  1.00000
-17           4.00000          host ubuntu-nested-4
  6  hdd_v2   1.00000              osd.6                 up   1.00000  1.00000
  7  hdd_v2   1.00000              osd.7                 up   1.00000  1.00000
 10  hdd_v2   1.00000              osd.10                up   1.00000  1.00000
 18  hdd_v2   1.00000              osd.18                up   1.00000  1.00000
-27           0.01959          host ubuntu-nested-7
 24  ssd_v2   0.00980              osd.24                up   1.00000  1.00000
 27  ssd_v2   0.00980              osd.27                up   1.00000  1.00000
-10           4.06357      rack rack02
 -5           0.04398          host ubuntu-nested-2
  2  hdd_v2   0.00980              osd.2                 up   1.00000  1.00000
  3  hdd_v2   0.00980              osd.3                 up   1.00000  1.00000
  9  hdd_v2   0.00980              osd.9                 up   1.00000  1.00000
 22  hdd_v2   0.01459              osd.22                up   1.00000  1.00000
-28           4.00000          host ubuntu-nested-5
 12  hdd_v2   1.00000              osd.12                up   1.00000  1.00000
 13  hdd_v2   1.00000              osd.13                up   1.00000  1.00000
 14  hdd_v2   1.00000              osd.14                up   1.00000  1.00000
 21  hdd_v2   1.00000              osd.21                up   1.00000  1.00000
-34           0.01959          host ubuntu-nested-8
 25  ssd_v2   0.00980              osd.25                up   1.00000  1.00000
 29  ssd_v2   0.00980              osd.29                up   1.00000  1.00000
-11           8.01959      rack rack03
 -7           4.00000          host ubuntu-nested-3
  4  hdd_v2   1.00000              osd.4                 up   1.00000  1.00000
  5  hdd_v2   1.00000              osd.5                 up   1.00000  1.00000
 11  hdd_v2   1.00000              osd.11                up   1.00000  1.00000
 23  hdd_v2   1.00000              osd.23                up   1.00000  1.00000
-31           4.00000          host ubuntu-nested-6
 15  hdd_v2   1.00000              osd.15                up   1.00000  1.00000
 16  hdd_v2   1.00000              osd.16                up   1.00000  1.00000
 17  hdd_v2   1.00000              osd.17                up   1.00000  1.00000
 19  hdd_v2   1.00000              osd.19                up   1.00000  1.00000
-37           0.01959          host ubuntu-nested-9
 26  ssd_v2   0.00980              osd.26                up   1.00000  1.00000
 28  ssd_v2   0.00980              osd.28                up   1.00000  1.00000
```