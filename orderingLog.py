## for logging ## 

import os, requests, sys, io, logging, time

log = logging.getLogger()

def SET_LOG() :
    if not os.path.exists('./log') : 
        os.mkdir('./log')
        
    logging.basicConfig(
        filename = f'./log/message_{time.time()}.txt',
        level = logging.INFO,
        format = '%(asctime)s %(module)s %(funcName)s[%(lineno)d] %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    