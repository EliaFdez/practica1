from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random, randint

NPROD = 3
N = 5

def delay(factor = 3):
    sleep(random()/factor)

def add_data(storage, proc_id, valor, mutex):
    mutex.acquire()
    try:
        valor = valor + randint(0,9)
        storage[proc_id] = valor
        delay(6)
    finally:
        mutex.release()

    return valor

def producer(storage, empty, non_empty, mutex):
    valor = randint(0,9)

    for v in range(N):
        print(f'producer {current_process().name} produciendo')
        delay(6)
        empty.acquire()
        valor = add_data(storage, int(current_process().name.split('_')[1]), valor, mutex)
        non_empty.release()
        print(f'producer {current_process().name} almacenado {valor}')

    empty.acquire()
    storage[int(current_process().name.split('_')[1])] = -1
    non_empty.release()
    
def get_data(storage, mutex, status):
    mutex.acquire()
    try:
        data = -1
        prod_id = -1
        for i in range(NPROD):
            if status[i]:
                if storage[i] == -1:
                    status[i] = False
                elif storage[i] < data or data == -1:
                    data = storage[i]
                    prod_id = i

    finally:
        mutex.release()

    return (data, prod_id)

def consumer(storage, emptyList, non_emptyList, mutex, status):
    datos = []

    for i in range(NPROD):
        non_emptyList[i].acquire()

    while any(elem for elem in status):

        print('consumidor desalmacenando')
        (dato, prod_id) = get_data(storage, mutex, status)
        if dato != -1:
            datos.append(dato)

        emptyList[prod_id].release()

        print(f'consumidor ha consumido {dato} del productor {prod_id}')

        if status[prod_id]:
            non_emptyList[prod_id].acquire()
    
    print('datos consumidos: ', datos)



def main():
    storage = Array('i', NPROD)
    status = Array('i', NPROD)

    for i in range(NPROD):
        storage[i] = -1
        status[i] = True
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