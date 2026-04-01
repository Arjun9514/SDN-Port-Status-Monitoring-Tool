# SDN Port Status Monitoring Tool

## 📌 Objective

To implement an SDN-based solution using Mininet and a Ryu controller that monitors and logs real-time switch port status changes (Up/Down events) and maintains network connectivity through dynamic flow rule insertion.

---

## ⚙️ Requirements

* Ubuntu (20.04/22.04)
* Mininet
* Ryu Controller
* Python 3

---

## 🏗️ Topology

Single switch topology with 3 hosts:

* **h1** (Host 1 - Monitoring Target)  
* **h2** (Host 2 - Traffic Partner)  
* **h3** (Host 3 - Traffic Partner)

---

## 🚀 How to Run

### 1. Start Ryu Controller

```bash
ryu-manager port_monitor.py
```

### ✅ Expected Output

```
loading app port_monitor.py
instantiating app PortMonitor
PORT UP: Switch 1, Port 1
PORT UP: Switch 1, Port 2
PORT UP: Switch 1, Port 3
```

---

### 2. Start Mininet (OpenFlow 1.3)

```bash
sudo mn --topo single,3 --controller remote --switch ovs,protocols=OpenFlow13
```

### ✅ Expected Output

```
*** Creating network
*** Adding controller
*** Adding hosts:
h1 h2 h3
*** Adding switches:
s1
*** Starting network
*** Starting CLI:
mininet>
```

---

### 3. Initialize Connectivity

```bash
mininet> h1 ping -c 3 h2
```

### ✅ Expected Output

```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.2 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=1.4 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=1.3 ms

--- 10.0.0.2 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss
```

---

## 🔬 Test Scenarios

### 🔹 Scenario 1: Normal Behavior (Learning Switch)

#### Action

```bash
h1 ping h2
```

#### Expected Output (Mininet)

```
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.3 ms
...
```

#### Expected Output (Ryu Logs)

```
Packet received: learning MAC addresses
Flow added: in_port=1, eth_dst=...
```

---

### 🔹 Scenario 2: Failure Detection (Port Down)

#### Action

```bash
link s1 h1 down
```

#### Expected Output (Mininet)

```
*** Link s1-h1 down
```

#### Expected Output (Ryu Controller)

```
[!!!] CRITICAL: Port 1 on Switch 1 is DOWN
PORT DOWN: Switch 1, Port 1
```

#### Expected Behavior

```
Destination Host Unreachable
```

---

### 🔹 Scenario 3: Recovery Detection (Port Up)

#### Action

```bash
link s1 h1 up
```

#### Expected Output (Mininet)

```
*** Link s1-h1 up
```

#### Expected Output (Ryu Controller)

```
[+] INFO: Port 1 on Switch 1 is UP
PORT UP: Switch 1, Port 1
```

#### Expected Behavior

```bash
h1 ping h2
```

```
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.2 ms
```

---

## 📊 Monitoring Logic

* Controller listens for `OFPPortStatus` events  
* Detects MODIFY, ADD, DELETE events  
* Uses Table-Miss flow (priority 0)  
* Installs dynamic flows (priority 1)  

---

## 📈 Observations & Metrics

* Latency: ~1.492 ms  
* Throughput: ~26.9 Gbits/sec  
* Instant alert detection  

---

## 🔍 Flow Table Verification

```bash
sudo ovs-ofctl dump-flows s1 -O OpenFlow13
```

### Expected Output

```
priority=0 actions=CONTROLLER
priority=1,in_port=1,dl_dst=xx:xx:xx:xx:xx:xx actions=output:2
priority=1,in_port=2,dl_dst=xx:xx:xx:xx:xx:xx actions=output:1
```

---

## 📸 Proof of Execution

* Ryu logs with port alerts  
* Mininet ping results  
* Flow table entries  

---

## ⚠️ Notes

```bash
sudo mn -c
```

* Always use OpenFlow 1.3

---

## ✅ Conclusion

This tool demonstrates:

* Real-time port monitoring  
* Fast failure detection  
* Dynamic SDN-based traffic handling  
