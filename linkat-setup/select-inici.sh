#!/bin/bash
#
# Script per seleccionar on s'inicia el Trivial Freezer
#

# Determinar quin inici es troba aplicat.
INICI=""
if [ -f /usr/share/lightdm/lightdm.conf.d/61-tfreezer.conf ] ; then
	INICI="Inici de sessió"
fi
egrep tfreezer /etc/rc.local > /dev/null 2>&1
if [ $? = 0 ] ; then
	INICI="Inici de sistema"
fi

# Informar de l'inici actual i preguntar que es vol fer.
zenity --question --title "Teniu aplicat $INICI" --text "Ara mateix teniu aplicat $INICI.\n\nVoleu modificar aquesta configuració?"
if [ ! $? = 0 ] ; then
	zenity --warning --text "Programa tancat per l'usuari"
	exit 1
fi

# Preguntar quin inici es vol configurar.
res=$(zenity --list --title "Inici del Trivial Freezer" --text "On vols iniciar el Trivial Freezer?" --radiolist  --column "Seleccionar" --column "opcions" FALSE "Inici de sistema" FALSE "Inici de sessió")

if [ "$res" = "Inici de sistema" ]; then
	/usr/share/tfreezer/inici-sistema.sh	
elif
	[ "$res" = "Inici de sessió" ]; then
	/usr/share/tfreezer/inici-sessio.sh
else
	zenity --warning --text "Programa tancat per l'usuari"
	exit 1
fi
