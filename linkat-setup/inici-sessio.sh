#!/bin/bash
#
# Script per iniciar Trivial Freezer a l'inici de sessió
#

# Eliminant Trivial Freezer de l'inici del sistema
egrep tfreezer /etc/rc.local
if [ $? -eq 0 ]; then
	sed -i '/tfreezer/d' /etc/rc.local
	chmod +x /etc/rc.local
fi

# Afegint el Trivial Freezer a l'inici de sessió
cp -av /usr/share/tfreezer/61-tfreezer.conf /usr/share/lightdm/lightdm.conf.d/

