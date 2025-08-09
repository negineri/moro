# Smart Commit

An intelligent git commit command that analyzes staged changes and creates an appropriate commit message following the project's commit conventions.

## Usage

```
/smart-commit
```

## What it does

1. Analyzes git status to see staged changes
2. Reviews git diff to understand the nature of changes
3. Examines recent commit history to follow existing message style
4. Generates an appropriate commit message based on the changes
5. Creates the commit with the generated message

## Implementation

You are a git commit assistant. Follow these steps to create an intelligent commit:

1. **Analyze the current state**: Run `git status` and `git diff --staged` in parallel to understand what changes are staged for commit.

2. **Study commit history**: Run `git log --oneline -10` to understand the existing commit message style and conventions used in this repository.

3. **Analyze the changes**: Based on the staged diff, determine:

   - Type of changes (feat, fix, refactor, docs, test, chore, etc.)
   - Scope of changes (which modules/components are affected)
   - Nature of the changes (what functionality is being added/modified/removed)

4. **Generate commit message**: Create a concise, descriptive commit message that:

   - Follows the conventional commit format used in the repository
   - Accurately describes the changes and their purpose
   - Uses imperative mood (e.g., "add", "fix", "refactor")
   - Focuses on the "why" rather than just the "what"
   - Is 50-72 characters for the first line
   - Includes a body with more details if needed

5. **Execute the commit**: Run the git commit command with the generated message using a heredoc format:

   ```bash
   git commit -m "$(cat <<'EOF'
   [commit message here]
   EOF
   )"
   ```

6. **Verify success**: Run `git status` to confirm the commit was successful.

## Requirements

- Only commit if there are staged changes
- Never commit if there are no changes
- Follow the repository's existing commit message conventions
- Ensure the commit message accurately reflects the staged changes
