### MODIFY THESE ###

export MODULEHOME=/gpfs/runtime/pymodules
export MODULEPATH=/gpfs/runtime/modulefiles
export MODULESHELL=bash
export MODULEPYTHON=/usr/bin/python

# Exclude the following space-separated list of users from loading the modules
# environment.
EXCLUDE_USERS="root"

### DO NOT EDIT BELOW ###

# Test for excluded users.
for u in $EXCLUDE_USERS; do
	if [ "$USER" == "$u" ]; then
		return
	fi
done

# Create a function that evaluates the stdout of the modulecmd script.
module() {
	eval `${MODULEPYTHON} ${MODULEHOME}/modulecmd.py $*`;
}
export -f module

# Create a function that runs the moduledb script.
moduledb() {
	${MODULEPYTHON} ${MODULEHOME}/moduledb.py $*
}
export -f moduledb

# Setup auto-completion.

# Match all possible expansions of name/version in the database, where
# name has to start with the partial string, but version just needs to
# contain the partial string.
_module_avail_complete() {
	# Split the module 'name' into the name proper and the version string.
	local name=(${1/\// })
	if [ ${#name[@]} -gt 1 -o "$1" == "${name[0]}/" ]
	then
		echo "	SELECT name, version
			FROM moduleids
			WHERE name='${name[0]}' AND version LIKE '${name[1]}%';" | \
			sqlite3 -separator / ${MODULEPATH}/.db.sqlite
	else
		echo "	SELECT name, version
			FROM moduleids
			WHERE name LIKE '${name[0]}%';" | \
			sqlite3 -separator / ${MODULEPATH}/.db.sqlite
	fi
}

_module_complete() {
	local cur="$2" pos=$COMP_CWORD cmds="add avail clear display help list load purge rm show swap switch unload whatis"

	COMPREPLY=()

	if [ $pos -gt 1 ]; then
		# Complete multiple module names once a command has been chosen
		# (at position 1).
		case "${COMP_WORDS[1]}" in
		avail|load|add|switch|swap|show|display|help|whatis)
			COMPREPLY=( `_module_avail_complete "$cur"` )
			;;
		unload|rm|remove)
			COMPREPLY=( `IFS=: compgen -W "${LOADEDMODULES}" -- "$cur"` )
			;;
		esac
	else
		# Complete the module command at position 1.
		COMPREPLY=( `compgen -W "$cmds" -- "$cur"` )
	fi
}

complete -F _module_complete module

# Load default modules, first from the global defaults, then from the user's
# ~/.modules file.
if [ -r ${MODULEPATH}/.modules ]; then
	. ${MODULEPATH}/.modules
fi
if [ -r ${HOME}/.modules ]; then
	. ${HOME}/.modules
fi

