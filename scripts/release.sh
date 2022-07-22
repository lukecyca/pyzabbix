#!/usr/bin/env bash

set -u

error() {
  echo >&2 "error: $*"
  exit 1
}

# This scripts will:
# - Expect the setup.py file to have new version
# - Stash the setup.py file
# - Check for clean state (no uncommitted changes), exit if failed
# - Clean the project
# - Install the project, lint and runt tests, exit if failed
# - Unstash the pyproject version bump and commit a new Release
# - Tag the new release
# - Show instruction to push tags and changes to github

command -v make > /dev/null || error "make command not found!"
command -v git > /dev/null || error "git command not found!"
command -v python3 > /dev/null || error "python3 command not found!"

setup="setup.py"
default_branch="master"

[[ "$(git rev-parse --show-toplevel)" == "$(pwd)" ]] || error "please go to the project root directory!"
[[ "$(git rev-parse --abbrev-ref HEAD)" == "$default_branch" ]] || error "please change to the $default_branch git branch!"

pkg_version=$(python3 setup.py --version || error "could not determine package version in $setup!")
git_version=$(git describe --abbrev=0 --tags || error "could not determine git version!")

# No version change
if [[ "$pkg_version" == "$git_version" ]]; then
    echo "Latest git tag '$pkg_version' and package version '$git_version' match, edit your $setup to change the version before running this script!"
    exit
fi

git stash push --quiet -- "$setup"
trap 'e=$?; git stash pop --quiet; exit $e' EXIT

[[ -z "$(git status --porcelain)" ]] || error "please commit or clean the changes before running this script!"

git clean -xdf

make lint test || error "tests failed, please correct the errors"

new_tag="$pkg_version"
release="chore: release $new_tag"

git stash pop --quiet
git add "$setup" || error "could not stage $setup!"
git commit -m "$release" --no-verify || error "could not commit the version bump!"
git tag "$new_tag" -a -m "$release" || error "could not tag the version bump!"

echo "Run 'git push --follow-tags' in order to publish the release on Github!"
