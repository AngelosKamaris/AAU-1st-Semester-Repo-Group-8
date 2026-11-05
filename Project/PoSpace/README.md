# Proof of Space: implementation and attacks

A step-by-step implementation of proofs of space. We start with the simplest
scheme (no security measures), attack it, add defences, and attack again.

| Step | Type | Status |
|---|---|---|
| 1. Basic scheme: prover stores a table, verifier sends challenges | Construction | ✅ Done |
| 2. Partial storage attack (keep only part of the table) | Attack | ✅ Done |
| 3. Repeated challenges + time limit | Defence | To do |
| 4. Hellman's time-memory trade-off | Attack | To do |
| 5. Collision-based construction (g_f) | Construction | To do |
| 6. Nested Hellman attack | Attack | To do |

**Contents**
1. [Setup](#1-setup)
2. [Running the code](#2-running-the-code)
   - [Cheat sheet: what to run for what](#cheat-sheet-what-to-run-for-what)
3. [How it works](#3-how-it-works)
4. [Files](#4-files)
5. [Group workflow (mandatory)](#5-group-workflow-mandatory)
6. [Extending the code](#6-extending-the-code)

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

## 2. Running the code

All commands below are run from **this folder** (`Project/PoSpace`). In VS Code,
open a terminal with **Terminal → New Terminal**, then move here:

```bash
cd Project/PoSpace
```

**Run the demo:**
```bash
python main.py
```

**Options:**
```bash
python main.py --n-bits 12          # bigger table: N = 2^12 = 4096
python main.py --challenges 20      # more challenges
python main.py --seed 42            # a different plot
python main.py --n-bits 12 --challenges 20 --seed 42   # combine them
```

| Option | Meaning | Default |
|---|---|---|
| `--n-bits` | Table size, N = 2^n_bits | 8 (N = 256) |
| `--challenges` | Number of challenges the verifier sends | 1 |
| `--seed` | The plot's seed (its identity) | 1 |
| `--prover` | `honest` or `partial` (the attack) | honest |
| `--fraction` | Partial prover: share of the table it keeps (0 to 1) | 0.5 |

**Run the partial storage attack:**
```bash
python main.py --prover partial --fraction 0.5 --challenges 10    # keeps 50%
python main.py --prover partial --fraction 0.25 --challenges 10   # keeps 25%
```

**Compare the honest prover with many cheaters at once:**
```bash
python -m experiments.partial_storage
python -m experiments.partial_storage --n-bits 12 --challenges 300
```
This prints one row per prover: how much it stores and how many challenges it passes.

**Run the tests:**
```bash
python -m unittest discover tests
```
The output should end with `OK`.

**If `python` isn't recognised:** use `py` (Windows) or `python3` (Mac/Linux) instead.

**What a successful run looks like:**
```
Prover: honest
Initialization (N = 2^8 = 256, seed = 1)
  table entries:     256
  storage:           67,584 bits
  setup evaluations: 256

Challenges
  #1   y = 351e604a30d7...  answer x = 68       accepted  (0 hash calls)

Accepted 1/1
Average hash calls per challenge: 0.0
```

### Cheat sheet: what to run for what

Quick list of everything you can run right now. Copy, paste, done.
Run all of these from inside `Project/PoSpace` (if `python` doesn't work, try `py`).

**1. Show the basic scheme working (honest prover)**
```bash
python main.py                    # 1 challenge (default)
python main.py --challenges 10    # 10 challenges, all should be accepted
```
Good for showing: the prover builds the table once, then answers every
challenge with a lookup (0 hash calls).

**2. Show that it works for bigger tables / other plots**
```bash
python main.py --n-bits 12 --challenges 20             # N = 4096 instead of 256
python main.py --seed 42 --challenges 10               # different seed = completely different table
python main.py --n-bits 12 --challenges 20 --seed 42   # both
```
Good for showing: storage grows with N, and every seed gives its own unique plot.

**3. Show the prover's table (the plot)**

Honest prover, first 20 rows (y is shortened to its first 12 hex digits):
```bash
python -c "from pos import PoSParams; from pos.schemes import SimpleScheme; from pos.provers import HonestProver; p = HonestProver(SimpleScheme(PoSParams(n_bits=8, seed=1))); p.setup(); [print(f'{y:064x}'[:12], '->', x) for y, x in sorted(p.plot._entries.items())[:20]]"
```
Partial cheater (keeps 50%), first 20 rows:
```bash
python -c "from pos import PoSParams; from pos.schemes import SimpleScheme; from pos.provers import PartialStorageProver; p = PartialStorageProver(SimpleScheme(PoSParams(n_bits=8, seed=1)), fraction=0.5, rng_seed=1); p.setup(); print(len(p.plot), 'entries kept'); [print(f'{y:064x}'[:12], '->', x) for y, x in sorted(p.plot._entries.items())[:20]]"
```
Change `seed=1`, `n_bits=8` or `fraction=0.5` to look at other plots. Remove
`[:20]` to print the whole table.

**4. Showcase the partial storage attack**
```bash
python main.py --prover partial --fraction 0.5 --challenges 10    # keeps 50% -> passes about half
python main.py --prover partial --fraction 0.25 --challenges 10   # keeps 25% -> passes about a quarter
python main.py --prover partial --fraction 0 --challenges 10      # keeps nothing -> fails everything
```
Good for showing: the cheater uses less storage (look at the "storage" line)
but gets rejected whenever the answer was in the part it threw away.

**5. Compare the honest prover with all the cheaters in one table**
```bash
python -m experiments.partial_storage                              # N = 4096, 200 challenges each
python -m experiments.partial_storage --n-bits 14 --challenges 500 # bigger, more accurate
```
Good for showing: storing X% of the table means passing about X% of the
challenges. This is the main result of step 2.

**6. Check nothing is broken**
```bash
python -m unittest discover tests     # should end with OK
```
Run this before every commit/push.

**Suggested order for a demo:** 1 → 3 → 4 → 5.

---

## 3. How it works

**Initialization (done once by the prover)**
- The function is f(x) = BLAKE2b(seed, x), using the **full 256-bit hash output**.
- Inputs x come from [0, N), with N = 2^n_bits.
- The prover computes f(x) for every x in [0, N) and stores a table f(x) → x.

**Proof of execution (repeated every round)**
1. The verifier picks a random x and sends the challenge y = f(x).
2. The prover looks up y in its table and sends back an x with f(x) = y.
3. The verifier checks: there is an answer, x is in range, and f(x) equals y.

**Notes**
- **We don't reduce the output mod N.** The hash keeps its full strength, so the
  scheme's weakness can't be blamed on a weakened function. Finding x for a
  given y still takes up to N tries, because there are only N possible inputs.
  That is what the proof of space relies on.
- **No collisions in practice.** With 256-bit outputs, two x values practically
  never give the same y, so the table has exactly N entries.
- **Each entry stores y and x** (256 + n_bits bits). The output shows y as its
  first 12 hex digits to keep it readable.
- **The prover doesn't send the seed.** The verifier already knows which plot
  it's checking.
- **Every function object counts its evaluations** (`calls`), so we can
  measure how much work each prover does.

**Attack: partial storage** (`pos/provers/partial_storage.py`)
- The cheater builds the full table, keeps only part of it (e.g. 50%), and
  throws the rest away to save space.
- If a challenge's answer is in the part it kept, it looks it up instantly.
- Otherwise it has no answer, and fails that challenge.

**What the attack shows** (N = 2^12):
| Stored | Challenges passed |
|---|---|
| 100% (honest) | 100% |
| 75% | about 75% |
| 50% | about 50% |
| 25% | about 25% |
| 0% | 0% |

- A cheater passes about **as often as the share of the table it kept**,
  while using only that share of the space.
- With **one challenge per proof**, a cheater keeping 50% fools the verifier
  half the time. So the basic scheme gives **no real guarantee**.
- The next step (asking several challenges per proof) addresses this: keeping
  50% and passing 10 challenges in a row works only about 0.5^10 ≈ 0.1% of the time.

---

## 4. Files

```
pos/
  params.py         PoSParams: n_bits (N = 2^n_bits) and the plot seed
  functions.py      HashFunction: f(x) = BLAKE2b(seed, x), full 256-bit output, counts its calls
  plot.py           Plot: the stored table (f(x) -> x), reports its size in bits
  schemes/
    base.py         Scheme interface: build plot, pick challenge, check answer
    simple.py       The simple scheme described above
  provers/
    base.py         Prover interface: setup(), answer(y), storage_bits()
    honest.py       Honest prover: full table, answers by lookup
    partial_storage.py  Attack: keeps only part of the table
  verifier.py       Verifier: new_challenge(), check(y, answer)
experiments/
  partial_storage.py    Compares the honest prover with many cheaters
main.py             Demo: initialization + challenges (choose the prover)
tests/              unittest tests
```

---

## 5. Group workflow (mandatory so we don't mess up anything :)

> **Rule: never commit directly to `main`.**
> Every change goes on its own branch and reaches `main` through a pull request
> that at least one other group member has looked at.

This keeps `main` working at all times, lets the group see every change before
it lands, and stops people overwriting each other's work.

These commands are run from the **repo's top folder**
(`AAU-1st-Semester-Repo-Group-8`), not from `Project/PoSpace`.

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
Name it after **who** and **what**, for example:
- `waleed/partial-storage-attack`
- `angelos/hellman-attack`
- `aicha/fix-verifier-check`

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

## 6. Extending the code

- **An attack** is a new `Prover` subclass in `pos/provers/`. Export it in
  `pos/provers/__init__.py`.
- **A new construction** (e.g. the collision-based g_f) is a new `Scheme`
  subclass in `pos/schemes/`, implementing `build_plot`, `sample_challenge`
  and `is_valid`.
- **Security measures** (repeated challenges, time limits) go in `verifier.py`.
- **Add a test** in `tests/` for anything new, so the group knows it works.
