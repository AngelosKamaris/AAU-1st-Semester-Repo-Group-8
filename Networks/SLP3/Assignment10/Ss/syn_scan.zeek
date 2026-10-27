module SynScanDetect;

export {
    redef enum Notice::Type += { SYN_Scan };
    const syn_scan_threshold: count = 500 &redef;
    const syn_scan_window: interval = 60 sec &redef;
}

global syn_attempts: table[addr, addr] of set[port] &create_expire=syn_scan_window;
global syn_notice_count: table[addr, addr] of count &default=0;

event connection_state_remove(c: connection)
    {
    if ( c$conn$proto != tcp )
        return;

    local state = c$conn$conn_state;
    if ( state != "S0" && state != "REJ" &&
         state != "RSTOS0" && state != "RSTRH" )
        return;

    local scanner = c$id$orig_h;
    local target   = c$id$resp_h;
    local p        = c$id$resp_p;

    if ( [scanner, target] !in syn_attempts )
        syn_attempts[scanner, target] = set();
    add syn_attempts[scanner, target][p];

    if ( |syn_attempts[scanner, target]| >= syn_scan_threshold )
        {
        ++syn_notice_count[scanner, target];
        NOTICE([$note=SYN_Scan,
                $msg=fmt("Possible SYN scan: %s probed %d distinct ports on %s without completing the handshake. Notice #%d for this pair.",
                         scanner, |syn_attempts[scanner, target]|, target,
                         syn_notice_count[scanner, target]),
                $src=scanner, $dst=target]);
        delete syn_attempts[scanner, target];
        }
    }