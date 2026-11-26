""" 
Attack 3: hellman attack.


"""

#from __future__ import annotations
import math
import time
from typing import Optional

from pos.plot import Plot
from pos.provers.base import Prover
from pos.schemes.base import Scheme

class HellmanProver(Prover):
"""Sthe cheater stores every t-th value on each cycle of f and walks through it to answer """
    def __init__(self, scheme, step=None):
        super().__init__(scheme)
        if not getattr(self.f, "is_permutation", False): #we need a permutation to have the cycles
            raise ValueError("Hellman's cycle attack needs a permutation (use the Feistel function)")
        N = scheme.params.N
        """ - step is the spacing between checkpoints, the t-th value
            - we have 3 cases;
                    . "step" is given
                    . "step" is not given but we have the verifier's time limit (time_limit_ms)
                    . "step" is not given and we dont have the verifier's time limit
        """
        if step is None and time_limit_ms is not None:
            step = self.step_from_time_limit(time_limit_ms)
        if step is None:
            step = max(1, math.isqrt(N))
        if type(step) is not int or not 1 <= step <= N:
            raise V alueError(f"step must be an integer between 1 and N = {N}, got {step!r}")
        self.step = step
        self.name = f"hellman(t={step})"


    def step_from_time_limit(self, time_limit_ms: float) -> int:
    """ - pick t so that t hash calls fit within the time limit.
        - find the largest t whose t hash calls still finish before the deadline
    """
        N = self.scheme.params.N #t should be never larger than N
        f = self.scheme.new_function() 
        """ - separate copy f, not counted as prover work
            - compute f 1000 times just to measure its speed
        """
        start = time.perf_counter()
        for x in range(1000):
            f(x % N) #keeps x inside 0 to N−1 (our domain)
        ms_per_call = (time.perf_counter() - start) * 1000 / 1000 #(ms/call)
        t = int(time_limit_ms / ms_per_call / 2)  # divide by 2 as a safety margin
        return max(1, min(t, N)) # never larger than N and smaller than 1 (no checkpoints)
    

    def setup(self) -> None:
    """ - runs once before the challenge 
        - build cheater small table (storing the checkpoints)
    """    
        N = self.scheme.params.N
        t = self.step
        visited = bytearray(N)
        previous = {} #table to fill (checkpoint -> the checkpoint before it)

        for start in range(N): #find each cycle and one walk through each cycle
            if visited[start]:
                continue
            last_checkpoint = None
            x, i = start, 0
            while True:
                visited[x] = 1 #mark as visited
                if i % t == 0: #check if it is a check point
                    if last_checkpoint is not None:
                        previous[x] = last_checkpoint
                    last_checkpoint = x
                x = self.f(x)
                i += 1
                if x == start: #back at the start: cycle done
                    break
            previous[start] = last_checkpoint #close circle
    
    self.plot = Plot(previous, entry_bits=2 * self.scheme.params.n_bits) #save table


    def answer(self, y: int) -> Optional[int]: 
    """answer a challenge based on table we saved: we receive y and we look for x (f(x)=y)"""
        t = self.step

        z, steps = y, 0 # we start at z
        while self.plot.lookup(z) is None: #walk forward until reaching a checkpoint
            z = self.f(z)
            steps += 1
            if steps > t:
                return None

        x = self.plot.lookup(z) #when we reach a checkpoint we go to the one before it
        for _ in range(t): #walk forward until the next value is y
            next_x = self.f(x)
            if next_x == y:
                return x
            x = next_x
        return None #in case we finish without finding y

