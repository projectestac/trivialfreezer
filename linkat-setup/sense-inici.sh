#!/bin/bash
#
# Script per eliminar el Trivial Freezer a l'inici de sistema i sessió
#

# Eliminant el Trivial Freezer de l'inici de sessió
if [ -f /usr/share/lightdm/lightdm.conf.d/61-tfreezer.conf ] ; then
	rm /usr/share/lightdm/lightdm.conf.d/61-tfreezer.conf
fi

# Eliminant Trivial Freezer de l'inici del sistema
egrep tfreezer /etc/rc.local
if [ $? -eq 0 ]; then
	sed -i '/tfreezer/d' /etc/rc.local
	chmod +x /etc/rc.local
fi

zenity --info --title "Trivial Freezer - Sense inici" --text "El Trivial Freezer no s'iniciarà automàticament."
