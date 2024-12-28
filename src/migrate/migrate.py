import argparse,rados,os,subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class rados_migrate:
    # Init rados 
    def __init__(self,worker:int,sync:bool):
        self.cluster = rados.Rados(conffile = '/etc/ceph/ceph.conf', conf = dict (keyring = '/etc/ceph/ceph.client.admin.keyring'))
        self.cluster.connect()
        self.worker = worker
        self.sync = sync
        self.dst_pool_obj_list = []

    # Setup src and dst pools session and check if ceph space avalable
    def setup_pools(self,src_pool:str,dst_pool:str):
        if self.cluster.pool_exists(dst_pool)!=True:
            print("Target pool not found")
            os._exit(1)

        self.cluster_avail = self.cluster.get_cluster_stats()['kb_avail']
        self.src_pool = self.cluster.open_ioctx(src_pool)
        self.dst_pool = self.cluster.open_ioctx(dst_pool)

        src_pool_size = self.src_pool.get_stats().get('num_kb')

        if round((src_pool_size*2) / self.cluster_avail * 100) >= 85:
            print("Error,Copying the obj into new pool will ate more than 85% space avalable")
            os._exit(1)

    # Split list of pool obj
    def split_obj_into_chunks(self):
        pbar = tqdm(total=len(list(self.dst_pool.list_objects())))
        pbar.set_description(f"[INFO] List&Filter {self.dst_pool.name} obj")
        for i in self.dst_pool.list_objects():
            pbar.update(1)
            self.dst_pool_obj_list.append(i.key)
        self.dst_pool_obj_list.sort()
        pbar.close()

        src_pool_obj_list = []
        pbar = tqdm(total=len(list(self.src_pool.list_objects())))
        pbar.set_description(f"[INFO] List&Filter {self.src_pool.name} obj")
        for i in self.src_pool.list_objects():
            pbar.update(1)
            if i.key in self.dst_pool_obj_list and self.sync == False:
                continue
            src_pool_obj_list.append(i.key)

        pbar.close()
        src_pool_obj_list.sort()
        if len(src_pool_obj_list) == 0:
            print("[ERR] Pool doesn't have any object, either you already run the migrate or pool was empty try use -s to sync between two pool")
            os._exit(1)

        chunks_size = round(len(src_pool_obj_list)/self.worker)
        return [src_pool_obj_list[i:i + chunks_size] for i in range(0, len(src_pool_obj_list), chunks_size)]
        
    def copy_pool_obj(self,src_obj_list):
        for src_obj_name in src_obj_list:
            if self.sync and src_obj_name in self.dst_pool_obj_list:
                src_obj_buff = self.src_pool.read(src_obj_name)
                try:
                    res = self.dst_pool.cmpext(src_obj_name,src_obj_buff)
                    print(f"[INFO] sync {self.src_pool.name}/{src_obj_name} == {self.dst_pool.name}/{src_obj_name}")
                    if res == 0:
                        continue
                    else:
                        print(f"[WARN] obj {self.dst_pool.name}/{src_obj_name} size not match with original obj,try to sync obj")
                except AssertionError:
                    print(f"[WARN] obj {self.dst_pool.name}/{src_obj_name} not sync with new pool,try to sync obj")

            ## this is was dirty but work, the proper way to do this is using ioctx.read on src pool then ioctx.write on dst pool 
            ## and i need to set the xattr 
            cmd = [f'rados', 'cp', f'--pool={self.src_pool.name}', f'{src_obj_name}', f'--target-pool={self.dst_pool.name}', f'{src_obj_name}']
            subprocess.run(cmd, text=True, capture_output=True)
            print(f"[INFO] {self.src_pool.name}/{src_obj_name} => {self.dst_pool.name}/{src_obj_name}")
            
    def shutoff(self):
        self.src_pool.close()
        self.dst_pool.close()
        self.cluster.shutdown()

def main():
    parser = argparse.ArgumentParser(description='Ceph pool migrate')
    parser.add_argument('-p','--pool', required=True,help="Source pool")
    parser.add_argument('-t','--target',required=True,help="Target pool")
    parser.add_argument('-w','--worker',required=False,default=1, type=int,help="Worker to copy obj")
    parser.add_argument('-s','--sync',default=False,action='store_true',help="comparing&sync obj in target pool by obj content")
    args = parser.parse_args()
    worker = args.worker
    migrate = rados_migrate(worker,args.sync)
    migrate.setup_pools(args.pool,args.target)
    src_pool_obj_list_chunks = migrate.split_obj_into_chunks()

    with ThreadPoolExecutor(max_workers=worker) as executor:
        futures = []
        for task in src_pool_obj_list_chunks:
            futures.append(executor.submit(migrate.copy_pool_obj, task))

        for future in as_completed(futures):
            future.result()

    migrate.shutoff()

main()