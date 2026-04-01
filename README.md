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

### 2. Start Mininet (OpenFlow 1.3)

```bash
sudo mn --topo single,3 --controller remote --switch ovs,protocols=OpenFlow13
```

### 3. Initialize Connectivity

```bash
mininet> h1 ping -c 3 h2
```

---

## 🔬 Test Scenarios

### 🔹 Scenario 1: Normal Behavior (Learning Switch)

Tests the controller's ability to handle `packet_in` events and install match-action rules for standard forwarding.

* **Action:**

  ```bash
  h1 ping h2
  ```
* **Observation:**
  Successful ICMP replies; flow rules installed in switch.

---

### 🔹 Scenario 2: Failure Detection (Port Down)

Tests the monitoring tool's ability to detect and log physical link failures.

* **Action:**

  ```bash
  link s1 h1 down
  ```
* **Observation:**
  Controller logs a **CRITICAL ALERT** identifying the specific port and switch ID.

---

### 🔹 Scenario 3: Recovery Detection (Port Up)

Tests the tool's ability to detect state restoration.

* **Action:**

  ```bash
  link s1 h1 up
  ```
* **Observation:**
  Controller logs an **INFO** message confirming the port is recovered.

---

## 📊 Monitoring Logic

* **Asynchronous Messages:**
  The controller listens for `OFPPortStatus` events from the switch.

* **Event Classification:**
  Logic identifies if a port was **Modified**, **Added**, or **Deleted**.

* **Flow Management:**
  Uses a **Table-Miss entry (Priority 0)** to redirect unknown packets to the controller for MAC learning.

---

## 📈 Observations & Metrics

* **Latency:** Average RTT of **1.492 ms** during normal operation
* **Throughput:** **26.9 Gbits/sec** bandwidth observed via iperf
* **Alert Accuracy:** Port status changes logged instantly upon link modification

---

## 🔍 Flow Table Verification

To view dynamically installed OpenFlow rules:

```bash
sudo ovs-ofctl dump-flows s1 -O OpenFlow13
```

---

## 📸 Proof of Execution

* Ryu Controller logs showing real-time UP/DOWN alerts
* Mininet outputs with successful ping and iperf results
* Flow table entries demonstrating MAC-based forwarding rules

---

## ⚠️ Notes

* Use the following command to clean Mininet before new sessions:

  ```bash
  sudo mn -c
  ```
* Ensure OpenFlow 1.3 is specified for advanced port status support

---

## ✅ Conclusion

The Port Status Monitoring Tool successfully demonstrates SDN’s capability to provide real-time network visibility and fault detection by leveraging asynchronous control plane messages.
