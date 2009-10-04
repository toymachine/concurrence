
import logging
import time
import sys

from concurrence import unittest, Tasklet, Channel, Lock, Semaphore, TaskletPool, Deque, TimeoutError, TaskletError, JoinError, Message

class TestTaskletPool(unittest.TestCase):
    def testBasic(self):

        d = Deque()

        def handler(i):
            Tasklet.sleep(1.0)
            d.append(i)

        tp = TaskletPool()

        for i in range(20):
            tp.defer(handler, i)
 
        start = time.time()

        xs = []
        while True:
            xs.append(d.popleft(True, 30))
            if len(xs) == 20:
                break
        
        end = time.time()
        
        #5 workers taking 1 second to process 20 items = 4.0 total proc time
        self.assertAlmostEqual(4.0, end - start, places = 1)
        self.assertEquals(190, sum(xs))

class TestPrimitives(unittest.TestCase):        
    def testSemaphore(self):
        sema = Semaphore(4)
        self.assertEquals(True, sema.acquire())
        self.assertEquals(3, sema.count)        
        self.assertEquals(True, sema.acquire())
        self.assertEquals(2, sema.count)        
        self.assertEquals(True, sema.acquire())
        self.assertEquals(1, sema.count)        
        self.assertEquals(True, sema.acquire())
        self.assertEquals(0, sema.count)        
        self.assertEquals(False, sema.acquire(False))
        self.assertEquals(0, sema.count)        

        self.assertEquals(None, sema.release())
        self.assertEquals(1, sema.count)        
        self.assertEquals(None, sema.release())
        self.assertEquals(2, sema.count)        
        self.assertEquals(None, sema.release())
        self.assertEquals(3, sema.count)        
        self.assertEquals(None, sema.release())
        self.assertEquals(4, sema.count)        
        self.assertEquals(None, sema.release())
        self.assertEquals(5, sema.count) #possible to go beyond initial count... is this ok?        

        sema = Semaphore(4)
        xs = []

        def t(x):
            try:
                with sema:
                    Tasklet.sleep(1.0)
                    xs.append(x)
                return x
            except TimeoutError:
                pass

        start = time.time()
        for i in range(8):
            Tasklet.new(t)(i)

        join_result = Tasklet.join_children() 
        self.assertEquals(8, len(join_result))
        self.assertEquals(28, sum(xs))

        end = time.time()
        self.assertAlmostEqual(2.0, end - start, places = 1)
    
    def testLock(self):
        lock = Lock()
        self.assertEquals(True, lock.acquire())   
        self.assertEquals(True, lock.is_locked())    
        self.assertEquals(None, lock.release())

        xs = []

        def t(x):
            try:
                with lock:
                    Tasklet.sleep(1.0)
                    xs.append(x)
                return x
            except TimeoutError:
                pass

        start = time.time()
        for i in range(5):
            Tasklet.new(t)(i)

        join_result = Tasklet.join_children()
        self.assertEquals(5, len(join_result))
        self.assertEquals(10, sum(xs))

        end = time.time()
        self.assertAlmostEqual(5.0, end - start, places = 1)

if __name__ == '__main__':
    unittest.main(timeout = 100.0)
