ufc
===

ULL Flow Control

Requisitos:

  * python (probado con 2.4)
  * python-sqlobject

Configuración rápida:

  * El script necesita una base de datos, si no tienes disponible lo más sencillo es utilizar SQLite.
  * Editamos la configuración para que se ajuste a la base de datos creada.
  * Ponemos el fichero de configuración en /etc/ufc.cfg.
  * El resto de configuración asume que el script estará en /opt/ccti/correo/ufc.py.
  * En el inicio del propio script también hay parámetros que se deberían adaptar (variables SMTPSERVER y RECIPIENTS).
  * Cambios a realizar en Postfix:

En master.cf añadimos lo siguiente:
---------------------------------8<--------------------------------
ufc       unix  -       n       n       -       0       spawn
  user=nobody argv=/opt/ccti/correo/ufc.py
---------------------------------8<--------------------------------

En main.cf editamos la opción smtpd_recipient_restrictions para que incluya "check_policy_service unix:private/ufc".
Ejemplo:
---------------------------------8<--------------------------------
smtpd_recipient_restrictions =
   check_policy_service unix:private/ufc
   reject_non_fqdn_recipient
   reject_unknown_recipient_domain
   permit_mynetworks
   reject_unauth_destination
---------------------------------8<--------------------------------

  * Por último, añadimos una tarea en cron para que limpie la base de datos periódicamente, ejemplo:
---------------------------------8<--------------------------------
# Eliminamos la base de datos del accounting de los correos enviados por los usuarios
15 * * * * /opt/ccti/correo/ufc.py -p >> /var/log/ufc.log 2>&1
---------------------------------8<--------------------------------

