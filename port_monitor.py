from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
import logging


class PortMonitor(app_manager.RyuApp):
    """
    A Ryu SDN application that:
    1. Installs a table-miss flow entry
    2. Acts as a learning switch
    3. Monitors port status (UP/DOWN events)
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PortMonitor, self).__init__(*args, **kwargs)

        # MAC address table: {dpid: {mac: port}}
        self.mac_to_port = {}

        # Configure logging level
        self.logger.setLevel(logging.INFO)

    # ---------------------------------------------------------------------
    # SECTION 1: Switch Connection & Flow Setup
    # ---------------------------------------------------------------------
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Triggered when a switch connects to the controller.
        Installs a default (table-miss) flow entry.
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Match all packets (table-miss)
        match = parser.OFPMatch()

        # Send unmatched packets to controller
        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(datapath, priority=0, match=match, actions=actions)

    def add_flow(self, datapath, priority, match, actions):
        """
        Helper function to install a flow rule on the switch.
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions
            )
        ]

        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions
        )

        datapath.send_msg(flow_mod)

    # ---------------------------------------------------------------------
    # SECTION 2: Port Status Monitoring
    # ---------------------------------------------------------------------
    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        """
        Handles port status changes (e.g., link up/down).
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        reason = msg.reason
        port_no = msg.desc.port_no
        dpid = datapath.id

        # We only care about port modifications
        if reason == ofproto.OFPPR_MODIFY:
            link_state = msg.desc.state

            if link_state & ofproto.OFPPS_LINK_DOWN:
                print(f"\n[!!!] CRITICAL: Port {port_no} on Switch {dpid} is DOWN\n")
                self.logger.info(
                    "PORT DOWN: Switch %s, Port %s", dpid, port_no
                )
            else:
                print(f"\n[+] INFO: Port {port_no} on Switch {dpid} is UP\n")
                self.logger.info(
                    "PORT UP: Switch %s, Port %s", dpid, port_no
                )

    # ---------------------------------------------------------------------
    # SECTION 3: Learning Switch Logic
    # ---------------------------------------------------------------------
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handles incoming packets and implements learning switch behavior.
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']
        dpid = datapath.id

        # Parse Ethernet packet
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocols(ethernet.ethernet)[0]

        src = eth_pkt.src
        dst = eth_pkt.dst

        # Initialize MAC table for this switch
        self.mac_to_port.setdefault(dpid, {})

        # Learn source MAC -> port mapping
        self.mac_to_port[dpid][src] = in_port

        # Determine output port
        out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow rule if destination is known
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, priority=1, match=match, actions=actions)

        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        packet_out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(packet_out)
