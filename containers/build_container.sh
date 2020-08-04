#!/usr/bin/env bash
echo "Usage: build_container.sh <varifier_repo_URL> <commit_id or branch>"
echo "<varifier_repo_URL> defaults to https://github.com/iqbal-lab-org/varifier/ if not provided"
echo "<commit_id or branch> defaults to master if not provided"
echo "An image with name varifier:<commit_id> will be created"
echo "e.g.: build_container.sh https://github.com/leoisl/varifier 3807a1 "
echo "will create image varifier:3807a1 "

varifier_repo_URL=${1:-"https://github.com/iqbal-lab-org/varifier/"}
commit_id_or_branch=${2:-"master"}

echo $varifier_repo_URL
echo $commit_id_or_branch

sudo docker build --build-arg varifier_repo_URL=${varifier_repo_URL} --build-arg commit_id_or_branch=${commit_id_or_branch} . -t varifier:"$commit_id_or_branch"
