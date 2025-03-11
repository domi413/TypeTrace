#!/bin/bash

commit_rules() {
    echo "Rules for commits: (^(fix|feat|pipeline|doc|wip)\(\#TYP-[0-9]+\): .+)|(Merge .+)"
    echo '#!/bin/bash' >./.git/hooks/commit-msg
    echo 'pattern="^(fix|feat|pipeline|doc|wip)\(#TYP-[0-9]+\): .+|Merge .+"' >>./.git/hooks/commit-msg
    echo 'commit_message=$(cat "$1")' >>./.git/hooks/commit-msg
    echo 'if ! [[ "$commit_message" =~ $pattern ]]; then' >>./.git/hooks/commit-msg
    echo '  echo "Invalid commit message format! Use this format: fix|feat|pipeline|doc|wip(#TICKET-ID): {description}"' >>./.git/hooks/commit-msg
    echo '  exit 1' >>./.git/hooks/commit-msg
    echo 'fi' >>./.git/hooks/commit-msg
    chmod +x ./.git/hooks/commit-msg
}

# Main execution
echo "Installing commit rules..."
commit_rules