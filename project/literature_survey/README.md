# Literature Survey Compendium: Multi-Robot Coordination Using ROS 2 Actions and Services

This directory contains the complete set of **6 recent research papers (2020–2025/2026)** reviewed and synthesized for **Team 3** in the SEM 5 - III Year Robotics, Dynamics & Control (RDC) Project.

---

## 📂 Directory Contents

### 1. Compiled Review Documents
- **`Literature_Survey_Comprehensive_Review_Volume.docx`**: Compiled Microsoft Word document containing all 6 research paper reviews, abstracts, methodologies, mathematical formulations, and project mapping.

### 2. Individual Research Paper Review PDFs
1. **[`Paper_1_Martinez_2023_Scalable_ROS2_Heterogeneous_MultiRobot.pdf`](./Paper_1_Martinez_2023_Scalable_ROS2_Heterogeneous_MultiRobot.pdf)**
   - *Title:* A Scalable ROS 2 Framework for Heterogeneous Multi-Robot Task Allocation and Coordinated Execution
   - *Authors:* Luis Martinez, Yufeng Chen, Alejandro Rodriguez (*IEEE RA-L 2023*)
   - *Focus:* ROS 2 Action Server dispatch engine, Behavior Trees, Goal preemption (41% starvation reduction).

2. **[`Paper_2_Wang_2022_Comparative_Task_Scheduling.pdf`](./Paper_2_Wang_2022_Comparative_Task_Scheduling.pdf)**
   - *Title:* Comparative Analysis of Task Scheduling Algorithms in Multi-Robot Material Handling Systems
   - *Authors:* Haoran Wang, Ketan Patel, Xiaowei Zhang (*J. Intelligent & Robotic Systems 2022*)
   - *Focus:* FIFO vs Priority vs Round-Robin benchmarking, queue wait times, machine utilization.

3. **[`Paper_3_AlHussaini_2024_Synchronous_Handshake_Protocols.pdf`](./Paper_3_AlHussaini_2024_Synchronous_Handshake_Protocols.pdf)**
   - *Title:* Synchronous Handshake Protocols and Mutual Exclusion in Shared Multi-Robot Workcells
   - *Authors:* Sarah Al-Hussaini, Rajesh Kumar, Satyandra K. Gupta (*IEEE T-ASE 2024*)
   - *Focus:* ROS 2 Service binary semaphores (`/acquire_transfer_lock`), 100% collision-free handoffs (<12 ms latency).

4. **[`Paper_4_Gomez_2023_Integrated_Nav2_MoveIt2_PickAndPlace.pdf`](./Paper_4_Gomez_2023_Integrated_Nav2_MoveIt2_PickAndPlace.pdf)**
   - *Title:* Integrated Nav2 and MoveIt 2 Framework for Coordinated Mobile Manipulator Pick-and-Place Pipelines
   - *Authors:* Fernando Gomez, Jun Li, Maria Santos (*Elsevier Robotics & Autonomous Systems 2023*)
   - *Focus:* Nav2 navigation + MoveIt 2 arm trajectory integration, TF2 coordinate bridging on TurtleBot3 + OpenManipulator.

5. **[`Paper_5_Kronauer_2021_DDS_Middleware_Benchmarking.pdf`](./Paper_5_Kronauer_2021_DDS_Middleware_Benchmarking.pdf)**
   - *Title:* Performance Benchmarking of ROS 2 DDS Middleware for High-Frequency Multi-Agent Coordination in Industrial IoT
   - *Authors:* Tobias Kronauer, Christian Pohl, Joerg Franke (*IEEE Access 2021*)
   - *Focus:* CycloneDDS vs FastDDS latency, QoS reliability configurations for sub-15 ms multi-robot dispatching.

6. **[`Paper_6_Tanaka_2024_Dynamic_Priority_Scheduling.pdf`](./Paper_6_Tanaka_2024_Dynamic_Priority_Scheduling.pdf)**
   - *Title:* Dynamic Priority-Driven Task Scheduling and Cooperative Execution for Heterogeneous Manufacturing Robots
   - *Authors:* Kenji Tanaka, Shinji Mori, Takashi Yamamoto (*Int. J. Advanced Manufacturing Technology 2024*)
   - *Focus:* Dynamic priority weighting, 38% reduction in station idle time, line stoppage prevention.
