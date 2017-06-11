# Style guide

1. Follow PEP8.
2. Use a 99 maximum character length instead of 79, but strive towards 79.
3. This is Python, not Java, Go, and definitely not JavaScript.
4. Watch ["Beyond PEP8" by Raymond Hettinger](https://www.youtube.com/watch?v=wf-BqAjZb8M).


# Commits and Pull Requests

All commits and pull requests should follow the following guidelines:

1. Keep pull requests **atomic**.
2. Provide a **clear explanation** of the feature or bug that you're addressing.
3. Conform to the **style guide**.
4. Somewhat conform to [Git commit guidelines set by Git itself](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines). I'm pretty loose on this, just make it descriptive.
5. **Squash your commits** into 1 commit or into a few atomic commits where 1 commit is 1 feature that works.
6. Base it on the **most recent default branch** (the branch GitHub shows by default).
7. Use a **new branch** for your commit. [This makes it easy to checkout to a pull requests' branch](https://help.github.com/articles/checking-out-pull-requests-locally/).

## New features
1. Try to only add **1 feature per pull request**.

## Bugs
1. **Add failing tests** to your pull request. This clearly shows the problem.
2. *(optional) Add code to fix your failing tests in a separate commit. Making it a separate commit will still show the failed test(s) of the first commit.*
3. Squashed commits should remove the failing test commit.
