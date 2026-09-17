#!/usr/bin/env python3
from github import Github
import os

# Create 'implementation' label if missing and add to recent issues without it
repo = Github().get_repo('huchufan/github')
labels = [l.name for l in repo.get_labels()]
if 'implementation' not in labels:
    repo.create_label('implementation', 'FFA500', 'Work items implementing module scaffolds')

issues = repo.get_issues(state='open')
count = 0
for issue in issues:
    names = [l.name for l in issue.labels]
    if 'implementation' not in names:
        issue.add_to_labels('implementation')
        count += 1
print('ADDED', count)
