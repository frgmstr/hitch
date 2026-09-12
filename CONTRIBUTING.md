# Contributing to Hitch

Thanks for your interest in improving Hitch! This profile is a general-purpose fork
of an internal automobile-buying assistant. All contributions are welcome.

## How to Contribute

1. **Fork** this repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/hitch.git
   cd hitch
   ```
3. **Create a branch** for your feature or bugfix:
   ```bash
   git checkout -b feat/my-new-feature
   ```
4. **Make your changes**:
   - Update the relevant skill's `SKILL.md` and any reference files under `references/`.
   - If you add new scripts, include a `# >>> PERSONALIZE <<<` comment block where users need to fill in their own values.
   - Keep all file paths portable — use `${HERMES_ARCHIVE_DIR}` or relative paths, never absolute Windows paths like `C:/Users/...`.
5. **Test locally**:
   ```bash
   python -m py_compile skills/research/automobile-value-rubric/scripts/rubric-score.py
   ```
6. **Commit** and push to your fork:
   ```bash
   git add .
   git commit -m "feat: describe what you changed"
   git push origin feat/my-new-feature
   ```
7. **Open a Pull Request**. Describe the change, why it's needed, and how it was tested.

## Guidelines

- **Stay vehicle-agnostic**: This profile is intentionally generic. Do not add make/model-specific logic to core skills — put that in `value-model.json` or trim tables marked `# >>> PERSONALIZE <<<`.
- **Secrets never live in the repo**: All credentials go in `.env`, which is gitignored. Update `.env.example` when you add a new required variable.
- **Document changes**: If your change affects how users personalize the profile, update `README.md`'s "Personalizing for Your Vehicle" section.

## Reporting Issues

Open an issue on GitHub if:
- The profile fails to import in Hermes Agent.
- A skill crashes or produces incorrect output.
- Documentation is unclear or outdated.

Include your OS, Hermes version, and the exact error message.