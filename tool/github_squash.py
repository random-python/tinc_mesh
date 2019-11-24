#!/usr/bin/env python

"""
Squash github commits starting from a point
"""

from devrepo import shell

point = "b9e905d72aa6ddb663e801632d5fa661bccc9679"
message = "Develop"

shell(f"git reset --soft {point}")
shell(f"git add --all")
shell(f"git commit --message='{message}'")
shell(f"git push --force --follow-tags")
