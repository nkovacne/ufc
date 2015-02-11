ufc
===

ULL Flow Control

Requisitos:

  * python
  * SQLAlchemy
  * python-twisted

Configuración rápida:

  * El script necesita una base de datos, si no tienes disponible lo más sencillo es utilizar SQLite. El script se encarga de crear la base de datos si no existe.
  * Ponemos el fichero de configuración en /etc/ufc.cfg.
  * Editamos la configuración para que se ajuste a la base de datos creada.
  * El resto de configuración asume que el script estará en /opt/ccti/correo/ufc.py.
  * En el inicio del propio script también hay parámetros que se deberían adaptar (variables SMTPSERVER y RECIPIENTS).
  * Cambios a realizar en Postfix:

En master.cf añadimos lo siguiente:
```
ufc       unix  -       n       n       -       0       spawn
  user=nobody argv=/opt/ccti/correo/ufc.py
```

En main.cf editamos la opción smtpd_recipient_restrictions para que incluya "check_policy_service unix:private/ufc". Ejemplo:
```
smtpd_recipient_restrictions =
   check_policy_service unix:private/ufc
   reject_non_fqdn_recipient
   reject_unknown_recipient_domain
   permit_mynetworks
   reject_unauth_destination
```
Por último, añadimos una tarea en cron para que limpie la base de datos periódicamente, ejemplo:
```
# Eliminamos la base de datos del accounting de los correos enviados por los usuarios
15 * * * * /opt/ccti/correo/ufc.py -p >> /var/log/ufc.log 2>&1
```
