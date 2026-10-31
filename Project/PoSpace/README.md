# Proof of Space: basic implementation

The simplest proof of space, with no security measures yet: a prover stores a
table, a verifier sends challenges and checks the answers.

**Contents**
1. [Setup](#1-setup)
2. [Running the code](#2-running-the-code)
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
| `--challenges` | Number of challenges the verifier sends | 10 |
| `--seed` | The plot's seed (its identity) | 1 |

**Run the tests:**
```bash
python -m unittest discover tests
```
The output should end with `OK`.

**If `python` isn't recognised:** use `py` (Windows) or `python3` (Mac/Linux) instead.

**What a successful run looks like:**
```
Initialization (N = 2^8 = 256, seed = 1)
  table entries:     168
  storage:           1,344 bits
  setup evaluations: 256

Challenges
  #1   y = 164      answer x = 17       accepted
  ...
Accepted 10/10
```

---

## 3. How it works

**Initialization (done once by the prover)**
- The function is f(x) = BLAKE2b(seed, x) mod N, with N = 2^n_bits.
- The prover computes f(x) for every x in [0, N) and stores a table f(x) → x.

**Proof of execution (repeated every round)**
1. The verifier picks a random x and sends the challenge y = f(x).
2. The prover looks up y in its table and sends back an x with f(x) = y.
3. The verifier checks: there is an answer, x is in range, and f(x) equals y.

**Notes**
- **The table has about 63% of N entries, not N.** A random function never
  produces about 37% of the possible values.
- **The prover doesn't send the seed.** The verifier already knows which plot
  it's checking.
- **Every function object counts its evaluations** (`calls`), so later we can
  measure how much work an attacker does.

---

## 4. Files

```
pos/
  params.py         PoSParams: n_bits (N = 2^n_bits) and the plot seed
  functions.py      HashFunction: f(x) = BLAKE2b(seed, x) mod N, counts its calls
  plot.py           Plot: the stored table (f(x) -> x), reports its size in bits
  schemes/
    base.py         Scheme interface: build plot, pick challenge, check answer
    simple.py       The simple scheme described above
  provers/
    base.py         Prover interface: setup(), answer(y), storage_bits()
    honest.py       Honest prover: full table, answers by lookup
  verifier.py       Verifier: new_challenge(), check(y, answer)
main.py             Demo: initialization + challenges
tests/              unittest tests
```

---

## 5. Group workflow (mandatory)

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
  subclass in `pos/schemes/`. Register it in `SCHEMES` in `pos/schemes/__init__.py`.
- **Security measures** (repeated challenges, time limits) go in `verifier.py`.
- **Add a test** in `tests/` for anything new, so the group knows it works.
