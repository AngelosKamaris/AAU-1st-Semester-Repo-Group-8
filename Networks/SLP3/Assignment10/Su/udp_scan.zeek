module UdpScanDetect;

export {
    redef enum Notice::Type += { UDP_Scan };
    const udp_scan_threshold: count = 50 &redef;
    const udp_scan_window: interval = 600 sec &redef;
}

global udp_attempts: table[addr, addr] of set[port] &create_expire=udp_scan_window;
global udp_notice_count: table[addr, addr] of count &default=0;

event connection_state_remove(c: connection)
    {
    if ( c$conn$proto != udp )
        return;
    if ( c$conn$conn_state != "S0" )
        return;

    local scanner = c$id$orig_h;
    local target   = c$id$resp_h;
    local p        = c$id$resp_p;

    if ( [scanner, target] !in udp_attempts )
        udp_attempts[scanner, target] = set();
    add udp_attempts[scanner, target][p];

    if ( |udp_attempts[scanner, target]| >= udp_scan_threshold )
        {
        ++udp_notice_count[scanner, target];
        NOTICE([$note=UDP_Scan,
                $msg=fmt("Possible UDP scan: %s probed %d distinct UDP ports on %s with no replies. Notice #%d for this pair.",
                         scanner, |udp_attempts[scanner, target]|, target,
                         udp_notice_count[scanner, target]),
                $src=scanner, $dst=target]);
        delete udp_attempts[scanner, target];
        }
    }