# Topology

```
                                      My PC
                                  ┌──────────┐
                                  │          │
         ┌───────────────────────►│          │◄─────────────────────┐
         │                        └──────────┘                      │
         │                              ▲                           │
         │                              │                           │
         │                              │                           │
         │                              │                           │
         │                              │                           │
         │                              │                           │
         │                              │                           │
         │                              │                           │
         │                              │                           │
 ┌───────┴───────┐             ┌────────┴────────┐          ┌───────┴────────┐
 │     Node 1    │             │      Node 2     │          │     Node 3     │
 │ ┌───┐   ┌───┐ │             │ ┌───┐    ┌───┐  │          │ ┌───┐    ┌───┐ │
 │ │OSD│   │OSD│ │             │ │OSD│    │OSD│  │          │ │OSD│    │OSD│ │
 │ └───┘   └───┘ │             │ └───┘    └───┘  │          │ └───┘    └───┘ │
 │               │             │                 │          │                │
 └───────┬───────┘             └────────┬────────┘          └───────┬────────┘
         │                              │                           │
         │                              │                           │
         │                              │                           │
         │                              │                           │
         └──────────────────────────────┴───────────────────────────┘
                            Cluster Network (MTU 9000)
```

## Desc
in this scenario here was the topology.

Node 1 will be act for Ceph Mon+Mgr and another is Ceph OSDS, Every osds only have 10 GB of size so the will make my ceph cluster have 60GB.


## Setup
|Node|IP Public|IP Cluster|OS|Ceph Ver|
|----|--|--|--|--------|
|Node 1| 192.168.122.173 |200.0.0.10 | Ubuntu 18.04 | octopus |
|Node 2| 192.168.122.91  |200.0.0.20 | Ubuntu 18.04 | octopus |
|Node 3| 192.168.122.181 |200.0.0.30 |Ubuntu 18.04 | octopus |


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
for i in {1..3}
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
All nodes have same block disks name (vdb,vdc)

- `ceph-volume lvm create --data /dev/vdb`
- `ceph-volume lvm create --data /dev/vdc`

