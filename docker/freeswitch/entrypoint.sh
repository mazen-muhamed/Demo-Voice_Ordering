#!/bin/sh
# Render the ESL password into the config at start-up, then run FreeSWITCH in
# the foreground (Docker's PID 1).
#
# Keep FS_ESL_PASSWORD to a simple value (letters/digits) because it is
# substituted with sed.  The default is ClueCon.
set -eu

: "${FS_ESL_PASSWORD:=ClueCon}"

CONF_DIR=/usr/local/freeswitch/conf

# Optional: pin the advertised SIP/RTP IP when the host has several
# interfaces.  Default is FreeSWITCH's local_ip_v4 (the default-route IP).
if [ -n "${FS_LOCAL_IP:-}" ]; then
    for file in vars.xml sip_profiles/internal.xml; do
        sed -i "s|\$\${local_ip_v4}|${FS_LOCAL_IP}|g" "$CONF_DIR/$file"
    done
fi

CONF=$CONF_DIR/autoload_configs/event_socket.conf.xml
if [ -f "$CONF" ]; then
    sed -i "s|__ESL_PASSWORD__|${FS_ESL_PASSWORD}|g" "$CONF"
fi

# FreeSWITCH's compiled-in default config dir is ${prefix}/etc/freeswitch,
# not ${prefix}/conf.  Point every runtime dir at the paths baked into the
# image so the trimmed config (and mod_audio_stream) is the one that loads.
exec freeswitch -nf -nonat \
    -conf /usr/local/freeswitch/conf \
    -log /usr/local/freeswitch/log \
    -run /usr/local/freeswitch/run \
    -db /usr/local/freeswitch/db \
    -temp /tmp \
    -recordings /usr/local/freeswitch/recordings
