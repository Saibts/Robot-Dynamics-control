"""
Generate a professional, publication-grade PDF report containing:
1. Multi-Robot Coordination System Overview & Architecture
2. The Detailed 4-Component Analysis Chart
3. Handshake State Machine & Protocol Flow
4. Task Scheduling Benchmark Performance Metrics (FIFO vs Priority vs Round Robin)
5. Current Project Implementation & Readiness Status Dashboard
"""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1A365D"))

        # Running Header (on all pages)
        self.drawString(45, 755, "RDC PROJECT | TEAM 3 — MULTI-ROBOT COORDINATION (ROS 2 JAZZY)")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawRightString(612 - 45, 755, "SYSTEM ANALYSIS & COMPONENT BENCHMARK")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.75)
        self.line(45, 747, 612 - 45, 747)

        # Running Footer (on all pages)
        self.line(45, 42, 612 - 45, 42)
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#4A5568"))
        self.drawString(45, 30, "DEPARTMENT OF ROBOTICS ENGINEERING — CONFIDENTIAL ACADEMIC REPORT")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 45, 30, page_str)
        self.restoreState()


def build_analysis_pdf(output_path="Multi_Robot_Coordination_Component_Analysis_Chart.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=52,
        bottomMargin=52
    )

    # Color Palette
    c_navy = colors.HexColor("#1A365D")
    c_slate = colors.HexColor("#2B6CB0")
    c_dark = colors.HexColor("#2D3748")
    c_gray = colors.HexColor("#718096")
    c_border = colors.HexColor("#CBD5E0")
    c_row_alt = colors.HexColor("#F7FAFC")

    # Typography Styles
    p_title = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=17, leading=21, textColor=c_navy, alignment=0, spaceAfter=3)
    p_sub = ParagraphStyle('DocSub', fontName='Helvetica', fontSize=9, leading=12, textColor=c_slate, alignment=0, spaceAfter=8)
    p_h1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=c_navy, spaceBefore=8, spaceAfter=4, keepWithNext=True)
    p_body = ParagraphStyle('Body', fontName='Helvetica', fontSize=8, leading=11, textColor=c_dark, spaceAfter=4)

    # Table Styles
    th_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=1)
    td_style = ParagraphStyle('TD', fontName='Helvetica', fontSize=7, leading=9.5, textColor=c_dark)
    td_bold = ParagraphStyle('TDBold', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=c_navy)
    td_center = ParagraphStyle('TDCenter', fontName='Helvetica', fontSize=7, leading=9.5, textColor=c_dark, alignment=1)
    td_center_bold = ParagraphStyle('TDCenterBold', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=c_navy, alignment=1)

    story = []

    # ========================================================
    # PAGE 1: HEADER BANNER & SYSTEM ARCHITECTURE
    # ========================================================
    story.append(Paragraph("<b>DEPARTMENT OF ROBOTICS ENGINEERING | B.TECH CURRICULUM</b>", ParagraphStyle('Dept', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_slate)))
    story.append(Paragraph("COURSE: ROBOTICS, DYNAMICS & CONTROL (RDC) — SEMESTER 5", ParagraphStyle('SubD', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=c_gray, spaceAfter=5)))
    story.append(Paragraph("SYSTEM ARCHITECTURE & 4-COMPONENT DETAILED ANALYSIS CHART", p_title))
    story.append(Paragraph("Heterogeneous Multi-Robot Coordination (UR5 + TurtleBot3 OpenManipulator) Using ROS 2 Actions and Services in ROS 2 Jazzy", p_sub))

    # Meta Table
    meta_info = [
        [
            Paragraph("<b>Project Team:</b> Team 3", p_body),
            Paragraph("<b>Team Members:</b> Sailakshmi (2024511019) & Navin (2024511029)", p_body),
        ],
        [
            Paragraph("<b>Assigned Task:</b> Task 3 — Multi-Robot Task Scheduling in ROS 2", p_body),
            Paragraph("<b>Platform:</b> Ubuntu 24.04 LTS | ROS 2 Jazzy Jalisco | RViz2", p_body),
        ]
    ]
    meta_table = Table(meta_info, colWidths=[240, 282])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("1. System Purpose & Operational Workflow", p_h1))
    story.append(Paragraph(
        "Modern autonomous manufacturing cells combine <b>Mobile Robots (AMR/AGV)</b> for dynamic raw-material transport and <b>Fixed Industrial Arms (UR5)</b> for high-precision assembly. "
        "The primary challenge is preventing physical collisions in the shared handoff zone while maximizing throughput. "
        "This project establishes an asynchronous coordination framework using <b>ROS 2 Actions</b> (for long-duration tasks with preemption and progress tracking), "
        "<b>ROS 2 Services</b> (for atomic mutual exclusion zone locking and gripper toggling), and a <b>Multi-Criteria Scheduling Engine</b> (evaluating FIFO, Priority-Based, and Round-Robin policies).",
        p_body
    ))

    # Embed Architecture Image
    arch_img_path = "/home/sailakshmi/Desktop/RDC_project/project/figures/multi_robot_architecture_diagram.png"
    if os.path.exists(arch_img_path):
        story.append(Spacer(1, 4))
        story.append(Image(arch_img_path, width=522, height=205))
        story.append(Paragraph("<i>Figure 1: Heterogeneous Multi-Robot Coordination Architecture showing Action Servers, Safety Mutex Service, and Central Coordinator.</i>", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=7.5, leading=9, textColor=c_gray, alignment=1, spaceBefore=4)))

    story.append(PageBreak())

    # ========================================================
    # PAGE 2: THE DETAILED 4-COMPONENT ANALYSIS CHART
    # ========================================================
    story.append(Paragraph("2. Detailed 4-Component Technical Analysis Chart", p_h1))
    story.append(Paragraph(
        "The system architecture is strictly partitioned into four modular, decoupled components. "
        "The table below details their technical primitives, operational rationale, state behavior, and input/output interfaces:",
        p_body
    ))

    # 4 Components Table Data
    comp_headers = [
        Paragraph("<b>#</b>", th_style),
        Paragraph("<b>Component</b>", th_style),
        Paragraph("<b>Technical Primitives</b>", th_style),
        Paragraph("<b>Implementation Purpose & Logic</b>", th_style),
        Paragraph("<b>Input / Output Specifications & Metrics</b>", th_style)
    ]

    row_1 = [
        Paragraph("<b>1</b>", td_center_bold),
        Paragraph("<b>Long-Horizon Robot Actions</b><br/><font color='#718096' size='6.5'>Mobile & Fixed Actuation</font>", td_bold),
        Paragraph(
            "• <font color='#C53030'><b>NavigateAndPick.action</b></font><br/>"
            "• <font color='#C53030'><b>UR5PickAndPlace.action</b></font><br/>"
            "<font color='#2B6CB0'>ROS 2 Action Servers & Clients (rclpy.action)</font>",
            td_style
        ),
        Paragraph(
            "• <b>Decouples physical motion</b> from blocking node execution.<br/>"
            "• <b>Publishes continuous feedback</b> at 10 Hz (0–100% progress and operational phase).<br/>"
            "• <b>Asynchronous preemption:</b> Enables immediate goal cancellation during safety aborts.<br/>"
            "• Simulates Nav2 waypoint navigation + 4-DOF OpenManipulator grasping, followed by UR5 6-DOF MoveIt 2 trajectory planning.",
            td_style
        ),
        Paragraph(
            "<b>TB3 Inputs:</b><br/>"
            "• <code>target_station_id</code> (string)<br/>"
            "• <code>pickup_coordinates</code> (float32[3])<br/>"
            "• <code>priority_level</code> (int32)<br/>"
            "<b>TB3 Outputs:</b><br/>"
            "• <code>success</code> (bool), <code>nav_time</code> (s)<br/>"
            "<b>UR5 Inputs:</b><br/>"
            "• <code>task_id</code>, <code>pickup_pose</code>, <code>assembly_pose</code><br/>"
            "<b>UR5 Outputs:</b><br/>"
            "• <code>completion_code</code>, <code>exec_time</code> (s)",
            td_style
        )
    ]

    row_2 = [
        Paragraph("<b>2</b>", td_center_bold),
        Paragraph("<b>Safety Mutex & Tool Services</b><br/><font color='#718096' size='6.5'>Atomic Zone Guardian</font>", td_bold),
        Paragraph(
            "• <font color='#C53030'><b>AcquireHandoffLock.srv</b></font><br/>"
            "• <font color='#C53030'><b>TriggerGripper.srv</b></font><br/>"
            "<font color='#2B6CB0'>ROS 2 Synchronous Services (rclpy.node.Service)</font>",
            td_style
        ),
        Paragraph(
            "• <b>Mutual Exclusion (Mutex):</b> Strictly protects the physical transfer station envelope.<br/>"
            "• <b>Zero-Collision Guarantee:</b> Prevents the mobile robot and UR5 arm from entering the overlapping workspace simultaneously.<br/>"
            "• <b>Atomic State Confirmation:</b> Provides instantaneous, blocking Boolean lock grant/rejection with timestamped logging.<br/>"
            "• Actuates Robotiq pneumatic parallel gripper grasping.",
            td_style
        ),
        Paragraph(
            "<b>Lock Request:</b><br/>"
            "• <code>robot_id</code> (string)<br/>"
            "• <code>zone_id</code> (int32)<br/>"
            "• <code>request_lock</code> (bool: True=Lock, False=Release)<br/>"
            "<b>Lock Response:</b><br/>"
            "• <code>lock_granted</code> (bool)<br/>"
            "• <code>message</code> (status string)<br/>"
            "• <code>timestamp</code> (int64 epoch)<br/>"
            "<b>Gripper:</b> <code>close_gripper</code>, <code>grasp_effort</code>",
            td_style
        )
    ]

    row_3 = [
        Paragraph("<b>3</b>", td_center_bold),
        Paragraph("<b>Central Coordinator & State Machine</b><br/><font color='#718096' size='6.5'>Workflow Orchestration</font>", td_bold),
        Paragraph(
            "• <font color='#C53030'><b>multi_robot_coordinator.py</b></font><br/>"
            "<font color='#2B6CB0'>Multi-Threaded ROS 2 Node & Execution Engine</font>",
            td_style
        ),
        Paragraph(
            "• <b>Automates Complete Transfer Cycle:</b><br/>"
            "  1. Dispatches TB3 Action Goal from Scheduler.<br/>"
            "  2. Monitors docking via 10 Hz action feedback.<br/>"
            "  3. Calls <code>AcquireHandoffLock.srv</code> to lock zone.<br/>"
            "  4. Dispatches UR5 Action Goal for assembly.<br/>"
            "  5. Releases lock and marks task complete.<br/>"
            "• <b>Preemption & Fault Recovery:</b> Re-queues tasks upon communication dropouts or safety interrupts.",
            td_style
        ),
        Paragraph(
            "<b>Internal State Machine:</b><br/>"
            "• <code>IDLE</code><br/>"
            "• <code>DISPATCHING_TB3</code><br/>"
            "• <code>NAVIGATING_TO_PICKUP</code><br/>"
            "• <code>REQUESTING_ZONE_LOCK</code><br/>"
            "• <code>ZONE_LOCKED_ACTIVE</code><br/>"
            "• <code>UR5_ASSEMBLING</code><br/>"
            "• <code>LOCK_RELEASED</code><br/>"
            "• <code>TASK_COMPLETED</code>",
            td_style
        )
    ]

    row_4 = [
        Paragraph("<b>4</b>", td_center_bold),
        Paragraph("<b>Task Scheduling Engine & Benchmark</b><br/><font color='#718096' size='6.5'>Performance Analytics</font>", td_bold),
        Paragraph(
            "• <font color='#C53030'><b>scheduler.py</b></font><br/>"
            "• <font color='#C53030'><b>simulation_runner.py</b></font><br/>"
            "<font color='#2B6CB0'>Algorithmic Queuing & Discrete Event Simulation</font>",
            td_style
        ),
        Paragraph(
            "• <b>Three Scheduling Implementations:</b><br/>"
            "  - <b>FIFO:</b> First-in, first-out double-ended queue.<br/>"
            "  - <b>Priority-Based:</b> Min-heap keyed by priority weights (1=Urgent to 5=Low).<br/>"
            "  - <b>Round-Robin:</b> Cyclic job-class fair allocation.<br/>"
            "• Evaluates dynamic task arrival over 30 stochastic industrial workloads.",
            td_style
        ),
        Paragraph(
            "<b>Key Comparative Metrics:</b><br/>"
            "• <b>Average Waiting Time (s):</b> Latency before pickup.<br/>"
            "• <b>Robot Utilization (%):</b> Active work vs idle ratio for TB3 & UR5.<br/>"
            "• <b>System Throughput:</b> Completed jobs per hour.<br/>"
            "• <b>Total Makespan (s):</b> Overall batch completion time.",
            td_style
        )
    ]

    comp_table = Table(
        [comp_headers, row_1, row_2, row_3, row_4],
        colWidths=[20, 95, 115, 155, 137]
    )
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('BACKGROUND', (0, 2), (-1, 2), c_row_alt),
        ('BACKGROUND', (0, 3), (-1, 3), colors.white),
        ('BACKGROUND', (0, 4), (-1, 4), c_row_alt),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(comp_table)

    story.append(PageBreak())

    # ========================================================
    # PAGE 3: FSM FLOWCHART + BENCHMARKS + STATUS DASHBOARD
    # ========================================================
    fsm_img_path = "/home/sailakshmi/Desktop/RDC_project/project/figures/state_machine_flowchart.png"
    if os.path.exists(fsm_img_path):
        story.append(Image(fsm_img_path, width=522, height=115))
        story.append(Paragraph("<i>Figure 2: Handshake Protocol & State Machine Transition Sequence across Coordinator, Mobile Robot, and UR5 Arm.</i>", ParagraphStyle('Cap2', fontName='Helvetica-Oblique', fontSize=7, leading=8.5, textColor=c_gray, alignment=1, spaceBefore=2, spaceAfter=6)))

    story.append(Paragraph("3. Quantitative Scheduling Benchmark Evaluation", p_h1))
    story.append(Paragraph(
        "A rigorous discrete-event simulation of 30 heterogeneous industrial jobs was executed across all three scheduling algorithms using "
        "<code>simulation_runner.py</code>. The empirical results fulfill the academic requirements of Task 3:",
        p_body
    ))

    metric_headers = [
        Paragraph("<b>Scheduling Algorithm</b>", th_style),
        Paragraph("<b>Total Makespan (s)</b>", th_style),
        Paragraph("<b>Avg Waiting Time (s)</b>", th_style),
        Paragraph("<b>UR5 Utilization (%)</b>", th_style),
        Paragraph("<b>TB3 Utilization (%)</b>", th_style),
        Paragraph("<b>Throughput (Tasks/Hr)</b>", th_style),
    ]

    metric_r1 = [
        Paragraph("<b>FIFO (First-In First-Out)</b>", td_bold),
        Paragraph("532.67 s", td_center),
        Paragraph("175.50 s", td_center),
        Paragraph("70.23 %", td_center),
        Paragraph("96.84 %", td_center),
        Paragraph("202.75", td_center),
    ]

    metric_r2 = [
        Paragraph("<b>Priority-Based (Heap)</b>", td_bold),
        Paragraph("536.84 s", td_center),
        Paragraph("<font color='#22543D'><b>167.80 s</b></font> <font color='#276749' size='6'>(-4.4% faster)</font>", td_center),
        Paragraph("69.69 %", td_center),
        Paragraph("96.08 %", td_center),
        Paragraph("201.18", td_center),
    ]

    metric_r3 = [
        Paragraph("<b>Round-Robin (Fair Share)</b>", td_bold),
        Paragraph("532.67 s", td_center),
        Paragraph("175.50 s", td_center),
        Paragraph("70.23 %", td_center),
        Paragraph("96.84 %", td_center),
        Paragraph("202.75", td_center),
    ]

    metric_table = Table([metric_headers, metric_r1, metric_r2, metric_r3], colWidths=[122, 80, 90, 80, 80, 70])
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#F0FFF4")),
        ('BACKGROUND', (0, 3), (-1, 3), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(metric_table)
    story.append(Spacer(1, 6))

    # Embed Scheduling Metrics Chart
    sched_img_path = "/home/sailakshmi/Desktop/RDC_project/project/figures/scheduling_performance_metrics.png"
    if os.path.exists(sched_img_path):
        story.append(Image(sched_img_path, width=522, height=115))
        story.append(Paragraph("<i>Figure 3: Comparative Benchmarking of FIFO, Priority-Based, and Round-Robin Scheduling across Waiting Time, Resource Utilization, and Throughput.</i>", ParagraphStyle('Cap3', fontName='Helvetica-Oblique', fontSize=7, leading=8.5, textColor=c_gray, alignment=1, spaceBefore=2, spaceAfter=6)))

    story.append(Paragraph("4. Current Project Implementation & Readiness Status", p_h1))

    status_headers = [
        Paragraph("<b>Subsystem / Deliverable</b>", th_style),
        Paragraph("<b>Target Scope</b>", th_style),
        Paragraph("<b>Current Status</b>", th_style),
        Paragraph("<b>Implementation Details & Location</b>", th_style)
    ]

    stat_r1 = [
        Paragraph("<b>Task Scheduling Algorithms</b>", td_bold),
        Paragraph("FIFO, Priority, Round Robin", td_style),
        Paragraph("<font color='#22543D'><b>100% Complete</b></font>", td_center),
        Paragraph("Verified via <code>simulation_runner.py</code>; full metrics recorded.", td_style)
    ]
    stat_r2 = [
        Paragraph("<b>Comprehensive Reports & Guides</b>", td_bold),
        Paragraph("Step-by-Step Guide & Master Report", td_style),
        Paragraph("<font color='#22543D'><b>100% Complete</b></font>", td_center),
        Paragraph("4 full PDF + Word documentation manuals generated in project root.", td_style)
    ]
    stat_r3 = [
        Paragraph("<b>Literature Survey Portfolio</b>", td_bold),
        Paragraph("6 Indexed Papers + Review Volume", td_style),
        Paragraph("<font color='#22543D'><b>100% Complete</b></font>", td_center),
        Paragraph("Stored in <code>literature_survey/</code> with citations and comparative tables.", td_style)
    ]
    stat_r4 = [
        Paragraph("<b>ROS 2 Node Logic</b>", td_bold),
        Paragraph("Coordinator, TB3, UR5, Lock Server", td_style),
        Paragraph("<font color='#22543D'><b>100% Complete</b></font>", td_center),
        Paragraph("Full async Python implementation in <code>ros2_ws/src/multi_robot_coordination/</code>.", td_style)
    ]
    stat_r5 = [
        Paragraph("<b>Action & Service IDL Compilation</b>", td_bold),
        Paragraph("ROS 2 Jazzy Interface Build", td_style),
        Paragraph("<font color='#744210'><b>Action Needed</b></font>", td_center),
        Paragraph("Needs CMake interface package setup to enable live <code>ros2 launch</code> execution.", td_style)
    ]

    status_table = Table([status_headers, stat_r1, stat_r2, stat_r3, stat_r4, stat_r5], colWidths=[120, 110, 85, 207])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('BACKGROUND', (0, 2), (-1, 2), c_row_alt),
        ('BACKGROUND', (0, 3), (-1, 3), colors.white),
        ('BACKGROUND', (0, 4), (-1, 4), c_row_alt),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor("#FEFCBF")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(status_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Successfully generated at: {output_path}")

if __name__ == '__main__':
    out_file = sys.argv[1] if len(sys.argv) > 1 else "/home/sailakshmi/Desktop/RDC_project/project/Multi_Robot_Coordination_Component_Analysis_Chart.pdf"
    build_analysis_pdf(out_file)
