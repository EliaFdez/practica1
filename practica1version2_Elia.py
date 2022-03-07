from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random, randint

NPROD = 3
N = 10
K = 4

def delay(factor = 3):
    sleep(random()/factor)

def add_data(storage, proc_id, valor, pos, mutex):
    mutex.acquire()
    try:
        valor = valor + randint(0,9)
        storage[proc_id * K + pos] = valor
        delay(6)
    finally:
        mutex.release()

    return valor

def producer(storage, empty, non_empty, mutex):
    valor = randint(0,9)
    prod_id = int(current_process().name.split('_')[1])
    cont = 1

    for v in range(N):
        print(f'producer {current_process().name} produciendo')
        delay(6)
        empty.acquire()
        valor = add_data(storage, prod_id, valor, v % K, mutex)
        print(f'producer {current_process().name} almacenado {valor}')  
        if cont < K:
            cont += 1
            empty.release()
        else:
            non_empty.release()

    empty.acquire()
    mutex.acquire()
    try:
        storage[(prod_id * K) + (N % K)] = -1
    finally:
        mutex.release()
    non_empty.release()
    
def get_data(storage, mutex, status):
    mutex.acquire()
    try:
        data = -1
        prod_id = -1
        pos = 0

        while pos < K*NPROD:
            #miramos si el productor a terminado de producir y si se han consumido ya todos sus elementos.
            if status[pos // K] == 0 and storage[pos] == -1:
                status[pos // K] = 1
            elif status[pos// K] == 1 and all(elem == -1 for elem in storage[(pos//K)*K : (pos//K)*K + K]):
                status[pos // K] = 2
            
            if status[pos // K] == 2:
                pos += K
            elif storage[pos] != -1:
                if data == -1 or storage[pos] < data:
                    data = storage[pos]
                    prod_id = pos
                pos += 1
            else:
                pos += 1
        if status[prod_id // K] == 1:
            storage[prod_id] = -1
        prod_id = prod_id // K
    finally:
        mutex.release()

    return (data, prod_id)

def consumer(storage, emptyList, non_emptyList, mutex, status):
    datos = []

    for i in range(NPROD):
        non_emptyList[i].acquire()

    while any(elem != 2 for elem in status):

        print('consumidor desalmacenando')
        (dato, prod_id) = get_data(storage, mutex, status)
        if dato != -1:
            datos.append(dato)

        if status[prod_id] == 0:
            emptyList[prod_id].release()
        else:
            non_emptyList[prod_id].release()

        print(f'consumidor ha consumido {dato} del productor {prod_id}')

        if status[prod_id] == 0:
            non_emptyList[prod_id].acquire()
    
    print('datos consumidos: ', datos)



def main():
    storage = Array('i', K*NPROD)
    status = Array('i', NPROD) # 0->puede producir, 1->termino de producir, 2->termino de consumir

    for i in range(K*NPROD):
        storage[i] = -1
    for i in range(NPROD):
        status[i] = 0
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
                     args=(storage, empty, non_empty, mutex, status))

    for p in prodList + [consum]:
        p.start()

    for p in prodList + [consum]:
        p.join()

if __name__ == '__main__':
    main()