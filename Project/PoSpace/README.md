# Proof of Space: implementation and attacks

A step-by-step implementation of proofs of space. We start with the simplest scheme (no security measures), attack it, add defences, and attack again.

| Step | Type | Status |
|---|---|---|
| 1. Basic scheme: prover stores a table, verifier sends challenges | Construction | ✅ Done |
| 2. Partial storage attack (keep only part of the table) and time-storage attack (brute-force the rest) | Attack | ✅ Done |
| 3. Repeated challenges (time limit still to do) | Defence | Repeated challenges supported |
| 4. Hellman's time-memory trade-off | Attack | To do |
| 5. Collision-based construction (g_f) | Construction | To do |
| 6. Nested Hellman attack | Attack | To do |

**Contents**
1. [Setup](#1-setup)
2. [Quick start](#2-quick-start)
3. [The basic scheme](#3-the-basic-scheme)
4. [Attacks](#4-attacks)
   - [4.1 Partial storage](#41-partial-storage)
   - [4.2 Time/storage](#42-timestorage)
5. [Input validation](#5-input-validation)
6. [Tests](#6-tests)
7. [Files](#7-files)
8. [Group workflow (mandatory)](#8-group-workflow-mandatory-so-we-dont-mess-up-anything-)
9. [Extending the code](#9-extending-the-code)

---

## 1. Setup

You need:
- **Python 3.9 or newer**: [python.org](https://www.python.org). On Windows, tick **"Add Python to PATH"** during install.
- **Git**: [git-scm.com](https://git-scm.com).
- **VS Code** (recommended) with the **Python** extension by Microsoft.

No packages to install. The code only uses Python's standard library.

**Get the repo (first time only):**
```bash
git clone https://github.com/AngelosKamaris/AAU-1st-Semester-Repo-Group-8
```
If the download keeps failing on a slow connection, use
`git clone --depth 1 <url>` to download only the latest version.

---

## 2. Quick start

All commands in this README are run from **this folder** (`Project/PoSpace`). In VS Code, open a terminal with **Terminal → New Terminal**, then:

```bash
cd Project/PoSpace
python main.py
```
If `python` isn't recognised, use `py` (Windows) or `python3` (Mac/Linux).

**What a successful run looks like:**
```
Prover: honest
Initialization (N = 2^16 = 65536, function = feistel)
  table entries:     65,536
  storage:           2,097,152 bits
  setup evaluations: 65,536
  setup time:        <elapsed> s

Challenges
  #1   y = <challenge>  answer x = <preimage>  accepted  (0 function calls, <time> ms)

Valid answers: 1/1
Proof accepted
Average function calls per challenge: 0.0
Average time per challenge:       0.00 ms
```
- **Initialization** is done once: the prover builds its table, and we print how big it is.
- **Each challenge line** shows the challenge `y` (shortened), the prover's answer, whether the verifier accepted it, and the prover's work for that challenge.
- Work is reported two ways: **function calls** (the same on every machine, our main measure) and **wall-clock time** (depends on your computer). The time covers only the prover answering, not the verifier checking.
- `--challenges` is the number of independent challenges required in one proof; all answers must be valid.

**Options** (combine them freely; `python main.py --help` lists them):
```bash
python main.py --n-bits 12 --challenges 20 --seed 42
python main.py --prover timestorage --fraction 0.5
python main.py --function blake2b --n-bits 16
python main.py --function feistel --n-bits 16 --rounds 8 --master-key 00112233445566778899aabbccddeeff
```

| Option | Meaning | Allowed | Default |
|---|---|---|---|
| `--n-bits` | Table size, N = 2^n_bits | 1 to 24; even and at least 2 for Feistel | 16 (N = 65,536) |
| `--function` | Function used for the plot | `feistel`, `blake2b` | `feistel` |
| `--rounds` | Number of Feistel rounds | positive integer | 8 |
| `--master-key` | Feistel key for repeatable plots | 32 hex characters | random key |
| `--challenges` | Independent challenges required in one proof; all must pass | integer, at least 1 | 1 |
| `--seed` | The plot's seed (its identity): a different seed gives a completely different table | integer, 0 to 2^128 - 1 | 1 |
| `--prover` | Who answers: `honest`, or one of the attacks `partial`, `timestorage` (see [section 4](#4-attacks)) | one of the three | honest |
| `--fraction` | For the attacks: share of the table the cheater keeps | number, 0 to 1 | 0.5 |

A value outside the allowed range gives a short usage error, for example `main.py: error: argument --challenges: must be at least 1, got 0` (see [section 5](#5-input-validation)).

---

## 3. The basic scheme

**Initialization (done once by the prover)**
- By default, `f` is an 8-round balanced Feistel permutation over `[0, N)`, with `N = 2^n_bits`.
- The input is split into equal halves; keyed BLAKE2b rounds transform them and preserve a permutation.
- A random 128-bit master key is generated for each plot. Pass `--master-key` to repeat a plot.
- The original BLAKE2b function remains available with `--function blake2b`.
- The prover computes `f(x)` for every input and stores a table `f(x) -> x`.

**Proof of execution (repeated every round)**
1. The verifier picks a random x and sends the challenge y = f(x).
2. The prover looks up y in its table and sends back an x with f(x) = y.
3. The verifier checks: the answer is a genuine integer (not a float, string, `None`, ...), x is in range, and f(x) equals y.

**Notes**
- **Every Feistel output appears exactly once**, so the plot has exactly N entries.
- **Each Feistel entry stores y and x** (2 · n_bits bits).
- **The inverse helper is kept separate from the forward function** and is used only for trusted tests; this models restricted oracle access, not a public one-way permutation.
- **Every function object counts its evaluations** (`calls`), so we can measure how much work each prover does.

**Look at the prover's table** (the first 20 rows):
```bash
python -c "from pos import PoSParams; from pos.schemes import SimpleScheme; from pos.provers import HonestProver; p = HonestProver(SimpleScheme(PoSParams(n_bits=8, seed=1))); p.setup(); [print(f'{y:x}', '->', x) for y, x in sorted(p.plot._entries.items())[:20]]"
```
Change `seed=1` or `n_bits=8` to look at other plots, remove `[:20]` to print everything, or swap `HonestProver(...)` for `PartialStorageProver(..., fraction=0.5, rng_seed=1)` to see a cheater's table.

**What to point out:** the prover builds the table once and then answers every challenge with a lookup (0 function calls). Storage grows with N.

---

## 4. Attacks

An attack is a different **prover** facing the same verifier. The attacks below keep only a share p of the table, so they use less space than the honest prover. They differ in what happens when the answer is not in the part they kept:

| Attack | `--prover` | On a miss | Challenges passed | Extra cost |
|---|---|---|---|---|
| [4.1 Partial storage](#41-partial-storage) | `partial` | gives up | about p | none |
| [4.2 Time/storage](#42-timestorage) | `timestorage` | brute-forces | all | about (1-p)² · N / 2 hash calls per challenge |

Suggested order for a demo: the basic scheme (section 3), then 4.1, 4.2 and section 5.

### 4.1 Partial storage

*Code: `pos/provers/partial_storage.py`, `experiments/partial_storage.py`, `tests/test_partial_storage.py`*

**What it does**
- The cheater builds the full table, keeps only part of it (e.g. 50%), and throws the rest away to save space.
- If a challenge's answer is in the part it kept, it looks it up instantly.
- Otherwise it has no answer, and fails that challenge.

**How to run it**
```bash
python main.py --prover partial --fraction 0.5 --challenges 1      # one challenge: about 50% success
python main.py --prover partial --fraction 0.5 --challenges 5      # all five must pass: about 3% success
python main.py --prover partial --fraction 0 --challenges 1        # keeps nothing: proof fails
python -m experiments.partial_storage                              # honest prover vs many cheaters, N = 4096
python -m experiments.partial_storage --n-bits 14 --challenges 500 # bigger, more accurate
```
The experiment prints one row per prover: how much it stores and how many challenges it passes.

**What it shows** (N = 2^12, one challenge per proof):

| Stored | Challenges passed |
|---|---|
| 100% (honest) | 100% |
| 75% | about 75% |
| 50% | about 50% |
| 25% | about 25% |
| 0% | 0% |

- A cheater passes about **as often as the share of the table it kept**, while using only that share of the space.
- With **one challenge per proof**, a cheater keeping 50% fools the verifier half the time. So the basic scheme gives **no real guarantee**.
- Increasing `--challenges` requires every challenge to pass, reducing partial-storage success to about p^c for c independent challenges.

### 4.2 Time/storage

*Code: `pos/provers/time_storage.py`, `experiments/time_storage.py`, `tests/test_time_storage.py`.
Diagram: [`Project/Diagramms/TimeStorageAttack`](../Diagramms/TimeStorageAttack.svg).*

**What it does**

Same cheater as 4.1, as it stores only a fraction $p$ of the table. The difference is what happens on a miss.

- **Hit:** the challenge answer is in the stored part of the table. Cost: 0 hash calls.
- **Miss:** the answer is not stored. Instead of giving up, the prover **brute-forces**, recomputing $f(x)$ for the inputs it dropped, one by one, until $f(x) = y$ (stored inputs never need to be checked).

Because every answer exists in the table, this prover **always answers correctly** while using less space than the honest one. It pays with time:

- **Worst case:** $S = p \cdot N$ entries stored and $T = (1-p) \cdot N$ hash calls, so $\mathbf{S + T = N}$. Space and time trade off along a straight line.
- **Average case:** a hit costs 0 and a miss costs about $(1-p) \cdot N / 2$, so a challenge costs $(1-p)^2 \cdot N / 2$ hash calls on average.


**How to run it**
```bash
python main.py --prover timestorage --fraction 0.5 --n-bits 14 --challenges 10   # always accepted; misses cost hash calls and time
python -m experiments.time_storage                                               # storage vs hash calls vs time
python -m experiments.time_storage --n-bits 14 --challenges 100                  # bigger table: brute force takes longer
```
Look at the "hash calls" and "ms" printed after each challenge: a hit costs 0,
a miss costs thousands.

**Historical results for the previous BLAKE2b setup** ($N = 2^{14} = 16384$, 100 challenges per prover, all provers pass 100% of challenges, times depend on the machine)

| Stored | S (entries) | Avg calls | Expected avg | Max calls | T (worst) | S + T | Avg time |
|---|---|---|---|---|---|---|---|
| 100% (honest) | 16384 | 0.0 | 0.0 | 0 | 0 | 16384 | 0.00 ms |
| 90% | 14746 | 72.6 | 81.9 | 1321 | 1638 | 16384 | 0.13 ms |
| 75% | 12288 | 449.4 | 512.0 | 4061 | 4096 | 16384 | 0.67 ms |
| 50% | 8192 | 2129.2 | 2048.0 | 8123 | 8192 | 16384 | 3.66 ms |
| 25% | 4096 | 4818.3 | 4608.0 | 12274 | 12288 | 16384 | 8.06 ms |
| 10% | 1638 | 7164.2 | 6635.5 | 14728 | 14746 | 16384 | 13.23 ms |
| 0% | 0 | 8831.3 | 8192.0 | 16364 | 16384 | 16384 | 14.88 ms |

How to read the columns:
- **S** is the number of entries the prover stores: $p \cdot N$, where $N$ is the total number of inputs and $p$ is the fraction stored.
- **Avg calls** is the measured mean number of hash calls over all challenges.
- **Expected avg** is the theoretical mean, $(1-p)^2 \cdot N / 2$: a miss happens with probability $1-p$ and, on average, the answer is found halfway through the $(1-p) \cdot N$ dropped inputs. Measured values differ slightly because the run has only a finite number of random challenges.
- **Max calls** is the most expensive single challenge seen in this run.
- **T** is the theoretical worst case for one challenge: a miss whose answer is the last dropped input scans all of them, i.e. $N - S = (1-p) \cdot N$ hash calls.
- **S + T = N** in every row: this is the straight-line trade-off. The average column cannot show it, because the average mixes hits and misses.

Takeaways
- Unlike the partial cheater, this one **never fails**: less storage just means more work.
- Storing nothing is plain brute force: about $N/2$ hash calls per challenge.
- Time follows the hash-call count, so hash calls are the main measure and milliseconds are a sanity check.

---

## 5. Input validation

The prover is untrusted, and users make typos, so inputs are checked where they enter:

| Where | What is checked | Where in the code |
|---|---|---|
| The prover's answer | must be a real `int` (not `float`, `str`, `list`, `None`, not even `True`) in [0, N). Anything else is rejected, never converted. The verifier does not crash and spends no hash calls on it. | `Scheme.is_domain_element()` in `pos/schemes/base.py`, used by `SimpleScheme.is_valid()` |
| Plot parameters | `n_bits` is an `int` from 1 to `MAX_N_BITS` (24); Feistel additionally requires an even width of at least 2 | `PoSParams` in `pos/params.py` |
| Feistel settings | Positive round count and optional 16-byte master key | `PoSParams` in `pos/params.py` |
| Cheater settings | `fraction` is a number from 0 to 1 (rejects `nan`, `True`, strings, `None`), checked when the prover is created | `PartialStorageProver` (also used by `TimeStorageProver`) |
| Command line | `--n-bits`, `--seed`, `--challenges`, `--fraction` give a clear usage error instead of a traceback | `pos/cli.py`, used by `main.py` and `experiments/time_storage.py` |

**See it in action:**
```bash
python main.py --challenges 0                    # usage error, not a crash
python main.py --n-bits 40                       # too big: refused before building a huge table
python main.py --n-bits 3                        # Feistel requires an even width
python main.py --prover partial --fraction 2     # fraction must be between 0 and 1
```
- To allow bigger tables, raise `MAX_N_BITS` in `pos/params.py` (you need the memory for N entries).
- Not covered here (later steps): a **time limit** for the prover and **replayed
  challenges** (step 3, "Repeated challenges + time limit").

---

## 6. Tests

```bash
python -m unittest discover tests     # all tests: should end with OK
python -m unittest tests.test_verifier   # just one file
```
Run the full set before every commit/push.

| File | What it checks |
|---|---|
| `test_basic.py` | The hash function, and the protocol with the honest prover |
| `test_feistel.py` | Feistel permutation, determinism, exhaustive uniqueness, and trusted inverse |
| `test_partial_storage.py` | The partial storage attack |
| `test_time_storage.py` | The time/storage attack |
| `test_verifier.py` | Input sanitizing: prover answers, parameters, command line |

---

## 7. Files

```
pos/
  params.py         PoSParams: n_bits (N = 2^n_bits) and the plot seed, with range/type checks
  cli.py            Validators for command-line arguments (--n-bits, --seed, --challenges, --fraction)
  functions.py      HashFunction: original BLAKE2b comparison function
  feistel.py        FeistelPermutation: forward-only permutation and trusted inverse helper
  plot.py           Plot: the stored table (f(x) -> x), reports its size in bits
  schemes/
    base.py         Scheme interface: build plot, pick challenge, check answer; is_domain_element() sanitizes answers
    simple.py       Selects Feistel or BLAKE2b and builds the plot
  provers/
    base.py         Prover interface: setup(), answer(y), storage_bits()
    honest.py       Honest prover: full table, answers by lookup
    partial_storage.py  Attack 4.1: keeps only part of the table
    time_storage.py     Attack 4.2: keeps part of the table, brute-forces what is missing
  verifier.py       Verifier: new_challenge(), check(y, answer)
experiments/
  partial_storage.py    Compares the honest prover with many cheaters
  time_storage.py       Time/storage attack: storage vs hash calls vs time
main.py             Demo: initialization + challenges (choose the prover), reports hash calls and time
tests/              unittest tests
```

---

## 8. Group workflow (mandatory so we don't mess up anything :)

> **Rule: never commit directly to `main`.**
> Every change goes on its own branch and reaches `main` through a pull request that at least one other group member has looked at.

This keeps `main` working at all times, lets the group see every change before it lands, and stops people overwriting each other's work.

These commands are run from the **repo's top folder** (`AAU-1st-Semester-Repo-Group-8`), not from `Project/PoSpace`.

### Step 1: Start from an up-to-date `main`
```bash
git checkout main
git pull
```
Always do this before creating a new branch, so you start from everyone's latest work.

### Step 2: Create your own branch
```bash
git checkout -b your-name/short-description
```

One branch per task. Keep tasks small so they're quick to review.

### Step 3: Make your changes and test them
Edit the code, then check nothing broke:
```bash
cd Project/PoSpace
python main.py
python -m unittest discover tests
cd ../..
```

### Step 4: Commit
```bash
git status                     # see what changed
git add Project/PoSpace        # add your changes
git commit -m "Add partial storage attack"
```
Write commit messages that say **what** you did, in a few words.
Commit as often as you like. Small commits are easier to follow.

### Step 5: Push your branch to GitHub
First time pushing this branch:
```bash
git push -u origin your-name/short-description
```
After that, just:
```bash
git push
```

### Step 6: Open a pull request
1. Go to the repo on GitHub.
2. Click **Compare & pull request** (yellow banner), or go to
   **Pull requests → New pull request** and choose
   `base: main` ← `compare: your-name/short-description`.
3. Write a short description: what you changed, why, and how to test it.
4. Click **Create pull request** and tell the group in the chat.

### Step 7: Review
- **At least one other group member** reads the changes and runs the code.
- They leave comments, or approve.
- If changes are needed, fix them on the **same branch**, then commit and push again.
  The pull request updates automatically.

### Step 8: Merge into `main`
Once approved, click **Merge pull request → Confirm merge** on GitHub.
Then click **Delete branch** on GitHub (the work is safe in `main` now).

### Step 9: Update your laptop
```bash
git checkout main
git pull
git branch -d your-name/short-description    # delete your local copy of the branch
```

### Keeping your branch up to date
If `main` changed while you were working (someone else merged first), bring
their changes into your branch before opening or merging your pull request:
```bash
git checkout main
git pull
git checkout your-name/short-description
git merge main
```
If Git reports a **conflict**, open the listed files in VS Code. It highlights
the clashing parts and lets you choose **Accept Current**, **Accept Incoming**
or **Accept Both**. Save, then:
```bash
git add .
git commit -m "Merge main into my branch"
git push
```
Not sure how to resolve a conflict? Ask in the group chat before guessing.

### Quick reference

| I want to… | Command |
|---|---|
| See which branch I'm on | `git branch` |
| See what I changed | `git status` |
| Get the latest `main` | `git checkout main` then `git pull` |
| Start a new task | `git checkout -b your-name/task` |
| Save my work | `git add .` then `git commit -m "message"` |
| Upload my branch | `git push` (first time: `git push -u origin your-name/task`) |
| Switch branches | `git checkout branch-name` |
| Undo changes to a file I haven't committed | `git restore path/to/file` |

**Golden rules**
1. Never commit directly to `main`.
2. `git pull` on `main` before starting new work.
3. One task per branch.
4. Run the tests before pushing.
5. Someone else reviews before merging.

---

## 9. Extending the code

- **An attack** is a new `Prover` subclass in `pos/provers/`. Export it in
  `pos/provers/__init__.py`, add it to `--prover` in `main.py`, and give it its
  own subsection in section 4 (idea, how to run, results, code files).
- **A new construction** (e.g. the collision-based g_f) is a new `Scheme`
  subclass in `pos/schemes/`, implementing `build_plot`, `sample_challenge`
  and `is_valid`.
- **Security measures** (repeated challenges, time limits) go in `verifier.py`.
- **Never trust the prover's answer.** In a new scheme's `is_valid`, check every
  part of the answer with `self.is_domain_element(...)` before evaluating f on it
  (the collision-based scheme has two parts, x and x').
- **New command-line options** should use the validators in `pos/cli.py`
  (`int_in_range`, `fraction`) so bad values give a usage error.
- **Add a test** in `tests/` for anything new, so the group knows it works.