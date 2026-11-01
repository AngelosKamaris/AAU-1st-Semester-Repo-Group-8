module ConnectScanDetect;

export {
    redef enum Notice::Type += { Connect_Scan };
    const connect_scan_threshold: count = 5 &redef;
    const connect_scan_window: interval = 60 sec &redef;
}

global connect_attempts: table[addr, addr] of set[port] &create_expire=connect_scan_window;
global connect_notice_count: table[addr, addr] of count &default=0;

event connection_state_remove(c: connection)
    {
    if ( c$conn$proto != tcp )
        return;

    local state = c$conn$conn_state;
    if ( state != "SF" && state != "RSTO" )
        return;
    if ( c$conn$orig_bytes > 10 || c$conn$resp_bytes > 10 )
        return;

    # Require the originator's ACK after the SYN/ACK (a real connect() handshake).
    # A SYN scan on an open port ends in an RST instead, so it is excluded here.
    if ( ! c$conn?$history )
        return;
    local h = c$conn$history;
    if ( |h| < 3 || h[0:3] != "ShA" )
        return;

    local scanner = c$id$orig_h;
    local target   = c$id$resp_h;
    local p        = c$id$resp_p;

    if ( [scanner, target] !in connect_attempts )
        connect_attempts[scanner, target] = set();
    add connect_attempts[scanner, target][p];

    if ( |connect_attempts[scanner, target]| >= connect_scan_threshold )
        {
        ++connect_notice_count[scanner, target];
        NOTICE([$note=Connect_Scan,
                $msg=fmt("Possible TCP connect scan: %s completed %d bare handshakes against %s. Notice #%d for this pair. Previous notices: %d.",
                         scanner, |connect_attempts[scanner, target]|, target,
                         connect_notice_count[scanner, target],
                         connect_notice_count[scanner, target] - 1),
                $src=scanner, $dst=target]);
        delete connect_attempts[scanner, target];
        }
    }