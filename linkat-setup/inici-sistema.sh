#!/bin/bash
#
# Script per afegir el Trivial Freezer a l'inici del sistema
#

# Eliminant el Trivial Freezer de l'inici de sessió
if [ -f /usr/share/lightdm/lightdm.conf.d/61-tfreezer.conf ] ; then
	rm /usr/share/lightdm/lightdm.conf.d/61-tfreezer.conf
fi

# Afegint el Trivial Freezer a l'inici del sistema
egrep tfreezer /etc/rc.local > /dev/null 2>&1
if [ $? -gt 0 ] ; then
        mv /etc/rc.local /etc/rc.local.tf.bak
        sed 's/^exit 0/#tfreezer \ndate >> \/var\/log\/tfreezer.log \n\/usr\/bin\/tfreezer -r -a >> \/var\/log\/tfreezer.log \n\nexit 0/g' /etc/rc.local.tf.bak > /etc/rc.local
	chmod +x /etc/rc.local
fi
