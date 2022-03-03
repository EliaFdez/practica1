from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random

NPROD = 5
N = 10

def delay(factor = 3):
    sleep(random()/factor)

def add_data(storage, proc_id, data, mutex):
    mutex.acquire()
    try:
        storage[proc_id] = proc_id*100 + data
        delay(6)
        print('Storage: ', storage[proc_id])
    finally:
        mutex.release()

def producer(storage, empty, non_empty, mutex):
    for v in range(N):
        print(f'producer {current_process().name} produciendo')
        delay(6)
        empty.acquire()
        add_data(storage, int(current_process().name.split('_')[1]), v, mutex)
        non_empty.release()
        print(f'producer {current_process().name} almacenado {v}')

def get_data(storage, mutex):
    mutex.acquire()
    try:
        for i in range(NPROD):
            print('Storage: ', storage[i])

        data = 5000000
        prod_id = -1
        for i in range(NPROD):
            if storage[i] < data:
                data = storage[i]
                prod_id = i
        storage[prod_id] = -1

    finally:
        mutex.release

    return (data, prod_id)

def consumer(storage, emptyList, non_emptyList, mutex):
    for i in range(NPROD):
        non_emptyList[i].acquire()

    print('consumidor desalmacenando')
    (dato, prod_id) = get_data(storage, mutex)

    print('PATATA ', prod_id)
    emptyList[prod_id].release()

    print(f'consumidor ha consumido {dato} del productor {prod_id}')



def main():
    storage = Array('i', NPROD)

    for i in range(NPROD):
        storage[i] = -1
    print('almacen inicial: ', storage[:])

    non_empty = [Semaphore(0) for i in range(NPROD)]
    empty = [BoundedSemaphore(1) for i in range(NPROD)]
    mutex = Lock()

    prodList = [Process(target=producer,
                        name=f'prod_{i}',
                        args=(storage, empty[i], non_empty[i], mutex))
                for i in range(NPROD)]

    consum = Process(target=consumer,
                     name='consumidor',
                     args=(storage, empty, non_empty, mutex))

    for p in prodList + [consum]:
        p.start()

    for p in prodList + [consum]:
        p.join()

if __name__ == '__main__':
    main()