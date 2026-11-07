# Proof of Space: implementation and attacks

A step-by-step implementation of proofs of space. We start with the simplest scheme (no security measures), attack it, add defences, and attack again.

| Step | Type | Status |
|---|---|---|
| 1. Basic scheme: prover stores a table, verifier sends challenges | Construction | ✅ Done |
| 2. Partial storage attack (keep only part of the table) and time-storage attack (brute-force the rest) | Attack | ✅ Done |
| 3. Repeated challenges + time limit | Defence | To do |
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
Initialization (N = 2^8 = 256, seed = 1)
  table entries:     256
  storage:           67,584 bits
  setup evaluations: 256
  setup time:        0.000 s

Challenges
  #1   y = 351e604a30d7...  answer x = 68       accepted  (0 hash calls, 0.00 ms)

Accepted 1/1
Average hash calls per challenge: 0.0
Average time per challenge:       0.00 ms
```
- **Initialization** is done once: the prover builds its table, and we print how big it is.
- **Each challenge line** shows the challenge `y` (shortened), the prover's answer, whether the verifier accepted it, and the prover's work for that challenge.
- Work is reported two ways: **hash calls** (the same on every machine, our main measure) and **wall-clock time** (depends on your computer). The time covers only the prover answering, not the verifier checking.

**Options** (combine them freely; `python main.py --help` lists them):
```bash
python main.py --n-bits 12 --challenges 20 --seed 42
python main.py --prover timestorage --fraction 0.5
```

| Option | Meaning | Allowed | Default |
|---|---|---|---|
| `--n-bits` | Table size, N = 2^n_bits | integer, 1 to 24 | 8 (N = 256) |
| `--challenges` | Number of challenges the verifier sends | integer, at least 1 | 1 |
| `--seed` | The plot's seed (its identity): a different seed gives a completely different table | integer, 0 to 2^128 - 1 | 1 |
| `--prover` | Who answers: `honest`, or one of the attacks `partial`, `timestorage` (see [section 4](#4-attacks)) | one of the three | honest |
| `--fraction` | For the attacks: share of the table the cheater keeps | number, 0 to 1 | 0.5 |

A value outside the allowed range gives a short usage error, for example `main.py: error: argument --challenges: must be at least 1, got 0` (see [section 5](#5-input-validation)).

---

## 3. The basic scheme

**Initialization (done once by the prover)**
- The function is f(x) = BLAKE2b(seed, x), using the **full 256-bit hash output**.
- Inputs x come from [0, N), with N = 2^n_bits.
- The prover computes f(x) for every x in [0, N) and stores a table f(x) → x.

**Proof of execution (repeated every round)**
1. The verifier picks a random x and sends the challenge y = f(x).
2. The prover looks up y in its table and sends back an x with f(x) = y.
3. The verifier checks: the answer is a genuine integer (not a float, string, `None`, ...), x is in range, and f(x) equals y.

**Notes**
- **We don't reduce the output mod N.** The hash keeps its full strength, so the   scheme's weakness can't be blamed on a weakened function. Finding x for a given y still takes up to N tries, because there are only N possible inputs. That is what the proof of space relies on.
- **No collisions in practice.** With 256-bit outputs, two x values practically never give the same y, so the table has exactly N entries.
- **Each entry stores y and x** (256 + n_bits bits). The output shows y as its first 12 hex digits to keep it readable.
- **The prover doesn't send the seed.** The verifier already knows which plot it's checking.
- **Every function object counts its evaluations** (`calls`), so we can measure how much work each prover does.

**Look at the prover's table** (the first 20 rows, y shortened to 12 hex digits):
```bash
python -c "from pos import PoSParams; from pos.schemes import SimpleScheme; from pos.provers import HonestProver; p = HonestProver(SimpleScheme(PoSParams(n_bits=8, seed=1))); p.setup(); [print(f'{y:064x}'[:12], '->', x) for y, x in sorted(p.plot._entries.items())[:20]]"
```
Change `seed=1` or `n_bits=8` to look at other plots, remove `[:20]` to print everything, or swap `HonestProver(...)` for `PartialStorageProver(..., fraction=0.5, rng_seed=1)` to see a cheater's table.

**What to point out:** the prover builds the table once and then answers every challenge with a lookup (0 hash calls). Storage grows with N, and every seed gives its own plot.

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
python main.py --prover partial --fraction 0.5 --challenges 10     # keeps 50%: passes about half
python main.py --prover partial --fraction 0 --challenges 10       # keeps nothing: fails everything
python -m experiments.partial_storage                              # honest prover vs many cheaters, N = 4096
python -m experiments.partial_storage --n-bits 14 --challenges 500 # bigger, more accurate
```
The experiment prints one row per prover: how much it stores and how many challenges it passes.

**What it shows** (N = 2^12):

| Stored | Challenges passed |
|---|---|
| 100% (honest) | 100% |
| 75% | about 75% |
| 50% | about 50% |
| 25% | about 25% |
| 0% | 0% |

- A cheater passes about **as often as the share of the table it kept**, while using only that share of the space.
- With **one challenge per proof**, a cheater keeping 50% fools the verifier half the time. So the basic scheme gives **no real guarantee**.

### 4.2 Time/storage

*Code: `pos/provers/time_storage.py`, `experiments/time_storage.py`, `tests/test_time_storage.py`.
Diagram: [`Project/Diagramms/TimeStorageAttack`](../Diagramms/TimeStorageAttack.svg).*

**What it does**
- Same cheater as 4.1 (keeps a share p of the table), but on a miss it does not give up. It **brute-forces**: it computes $f(x)$ for the inputs it dropped until $f(x) = y$.
- Stored inputs are skipped. For them $f(x)$ is already known (it is in the table) and it is not $y$, otherwise the lookup would have found it.
- So it **always answers correctly**, uses less space than the honest prover, and pays with time: a hit costs 0 hash calls, a miss costs up to $(1-p) \cdot N$. On average that is $(1-p)^2 \cdot N / 2$ hash calls per challenge, so space and time trade off roughly linearly ($S \cdot T$ is about $N$).

**How to run it**
```bash
python main.py --prover timestorage --fraction 0.5 --n-bits 14 --challenges 10   # always accepted; misses cost hash calls and time
python -m experiments.time_storage                                               # storage vs hash calls vs time
python -m experiments.time_storage --n-bits 14 --challenges 100                  # bigger table: brute force takes longer
```
Look at the "hash calls" and "ms" printed after each challenge: a hit costs 0,
a miss costs thousands.

**What it shows** (N = 2^14, 100 challenges; time depends on the machine):

| Stored | Challenges passed | Avg hash calls | Expected (1-p)²·N/2 | Avg time |
|---|---|---|---|---|
| 100% (honest) | 100% | 0 | 0 | 0.00 ms |
| 90% | 100% | 72.6 | 81.9 | 0.08 ms |
| 75% | 100% | 449.4 | 512.0 | 0.43 ms |
| 50% | 100% | 2129.2 | 2048.0 | 1.93 ms |
| 25% | 100% | 4818.3 | 4608.0 | 4.43 ms |
| 10% | 100% | 7164.2 | 6635.5 | 6.10 ms |
| 0% | 100% | 8831.3 | 8192.0 | 7.46 ms |

- Unlike the partial cheater, this one **never fails**: less storage just means more work.
- Storing nothing is plain brute force: about N/2 hash calls per challenge.
- Time follows the hash-call count (about 1 µs per call on the machine used here), which is why hash calls are the main measure and milliseconds are a sanity check.

---

## 5. Input validation

The prover is untrusted, and users make typos, so inputs are checked where they enter:

| Where | What is checked | Where in the code |
|---|---|---|
| The prover's answer | must be a real `int` (not `float`, `str`, `list`, `None`, not even `True`) in [0, N). Anything else is rejected, never converted. The verifier does not crash and spends no hash calls on it. | `Scheme.is_domain_element()` in `pos/schemes/base.py`, used by `SimpleScheme.is_valid()` |
| Plot parameters | `n_bits` is an `int` from 1 to `MAX_N_BITS` (24, so a typo can't try to build a 2^40 table); `seed` is an `int` from 0 to 2^128 - 1 (it is stored in a 16-byte key) | `PoSParams` in `pos/params.py` |
| Cheater settings | `fraction` is a number from 0 to 1 (rejects `nan`, `True`, strings, `None`), checked when the prover is created | `PartialStorageProver` (also used by `TimeStorageProver`) |
| Command line | `--n-bits`, `--seed`, `--challenges`, `--fraction` give a clear usage error instead of a traceback | `pos/cli.py`, used by `main.py` and `experiments/time_storage.py` |

**See it in action:**
```bash
python main.py --challenges 0                    # usage error, not a crash
python main.py --n-bits 40                       # too big: refused before building a huge table
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
| `test_partial_storage.py` | The partial storage attack |
| `test_time_storage.py` | The time/storage attack |
| `test_verifier.py` | Input sanitizing: prover answers, parameters, command line |

---

## 7. Files

```
pos/
  params.py         PoSParams: n_bits (N = 2^n_bits) and the plot seed, with range/type checks
  cli.py            Validators for command-line arguments (--n-bits, --seed, --challenges, --fraction)
  functions.py      HashFunction: f(x) = BLAKE2b(seed, x), full 256-bit output, counts its calls
  plot.py           Plot: the stored table (f(x) -> x), reports its size in bits
  schemes/
    base.py         Scheme interface: build plot, pick challenge, check answer; is_domain_element() sanitizes answers
    simple.py       The simple scheme described above
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