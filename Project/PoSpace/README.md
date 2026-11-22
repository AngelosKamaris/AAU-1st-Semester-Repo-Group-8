# Proof of Space — Stage 1

A single-challenge, untimed proof of space using truncated BLAKE2b.

**Contents**
1. [Group workflow](#1-group-workflow-mandatory-so-we-dont-mess-up-anything-)
2. [Setup](#2-setup)
3. [Quick start](#3-quick-start)
4. [Plot and verification](#4-plot-and-verification)
5. [Storage experiments](#5-storage-experiments)
6. [Tests](#6-tests)

---

## 1. Group workflow (mandatory so we don't mess up anything :)

> **Rule: never commit directly to `main`.**
> Every change goes on its own branch and reaches `main` through a pull request that at least one other group member has looked at.

This keeps `main` working at all times, lets the group see every change before it lands, and stops people overwriting each other's work.

First time here? Do the [Setup](#2-setup) first, then come back.

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

## 2. Setup

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

## 3. Quick start

Run from `Project/PoSpace` with Python 3:

```bash
python main.py
python main.py --n-bits 12 --challenges 20 --seed 1 --challenge-seed 42
```

Stage 1 verifies one untimed challenge per trial. `--challenges` controls the
number of independent trials. `--seed` (also `--seed-f`) sets the public plot seed.
Omit `--challenge-seed` for OS-backed randomness.

## 4. Plot and verification

The prover evaluates all `N = 2**n_bits` inputs. For each fixed-width input it
takes the first `n_bits` of the BLAKE2b digest, keyed by the `f` tag and public
seed. The plot keeps one preimage per distinct hash output.

The verifier hashes a random input and sends the output. It checks the
returned preimage without accessing the plot. Storage figures are packed table
sizes, not Python object overhead. Online evaluation counts exclude setup.

## 5. Storage experiments

The partial-storage prover keeps a random subset of the plot and fails on a
miss. The time/storage prover searches the inputs it did not retain. Without a
deadline or query limit it can answer every Stage 1 challenge. With `S` retained
entries, a miss takes at most `N - S` hash evaluations; collisions can yield
an earlier match.

```bash
python main.py --prover partial --fraction 0.5 --challenges 20
python -m experiments.partial_storage --n-bits 12 --challenges 300
python -m experiments.time_storage --n-bits 12 --challenges 300
```

The experiment modules measure individual untimed challenges. See the
[time/storage diagram](../Diagramms/TimeStorageAttack.svg) for the search process.

## 6. Tests

```bash
python -m unittest discover tests
```
