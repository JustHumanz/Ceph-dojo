# Crush Rule

## Desc
Before we can use ceph or creating image we need to define the [crush rule](https://docs.ceph.com/en/quincy/rados/operations/crush-map/), in this scenario i will have 2 device class hdd_v2 and ssd_v2, and each device class will be assigned to different pool also for the replication i will choics rack domain.

#### Creating&Set device class
- `ceph osd crush class create hdd_v2`
- `ceph osd crush class create ssd_v2`
- `ceph osd crush rm-device-class osd.1 osd.2 ...`
- `ceph osd crush set-device-class hdd_v2 osd.1 osd.2 ...`
- `ceph osd crush set-device-class ssd_v2 osd.3 osd.4 ...`

#### Create crush rule
- `ceph osd crush rule create-replicated kano-crush default rack hdd_v2`
- `ceph osd crush rule create-replicated lon-crush default rack ssd_v2`
--------------------------------------------------------------------------------------------------------------------------------------------

# Pool
## Desc
After we creating crush rule now we can creating ceph volume.

##### Create ceph pool
- `ceph osd pool create mklntic 32 32 replicated kano-crush`
- `ceph osd pool create mklntic-fast 32 32 replicated lon-crush`

##### Set replication size in ceph pool
- `ceph osd pool set mklntic size 3`
- `ceph osd pool set mklntic-fast size 3`

##### Init pool
- `rbd pool init mklntic`
- `rbd pool init mklntic-fast`

##### Create ceph image
- `rbd create --size 3G --pool mklntic kano-vol`
- `rbd create --size 2G --pool mklntic-fast lon-vol`

##### Format && Mount the image
- `rbd map -p mklntic kano-vol` # /dev/rbd0
- `rbd map -p mklntic-fast lon-vol` # /dev/rbd1

- `mkfs.ext4 /dev/rbd0`
- `mkfs.ext4 /dev/rbd1`

Ceph image already created,now we can do the experiment. 