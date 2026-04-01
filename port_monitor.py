from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
import logging

class PortMonitor(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PortMonitor, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        # Set logging to INFO to ensure messages are captured [cite: 11]
        self.logger.setLevel(logging.INFO)

    # --- SECTION 1: Controller-Switch Interaction & Flow Design [cite: 4, 5] ---
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Install table-miss flow entry to send unknown packets to controller [cite: 10]
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    # --- SECTION 2: Port Status Monitoring Logic (The Core Task) [cite: 9, 10] ---
    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no
        dpid = msg.datapath.id

        # Detect Port Down/Up Events 
        if reason == msg.datapath.ofproto.OFPPR_MODIFY:
            link_state = msg.desc.state
            if link_state & msg.datapath.ofproto.OFPPS_LINK_DOWN:
                print(f"\n[!!!] CRITICAL ALERT: Port {port_no} on Switch {dpid} is DOWN [!!!]\n")
                self.logger.info("PORT_STATUS: Port %s on DPID %s is DOWN", port_no, dpid)
            else:
                print(f"\n[+] INFO: Port {port_no} on Switch {dpid} is UP/RECOVERED [+]\n")
                self.logger.info("PORT_STATUS: Port %s on DPID %s is UP", port_no, dpid)

    # --- SECTION 3: Functional Behavior (Learning Switch) [cite: 11] ---
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        
        self.mac_to_port.setdefault(dpid, {})

        # Log packet-in for documentation [cite: 10]
        # self.logger.info("Packet-in: Switch %s SRC:%s DST:%s Port:%s", dpid, src, dst, in_port)

        self.mac_to_port[dpid][src] = in_port
        out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)
        
        actions = [parser.OFPActionOutput(out_port)]

        # Install flow rule if destination is known [cite: 9]
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
