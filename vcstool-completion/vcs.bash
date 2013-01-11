function _vcs()
{
    local cur
    COMPREPLY=()
    cur=${COMP_WORDS[COMP_CWORD]}

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $( compgen -W "`vcs --commands`" -- $cur ))
    fi
}

complete -o dirnames -F _vcs vcs
